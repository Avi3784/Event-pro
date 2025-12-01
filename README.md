
# Event-pro Web Application

Event-pro is a comprehensive Django-based web application designed to streamline the entire lifecycle of event planning. This application provides a centralized interface for organizing events, managing sponsors, tracking volunteers, handling ticket bookings, and automating email communications.

## Features

- **User Authentication**: Secure registration, login, and logout functionality for all users.
- **Dynamic Dashboard**: Real-time analytics displaying total events, active sponsors, **funds raised**, and total ticket sales.
- **Event Management**: Admins can add, view, edit, and manage events with detailed attributes including:
    - Event Name & Organizer
    - Date & Time
    - **Venue & Location**
    - **Event Theme/Category**
- **Automated Email System**: Sends automated **email confirmations** to users upon successful ticket booking or registration.
- **Ticket Booking System**: Users can browse and book tickets with logic supporting both **Paid** and **Free** event types.
- **Sponsor Management**: Dedicated module to track sponsors, including their contact details, purpose, and **financial contribution tracking**.
- **Volunteer Management**: Admins can recruit, view, and manage volunteers interested in contributing to specific events.
- **CSV Export**: One-click functionality to export participant and event data to a CSV file for offline record-keeping and analysis.

## Installation

1. **Clone the repository:**

    ```bash
    git clone [https://github.com/Avi3784/Event-pro.git](https://github.com/Avi3784/Event-pro.git)
    cd event-pro
    ```

2. **Create and activate a virtual environment (Recommended):**

    ```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # Mac/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Set up environment variables:**

    Create a `.env` file in the root directory (same level as `manage.py`) to configure your Django secret key and Email settings:
    
    ```env
    SECRET_KEY=your_django_secret_key
    DEBUG=True
    
    # Email Configuration
    EMAIL_HOST_USER=your_email@gmail.com
    EMAIL_HOST_PASSWORD=your_app_password
    ```

5. **Run migrations:**

    ```bash
    python manage.py makemigrations 
    python manage.py migrate 
    ```

6. **Run the development server:**

    ```bash
    python manage.py runserver
    ```


## Usage

- **Dashboard:** Log in to view insights into funds raised, sponsor stats, and event counts.
- **Events:** Create new events specifying the Theme, Venue, and Date.
- **Booking:** Users can select between Paid or Free events and book their spot.
- **Email:** Upon booking, check your registered email inbox for the automated confirmation.
- **Sponsors:** Add sponsors and log their financial contribution to the event.
- **Volunteers:** Manage the list of volunteers signed up for upcoming events.
- **Export:** Download the participant list as a CSV file.

## Contributing

Contributions are welcome! Please follow the steps below:
1. Fork the repository.
2. Create a new branch (`git checkout -b feature/YourFeature`).
3. Commit your changes (`git commit -m 'Add some feature'`).
4. Push to the branch (`git push origin feature/YourFeature`).
5. Open a Pull Request.

## License

This project is licensed under the MIT License.
