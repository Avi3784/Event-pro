# Event Management System (EVM) Web Application

The Event Management System (EVM) is a Django-based web application designed to streamline the entire lifecycle of event planning. This application provides a centralized interface for organizing events, managing sponsors, tracking volunteers, and handling ticket bookings efficiently.

## Features

- **User Authentication**: Secure registration, login, and logout functionality for all users.
- **Dashboard**: Real-time analytics displaying total events, active sponsors, funds raised, and ticket sales.
- **Event Management**: Admins can add, view, edit, and manage events with details such as name, organizer, date, time, venue, and theme.
- **Sponsor Management**: Tools to track sponsors associated with events, including their purpose, contact information, and contribution costs.
- **Ticket Booking**: Users can register and book tickets for various events directly through the platform.
- **Volunteer Management**: Admins can add, view, and manage volunteers interested in contributing to events.
- **CSV Export**: One-click functionality to export participant details to a CSV file for record-keeping and analysis.

## Installation

1. **Clone the repository:**

    ```bash
    git clone [https://github.com/Avi3784/event-pro.git](https://github.com/Avi3784/event-pro.git)
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

    Create a `.env` file in the root directory (or check `settings.py`) to configure your standard Django keys:
    
    ```env
    SECRET_KEY=your_django_secret_key
    DEBUG=True
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

7. **Access the application at `http://localhost:8000/`.**

## Usage

- Register as a user or login if already registered.
- Explore the dashboard for insights into events, sponsors, and funds raised.
- Add, view, edit, and manage events through the admin interface.
- Browse available events and book tickets.
- Manage volunteers and sponsors associated with events.
- Export participant details to a CSV file for analysis.

## Contributing

Contributions are welcome! Please follow the steps below:
1. Fork the repository.
2. Create a new branch (`git checkout -b feature/YourFeature`).
3. Commit your changes (`git commit -m 'Add some feature'`).
4. Push to the branch (`git push origin feature/YourFeature`).
5. Open a Pull Request.

## License

This project is licensed under the MIT License.
