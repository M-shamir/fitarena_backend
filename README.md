# 🏋️‍♂ FitArena Backend API

FitArena is a backend system built using Django REST Framework for managing stadium bookings and trainer course bookings.

##  Features

- Stadium booking management
- Trainer course approval and booking
- User roles: Admin, Stadium Owner, Trainer, Customer
- JWT-based authentication
- API for managing slots, approvals, and bookings

##  Tech Stack

- Python 3
- Django
- Django REST Framework
- PostgreSQL
- JWT Authentication

##  Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/fitarena-backend.git
   cd fitarena-backend

    python -m venv env
    source env/bin/activate  # On Windows: env\Scripts\activate  
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py runserver
