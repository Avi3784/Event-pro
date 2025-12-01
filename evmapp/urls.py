from django.urls import path
from evmapp import views
from django.contrib import admin

urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    # Core
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Events
    path('addevent', views.add_event, name='addevent'),
    path('viewevent', views.view_event, name='viewevent'),
    path('edit_event/<int:event_id>/', views.edit_event, name='edit_event'),
    path('download-participants-csv/<int:event_id>/', views.download_participants_csv, name='download_event_csv'),
    path('update_event_status', views.update_event_status, name='update_event_status'),
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
    
    
    # Booking & Payment
    path('booktickets', views.ticketbooking, name='bookticket'),
    
    # --- THIS IS THE MISSING LINE FIXING YOUR ERROR ---
    path('my-bookings/', views.my_bookings, name='my_bookings'), 
    # --------------------------------------------------
    path('booking/success/<int:booking_id>/', views.booking_success, name='booking_success'),

    path('payment/qr/<int:booking_id>/', views.qr_payment_view, name='qr_payment'),
    path('payments/confirm/', views.payment_confirm, name='payment_confirm'),
    path('payments/admin/', views.payments_admin, name='payments_admin'),

    # Volunteers & Sponsors
    path('sponsor/', views.sponsor, name='sponsor'),
    path('add_volunteer/', views.add_volunteer, name='add_volunteer'),
    path('view_volunteers/', views.view_volunteers, name='view_volunteers'),
    path('update_volunteer_status/', views.update_volunteer_status, name='update_volunteer_status'),

    # CSV & Admin Tools
    path('download-participants-csv/', views.download_participants_csv, name='download_participants_csv'),
    path("admin-tools/view-db/", views.view_db, name="view_db"),
    path("admin-tools/download-db/", views.download_db, name="download_db"),
]