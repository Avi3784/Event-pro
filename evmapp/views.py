import csv, string, secrets, json, uuid, os, sqlite3
from django.views.decorators.csrf import csrf_exempt

# Imports for payment and images
import razorpay
import qrcode
from io import BytesIO
from urllib.parse import quote_plus

# Django core imports
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.mail import EmailMessage, send_mail
from django.shortcuts import render, redirect, get_object_or_404
from decimal import Decimal, InvalidOperation
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from .models import Booking, Event, Sponsor, Volunteer, Payment
from django.contrib import messages
from django.template.loader import render_to_string
from datetime import datetime, timedelta
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.http import HttpResponse, JsonResponse, FileResponse, Http404
from django.db.models import Sum, F, Min, Count, Q
from django.db import transaction
from twilio.rest import Client
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm

# -------------------------
# Auth / Registration Views
# -------------------------

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'evmapp/register.html', {'form': form})


def login_view(request):
    error_message = ''
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            error_message = "Invalid Credentials, Please try again"
    return render(request, 'evmapp/login.html', {'error_message': error_message})


@login_required
def logout_view(request):
    logout(request)
    return redirect('home')


# -------------------------
# Dashboard & Logic
# -------------------------

@login_required(login_url='/login/')
def dashboard(request):
    events = Event.objects.all()
    total_events = events.count()
    volunteers = Volunteer.objects.count()
    total_sponsors = Sponsor.objects.count()

    # Count ALL Paid bookings (Verified + Pending)
    paid_bookings = Booking.objects.filter(is_paid=True)

    # Calculate Revenue
    revenue_data_agg = paid_bookings.aggregate(total=Sum('total_cost'))
    total_funds = revenue_data_agg['total'] or 0
    
    # Calculate Tickets
    ticket_data_agg = paid_bookings.aggregate(total=Sum('number_of_tickets'))
    total_tickets_sold = ticket_data_agg['total'] or 0
    
    # Calculate Net Profit
    sponsor_funds = Sponsor.objects.aggregate(total=Sum('cost'))['total'] or 0
    net_revenue = total_funds - sponsor_funds

    # Chart Data
    events_with_stats = Event.objects.annotate(
        tickets_sold=Sum('booking__number_of_tickets'),
        revenue=Sum('booking__total_cost'),
        tickets_remaining=F('total_tickets') - Sum('booking__number_of_tickets'),
        booking_count=Count('booking')
    ).order_by('-date')

    event_labels = [e.event_name for e in events_with_stats]
    revenue_data = [float(e.revenue or 0) for e in events_with_stats]

    # Recent Bookings
    recent_bookings = Booking.objects.select_related('event').order_by('-booking_date')[:5]

    context = {
        'total_events': total_events,
        'total_sponsors': total_sponsors,
        'total_funds': total_funds,
        'sponsor_funds': sponsor_funds,
        'net_revenue': net_revenue,
        'volunteers': volunteers,
        'events': events_with_stats,
        'recent_bookings': recent_bookings,
        'event_labels': event_labels,
        'revenue_data': revenue_data,
        'total_tickets_sold': total_tickets_sold,
    }
    return render(request, 'evmapp/dashboard.html', context)


def select_venue(request):
    if request.method == 'POST':
        venue = request.POST.get('venue')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        if venue and latitude and longitude:
            return JsonResponse({'venue': venue, 'latitude': latitude, 'longitude': longitude})
    return render(request, 'evmapp/venue_map.html')


@login_required(login_url='/login/')
def add_event(request):
    if request.method == 'POST':
        event_name = request.POST.get('event_name')
        category = request.POST.get('category') # <--- CAPTURED CATEGORY
        organiser_name = request.POST.get('organiser_name')
        time = request.POST.get('time')
        date = request.POST.get('date')
        venue = request.POST.get('venue')
        theme = request.POST.get('theme') or 'General'
        total_tickets_raw = request.POST.get('total_tickets')
        price_per_ticket_raw = request.POST.get('price_per_ticket')
        description = request.POST.get('description')
        free_ticket = request.POST.get('free_ticket') == 'on'

        try:
            total_tickets = int(total_tickets_raw) if total_tickets_raw and str(total_tickets_raw).strip() else 0
        except (ValueError, TypeError):
            total_tickets = 0

        if free_ticket:
            price_per_ticket = Decimal('0')
        else:
            try:
                price_per_ticket = Decimal(str(price_per_ticket_raw).strip()) if price_per_ticket_raw and str(price_per_ticket_raw).strip() else Decimal('0')
            except (InvalidOperation, TypeError):
                price_per_ticket = Decimal('0')

        event = Event.objects.create(
            event_name=event_name,
            category=category, # <--- SAVED CATEGORY
            organiser=organiser_name,
            time=time,
            date=date,
            venue=venue,
            theme=theme,
            total_tickets=total_tickets,
            price_per_ticket=price_per_ticket,
            description=description,
            free_ticket=free_ticket,
        )

        sponsor_names = request.POST.getlist('sponsor_name[]')
        purposes = request.POST.getlist('purpose[]')
        contacts = request.POST.getlist('contact[]')
        costs = request.POST.getlist('cost[]')

        for i in range(len(sponsor_names)):
            sponsor_name = sponsor_names[i].strip() if sponsor_names[i] else ''
            purpose = purposes[i].strip() if i < len(purposes) and purposes[i] else ''
            contact = contacts[i].strip() if i < len(contacts) and contacts[i] else ''
            cost_raw = costs[i] if i < len(costs) and costs[i] else ''
            try:
                cost_val = Decimal(str(cost_raw).strip()) if cost_raw and str(cost_raw).strip() else Decimal('0')
            except (InvalidOperation, TypeError):
                cost_val = Decimal('0')
            if sponsor_name:
                sponsor = Sponsor.objects.create(
                    name=sponsor_name,
                    purpose=purpose,
                    contact=contact,
                    cost=cost_val
                )
                event.sponsors.add(sponsor)

        messages.success(request, 'Event added successfully.')
        return redirect('dashboard')

    return render(request, 'evmapp/add_event.html')


@login_required(login_url='/login/')
def view_event(request):
    events = Event.objects.all()
    total_tickets_sold = Booking.objects.aggregate(total_tickets_sold=Sum('number_of_tickets'))['total_tickets_sold'] or 0
    return render(request, 'evmapp/view_events.html', {'events': events, 'total_tickets_sold': total_tickets_sold})


@login_required(login_url='/login/')
def edit_event(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if request.method == 'POST':
        try:
            event.event_name = request.POST.get('event_name')
            event.category = request.POST.get('category') # <--- UPDATE CATEGORY
            event.organiser = request.POST.get('organiser_name')
            event.venue = request.POST.get('venue')
            event.theme = request.POST.get('theme')
            event.description = request.POST.get('description')
            
            # Update numerical fields if provided
            total_tickets = request.POST.get('total_tickets')
            if total_tickets:
                event.total_tickets = int(total_tickets)
            
            price = request.POST.get('price_per_ticket')
            if price:
                event.price_per_ticket = Decimal(price)

            time = request.POST.get('time')
            if time and time.strip():
                event.time = time
            date = request.POST.get('date')
            if date and date.strip():
                event.date = date
            
            event.save()
            messages.success(request, 'Event details edited successfully')
            return redirect('viewevent')
        except Exception as e:
            messages.error(request, 'Error updating event: Please ensure all required fields are filled correctly')
            return render(request, 'evmapp/edit_event.html', {'event': event, 'error': str(e)})
    return render(request, 'evmapp/edit_event.html', {'event': event})


def update_event_status(request):
    event_id = request.POST.get('event_id')
    status = request.POST.get('status')
    try:
        event = Event.objects.get(pk=event_id)
        event.status = (status == 'active')
        event.save()
        messages.success(request, 'Event status changed successfully')
    except Event.DoesNotExist:
        messages.error(request, 'Event not found')
    return redirect('viewevent')


@login_required
def event_detail(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    total_tickets_sold = Booking.objects.filter(event=event).aggregate(total_tickets_sold=Sum('number_of_tickets'))['total_tickets_sold'] or 0
    event_cost = event.sponsors.aggregate(total_cost=Sum('cost'))['total_cost'] or 0
    money_collected = total_tickets_sold * event.price_per_ticket
    percentage_collected = round((money_collected / event_cost) * 100, 2) if event_cost else 0
    bookings = Booking.objects.filter(event=event)
    
    # Filters
    name_filter = request.GET.get('name')
    contact_number_filter = request.GET.get('contact_number')
    if name_filter:
        bookings = bookings.filter(name__icontains=name_filter)
    if contact_number_filter:
        bookings = bookings.filter(contact_number__icontains=contact_number_filter)
        
    return render(request, "evmapp/event_detail.html", {
        'event': event, 
        'total_tickets_sold': total_tickets_sold, 
        'event_cost': event_cost, 
        'percentage_collected': percentage_collected, 
        'bookings': bookings
    })


def home(request):
    # 1. Fetch Events
    events = Event.objects.filter(status=True).order_by('date') 

    # 2. Calculate Stats
    total_events = events.count()
    ticket_data = Booking.objects.filter(is_verified=True).aggregate(total=Sum('number_of_tickets'))
    total_tickets_sold = ticket_data['total'] if ticket_data['total'] else 0
    total_volunteers = Volunteer.objects.count()

    context = {
        'events': events,
        'total_events': total_events,
        'total_tickets_sold': total_tickets_sold,
        'total_volunteers': total_volunteers,
    }
    return render(request, "evmapp/home.html", context)


# -------------------------
# Messaging / Emails / SMS
# -------------------------

def send_confirmation_sms(contact_number, message):
    try:
        if settings.TWILIO_ACCOUNT_SID:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(body=message, from_=settings.TWILIO_PHONE_NUMBER, to=contact_number)
    except Exception as e:
        print(f"Failed to send SMS: {str(e)}")


def send_booking_confirmation_email(booking):
    event = booking.event
    subject = f'🎫 Ticket Confirmed: {event.event_name} | Ticket ID: {booking.ticket_id}'
    context = {
        'booking': booking,
        'event': event,
        'payment_info': {'amount': booking.total_cost, 'currency': 'INR', 'is_free': booking.total_cost == 0},
    }
    
    # UPI QR generation (Legacy support if UPI_VPA is in settings)
    upi_uri = None
    try:
        if getattr(settings, 'UPI_VPA', None) and booking.total_cost and float(booking.total_cost) > 0:
            note = getattr(settings, 'UPI_NOTE', '') or event.event_name
            upi_uri = f"upi://pay?pa={settings.UPI_VPA}&pn={quote_plus(getattr(settings, 'UPI_NAME', ''))}&am={booking.total_cost}&cu=INR&tn={quote_plus(note)}"
            context['upi_uri'] = upi_uri
    except Exception as e:
        print(f"Error generating UPI URI: {str(e)}")

    try:
        message = render_to_string('evmapp/email/booking_confirmation.html', context)
    except Exception as template_error:
        message = f"Your ticket for {event.event_name} is confirmed. Ticket ID: {booking.ticket_id}"
        
    try:
        email = EmailMessage(subject, message, from_email=settings.DEFAULT_FROM_EMAIL, to=[booking.email], reply_to=[settings.DEFAULT_FROM_EMAIL])
        email.content_subtype = "html"
        
        if upi_uri:
            try:
                qr_img = qrcode.make(upi_uri)
                buf = BytesIO()
                qr_img.save(buf, format='PNG')
                buf.seek(0)
                email.attach(f'upi_{booking.id}.png', buf.read(), 'image/png')
            except Exception:
                pass
                
        email.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"Failed to send booking confirmation email to {booking.email}: {str(e)}")
        return False


def send_event_reminder_email(booking, hours_remaining=24):
    event = booking.event
    if hours_remaining == 24:
        subject = f'⏰ 24 Hours to Go: {event.event_name} Tomorrow!'
    elif hours_remaining == 2:
        subject = f'🔔 Starting Soon: {event.event_name} in 2 Hours!'
    else:
        subject = f'Reminder: {event.event_name} is Coming Up!'
    context = {'booking': booking, 'event': event, 'hours_remaining': hours_remaining, 'important_items': ['Your Ticket ID', 'Valid ID proof', 'Comfortable attire']}
    message = render_to_string('evmapp/email/event_reminder.html', context)
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [booking.email], html_message=message, fail_silently=False)
    except Exception as e:
        print(f"Failed to send reminder to {booking.email}: {str(e)}")


def check_and_send_reminders():
    now = timezone.now()
    tomorrow = now + timedelta(days=1)
    day_before_bookings = Booking.objects.filter(event__date=tomorrow.date(), reminder_24h_sent=False)
    for booking in day_before_bookings:
        send_event_reminder_email(booking, hours_remaining=24)
        booking.reminder_24h_sent = True
        booking.save()
    
    two_hours_from_now = now + timedelta(hours=2)
    upcoming_bookings = Booking.objects.filter(event__date=now.date(), event__time__hour=two_hours_from_now.hour, event__time__minute=two_hours_from_now.minute, reminder_2h_sent=False)
    for booking in upcoming_bookings:
        send_event_reminder_email(booking, hours_remaining=2)
        booking.reminder_2h_sent = True
        booking.save()


def generate_ticket_id(length=5):
    characters = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))


# -------------------------
# NEW BOOKING & QR PAYMENT LOGIC
# -------------------------

def send_payment_received_email(booking):
    """Sends email to user confirming we got their payment details"""
    try:
        subject = f'Payment Reference Received - {booking.event.event_name}'
        try:
            context = {'booking': booking}
            message = render_to_string('evmapp/email/payment_received.html', context)
        except:
            message = f"Hi {booking.name}, we have received your transaction ID: {booking.payment_ref}. Please wait for admin verification."

        email = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [booking.email])
        email.content_subtype = "html"
        email.send(fail_silently=True)
    except Exception as e:
        print("Failed to send payment received email to user:", e)


def ticketbooking(request):
    events = Event.objects.filter(status=True)
    if not events.exists():
        messages.warning(request, 'No events are currently available for booking.')
        return render(request, 'evmapp/ticketbooking.html', {'events': []})

    if request.method == 'POST':
        try:
            event_id = request.POST.get('event')
            if not event_id:
                messages.error(request, 'Please select an event')
                return render(request, 'evmapp/ticketbooking.html', {'events': events})

            event = Event.objects.filter(pk=event_id, status=True).first()
            if not event:
                messages.error(request, 'Selected event is not available')
                return render(request, 'evmapp/ticketbooking.html', {'events': events})

            try:
                number_of_tickets = int(request.POST.get('number_of_tickets', 0))
                if number_of_tickets <= 0: raise ValueError
            except ValueError:
                messages.error(request, 'Please enter a valid number of tickets')
                return render(request, 'evmapp/ticketbooking.html', {'events': events})

            name = request.POST.get('name')
            contact_number = request.POST.get('contact_number')
            email = request.POST.get('email')

            if not all([name, contact_number, email]):
                messages.error(request, 'Please fill in all required fields')
                return render(request, 'evmapp/ticketbooking.html', {'events': events})

            if not contact_number.startswith('+'):
                contact_number = f'+91{contact_number}'

            total_cost = float(event.price_per_ticket * number_of_tickets)
            ticket_id = generate_ticket_id()

            booking = Booking.objects.create(
                event=event,
                number_of_tickets=number_of_tickets,
                name=name,
                contact_number=contact_number,
                email=email,
                total_cost=total_cost,
                ticket_id=ticket_id,
                is_paid=False,
                is_verified=False,
                paid=False
            )

            if total_cost > 0:
                return redirect('qr_payment', booking_id=booking.id)
            else:
                booking.is_verified = True
                booking.save()
                send_booking_confirmation_email(booking)
                return redirect('booking_success', booking_id=booking.id)

        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return render(request, 'evmapp/ticketbooking.html', {'events': events})

    return render(request, 'evmapp/ticketbooking.html', {'events': events})


@require_http_methods(["GET", "POST"])
def qr_payment_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == "POST":
        payment_ref = request.POST.get("payment_ref", "").strip()
        screenshot = request.FILES.get("payment_screenshot")

        if not payment_ref:
            messages.error(request, "Please enter the Transaction ID / Reference Number.")
            return render(request, "evmapp/qr_payment.html", {"booking": booking})

        booking.payment_ref = payment_ref
        if screenshot:
            booking.payment_screenshot = screenshot
        
        # Force Pending Status
        booking.is_paid = True
        booking.is_verified = False
        booking.save()

        send_payment_received_email(booking)
        return redirect('booking_success', booking_id=booking.id)

    return render(request, "evmapp/qr_payment.html", {"booking": booking})


def booking_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, 'evmapp/booking_success.html', {'booking': booking})


def my_bookings(request):
    bookings = None
    search_email = None

    if request.user.is_authenticated:
        search_email = request.user.email
        bookings = Booking.objects.filter(email=search_email).order_by('-booking_date')
    
    elif request.method == 'POST':
        search_email = request.POST.get('email')
        if search_email:
            bookings = Booking.objects.filter(email=search_email).order_by('-booking_date')
            if not bookings.exists():
                messages.error(request, "No tickets found for this email.")

    return render(request, 'evmapp/my_bookings.html', {
        'bookings': bookings, 
        'search_email': search_email
    })


# -------------------------
# Razorpay / Legacy Payments
# -------------------------

@csrf_exempt
def payment_confirm(request):
    return JsonResponse({'status': 'ok'})

@csrf_exempt
def razorpay_webhook(request):
    return HttpResponse(status=200)


@login_required(login_url='/login/')
def payments_admin(request):
    if not request.user.is_staff:
        messages.error(request, 'Permission denied')
        return redirect('home')
    payments = Payment.objects.select_related('booking__event').order_by('-created_at')[:200]
    return render(request, 'evmapp/payments_list.html', {'payments': payments})


# -------------------------
# Volunteers & Misc
# -------------------------

@login_required(login_url='/login/')
def sponsor(request):
    sponsors = Sponsor.objects.all()
    return render(request, 'evmapp/sponsor.html', {'sponsors': sponsors})


def download_participants_csv(request, event_id=None):
    response = HttpResponse(content_type='text/csv')
    
    if event_id:
        filename = f"participants_event_{event_id}.csv"
        bookings = Booking.objects.filter(event_id=event_id)
    else:
        filename = "all_participants.csv"
        bookings = Booking.objects.all()
        
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow(['Name', 'Contact Number', 'Tickets', 'Total Cost', 'Ticket ID', 'Payment Ref', 'Verified'])
    
    for booking in bookings:
        writer.writerow([
            booking.name, 
            booking.contact_number, 
            booking.number_of_tickets, 
            booking.total_cost, 
            booking.ticket_id,
            booking.payment_ref,
            "Yes" if booking.is_verified else "No"
        ])
    return response


def add_volunteer(request):
    if request.method == 'POST':
        try:
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            address = request.POST.get('address')
            city = request.POST.get('city')
            state = request.POST.get('state')
            volunteer_role = request.POST.get('volunteer_role')
            skills = request.POST.get('skills')
            availability = request.POST.getlist('availability[]')

            if not all([first_name, last_name, email, phone, address, city, state, volunteer_role]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('add_volunteer')

            phone = phone.replace('-', '').strip()
            if not phone.startswith('+91'):
                phone = f'+91{phone}'

            new_volunteer = Volunteer.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                address=address,
                city=city,
                state=state,
                volunteer_role=volunteer_role,
                skills=skills,
                availability=availability,
                status='Pending'
            )

            try:
                subject = 'Volunteer Application Received'
                context = {'volunteer': new_volunteer}
                try:
                    message = render_to_string('evmapp/email/volunteer_confirmation.html', context)
                except:
                    message = f"Hello {first_name}, thanks for volunteering!"
                
                email_message = EmailMessage(subject=subject, body=message, from_email=settings.DEFAULT_FROM_EMAIL, to=[email])
                email_message.content_subtype = "html"
                email_message.send(fail_silently=False)
            except Exception as email_error:
                print(f"Failed to send email: {str(email_error)}")
                messages.warning(request, 'Application received, but confirmation email failed.')

            messages.success(request, 'Thank you for your interest in volunteering! We will contact you soon.')
            return redirect('home')
        except Exception as e:
            messages.error(request, f'An error occurred. Please try again.')
            print(f"Volunteer application error: {str(e)}")
            return redirect('add_volunteer')
    return render(request, 'evmapp/volunteers/add.html')

@login_required(login_url='/login/')
def view_volunteers(request):
    volunteers = Volunteer.objects.all()
    return render(request, 'evmapp/view_volunteers.html', {'volunteers': volunteers})

@require_POST
@login_required(login_url='/login/')
def update_volunteer_status(request):
    volunteer_id = request.POST.get('volunteer_id')
    new_status = request.POST.get('status')
    
    volunteer = get_object_or_404(Volunteer, id=volunteer_id)
    volunteer.status = new_status
    volunteer.save()
    
    messages.success(request, f"Updated status for {volunteer.first_name} to {new_status}")
    return redirect('view_volunteers')


# -------------------------
# Admin Tools
# -------------------------

def _is_superuser(user):
    return user.is_active and user.is_superuser

@user_passes_test(_is_superuser)
@require_GET
def download_db(request):
    db_settings = settings.DATABASES.get("default", {})
    engine = db_settings.get("ENGINE", "")
    db_name = db_settings.get("NAME", "")
    if "sqlite3" not in engine.lower():
        raise Http404("Database download only supported for SQLite databases.")
    if not db_name or not os.path.exists(db_name):
        raise Http404("Database file not found.")
    return FileResponse(open(db_name, "rb"), as_attachment=True, filename=os.path.basename(db_name))


@user_passes_test(_is_superuser)
@require_GET
def view_db(request):
    db_settings = settings.DATABASES.get("default", {})
    engine = db_settings.get("ENGINE", "")
    db_name = db_settings.get("NAME", "")
    if "sqlite3" not in engine.lower():
        return HttpResponse("Viewing DB schema is only supported for SQLite databases.", status=400)
    if not db_name or not os.path.exists(db_name):
        return HttpResponse("Database file not found.", status=404)
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
        tables = [r[0] for r in cursor.fetchall()]
        db_info = []
        SAMPLE_ROWS = 10
        for table in tables:
            cursor.execute(f"PRAGMA table_info('{table}')")
            cols_info = cursor.fetchall()
            columns = [col[1] for col in cols_info]
            cursor.execute(f"SELECT * FROM '{table}' LIMIT {SAMPLE_ROWS}")
            rows = cursor.fetchall()
            db_info.append({"table": table, "columns": columns, "rows": rows})
    except Exception as e:
        return HttpResponse("Error reading database: " + str(e), status=500)
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass
    return render(request, "admin_tools/db_view.html", {"db_info": db_info})