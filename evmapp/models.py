from django.db import models
import uuid

class Sponsor(models.Model):
    name = models.CharField(max_length=100)
    purpose = models.CharField(max_length=200)
    contact = models.CharField(max_length=100)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Event(models.Model):
    CONFERENCE = 'CONFERENCE'
    WORKSHOP = 'WORKSHOP'
    SEMINAR = 'SEMINAR'
    CULTURAL = 'CULTURAL'
    SPORTS = 'SPORTS'
    CONCERT = 'CONCERT'
    EXHIBITION = 'EXHIBITION'
    NETWORKING = 'NETWORKING'
    OTHER = 'OTHER'

    EVENT_CATEGORIES = [
        (CONFERENCE, 'Conference'),
        (WORKSHOP, 'Workshop'),
        (SEMINAR, 'Seminar'),
        (CULTURAL, 'Cultural Event'),
        (SPORTS, 'Sports Event'),
        (CONCERT, 'Concert'),
        (EXHIBITION, 'Exhibition'),
        (NETWORKING, 'Networking Event'),
        (OTHER, 'Other')
    ]

    event_name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=EVENT_CATEGORIES, default='OTHER')
    organiser = models.CharField(max_length=100)
    time = models.TimeField()
    date = models.DateField()
    venue = models.CharField(max_length=200)
    venue_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    venue_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    theme = models.CharField(max_length=200)
    total_tickets = models.IntegerField()
    price_per_ticket = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sponsors = models.ManyToManyField(Sponsor)
    status = models.BooleanField(default=True)
    description = models.CharField(max_length=250, default="Fun Activities Followed by Dinner, Bring Your Friends and Family along!", null=True)
    free_ticket = models.BooleanField(default=False, null=True)
    group_discount = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Discount percentage for group bookings")
    
    # --- ADDED FIELD ---
    payment_qr = models.ImageField(upload_to='event_qrs/', blank=True, null=True, help_text="Upload QR Code for payment here")

    def __str__(self):
        return self.event_name


def generate_ticket_id(length=5):
    return uuid.uuid4().hex[:length].upper()


class Booking(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    number_of_tickets = models.IntegerField()
    name = models.CharField(max_length=200)
    contact_number = models.CharField(max_length=15)
    email = models.EmailField(max_length=254, null=True, default='')
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    
    paid = models.BooleanField(default=False)
    payment_id = models.CharField(max_length=100, default='000', blank=True)
    ticket_id = models.CharField(max_length=10, unique=True, default=generate_ticket_id)
    booking_date = models.DateTimeField(auto_now_add=True, null=True)

    # Email reminder tracking
    reminder_24h_sent = models.BooleanField(default=False)
    reminder_2h_sent = models.BooleanField(default=False)
    last_reminder_sent = models.DateTimeField(null=True, blank=True)

    # Verification Fields
    is_paid = models.BooleanField(default=False, help_text="User marked as paid.")
    is_verified = models.BooleanField(default=False, help_text="Admin verified payment.")
    payment_ref = models.CharField(max_length=255, blank=True, null=True, help_text="Transaction ID entered by user.")
    payment_screenshot = models.ImageField(upload_to='payment_screenshots/', blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.event.event_name}"


class UserProfile(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)


class Volunteer(models.Model):
    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Pending', 'Pending'),
        ('Inactive', 'Inactive'),
    )

    ROLE_CHOICES = (
        ('Event Coordinator', 'Event Coordinator'),
        ('Registration Desk', 'Registration Desk'),
        ('Technical Support', 'Technical Support'),
        ('Guest Relations', 'Guest Relations'),
        ('Marketing', 'Marketing & Promotion'),
        ('Logistics', 'Logistics & Setup'),
        ('Security', 'Security'),
        ('First Aid', 'First Aid & Safety'),
        ('Photography', 'Photography & Documentation'),
        ('General', 'General Volunteer'),
    )

    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)

    volunteer_role = models.CharField(max_length=100, choices=ROLE_CHOICES, default='General')
    skills = models.TextField(blank=True, null=True)
    availability = models.JSONField(default=list) 
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name} - {self.volunteer_role}"
        return f"Volunteer - {self.volunteer_role}"

    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return "No name provided"


class Payment(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    razorpay_order_id = models.CharField(max_length=128, db_index=True, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=128, null=True, blank=True, unique=True)
    status = models.CharField(max_length=32, default='created')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=8, default='INR')
    method = models.CharField(max_length=32, null=True, blank=True)
    raw_response = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.razorpay_order_id or self.razorpay_payment_id} - {self.status}"