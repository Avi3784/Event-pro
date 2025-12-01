from django.contrib import admin
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.template.loader import render_to_string
from .models import Sponsor, Event, Booking, UserProfile, Volunteer, Payment

# Set the header for the dashboard
admin.site.site_header = 'Event Management Admin'

# --- 1. Custom Action for One-Click Verification ---
@admin.action(description='Verify Payment & Send Confirmation Email')
def verify_payment_and_notify(modeladmin, request, queryset):
    success_count = 0
    email_fail_count = 0
    already_verified_count = 0

    for booking in queryset:
        if not booking.is_verified:
            # 1. Update status flags (Verify FIRST, so DB is updated even if email fails)
            booking.is_verified = True
            booking.is_paid = True
            booking.paid = True
            booking.save()

            # 2. Prepare the Email
            subject = f" Payment Verified: {booking.event.event_name}"
            
            # Load the HTML file
            context = {'booking': booking}
            html_message = render_to_string('evmapp/email/payment_verified.html', context)
            
            # Plain text fallback
            plain_message = f"Your booking for {booking.event.event_name} is confirmed. Ticket ID: {booking.ticket_id}"

            # 3. Send the Email
            try:
                send_mail(
                    subject,
                    plain_message, 
                    settings.EMAIL_HOST_USER,
                    [booking.email],
                    fail_silently=False,
                    html_message=html_message
                )
                success_count += 1
            except Exception as e:
                # If email fails (Network/Auth error), just count it. Don't crash.
                email_fail_count += 1
                print(f"EMAIL FAILED for {booking.email}: {e}")
        else:
            already_verified_count += 1

    # 4. Feedback messages to Admin
    if success_count > 0:
        modeladmin.message_user(request, f"Successfully verified and emailed {success_count} users.", level=messages.SUCCESS)
    
    if email_fail_count > 0:
        # This warns you that the DB is updated, but emails didn't go out
        modeladmin.message_user(request, f" Verified {email_fail_count} users, but emails failed to send (Check Network/Settings).", level=messages.WARNING)
        
    if already_verified_count > 0:
        modeladmin.message_user(request, f"{already_verified_count} users were already verified.", level=messages.INFO)


# --- 2. Admin Model Configurations ---

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "event", "total_cost", "payment_ref", "is_verified", "ticket_id", "booking_date")
    list_filter = ("is_verified", "is_paid", "event")
    search_fields = ("name", "email", "ticket_id", "payment_ref")
    readonly_fields = ("booking_date", "ticket_id")
    actions = [verify_payment_and_notify]

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    # Explicitly list fields to ensure payment_qr appears
    fields = ('event_name', 'category', 'payment_qr', 'price_per_ticket', 'total_tickets', 'organiser', 'date', 'time', 'venue', 'venue_latitude', 'venue_longitude', 'theme', 'description', 'free_ticket', 'group_discount', 'sponsors', 'status')
    
    list_display = ('event_name', 'date', 'price_per_ticket', 'has_qr_code')
    list_filter = ('category', 'date')
    search_fields = ('event_name',)

    def has_qr_code(self, obj):
        return bool(obj.payment_qr)
    has_qr_code.boolean = True
    has_qr_code.short_description = "QR Code Uploaded?"

@admin.register(Volunteer)
class VolunteerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'volunteer_role', 'status')
    list_filter = ('status', 'volunteer_role')
    search_fields = ('first_name', 'email')

# --- 3. Register Remaining Models ---
admin.site.register(Sponsor)
admin.site.register(UserProfile)
admin.site.register(Payment)