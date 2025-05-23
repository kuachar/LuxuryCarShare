# Luxury CarShare Hub

A premium luxury car-sharing platform built with Flask and SQLAlchemy, designed for high-end vehicle rentals.

## Project Overview

Luxury CarShare Hub is an exclusive platform connecting luxury car owners with discerning renters. The application provides a seamless experience for browsing, booking, and managing high-end vehicles with a modern, glass-morphism UI design that emphasizes luxury and sophistication.

### The Problem We Solve

The luxury car rental market faces unique challenges that traditional rental platforms don't address:

1. **Trust and Verification**: Owners of high-value vehicles need assurance about who is renting their prized possessions
2. **Specialized Experience**: Luxury car enthusiasts seek a premium booking experience that matches the caliber of vehicles
3. **Direct Communication**: Both parties benefit from direct communication rather than dealing with corporate intermediaries
4. **Underutilized Assets**: Many luxury vehicles sit idle in garages, representing significant untapped value
5. **Limited Accessibility**: Experiencing luxury vehicles is typically restricted to those who can afford to purchase them

Luxury CarShare Hub bridges these gaps by creating a peer-to-peer marketplace specifically designed for high-end vehicles, with built-in verification, secure payment processing, and a user experience that reflects the premium nature of the service.

### Team

- **Kushal Achar** - Lead Developer & Designer

## Features

- **User Authentication**: Secure signup/login with password hashing and validation
- **Luxury Car Listings**: Browse available vehicles with detailed information
- **Advanced Search**: Filter cars by location and other criteria
- **Booking System**: Interactive calendar for date selection with availability checking
- **Messaging System**: Built-in communication between owners and renters with notification badges
- **User Profiles**: Comprehensive dashboards showing earnings, bookings, and reviews
- **Review & Rating System**: Transparent feedback mechanism for users
- **Responsive Design**: Modern UI with glass-morphism effects and gold accents

## Tech Stack

- **Backend**: Python Flask 3.1.0
- **Database**: SQLAlchemy 2.0.40 with SQLite
- **Authentication**: Flask-Login 0.6.3
- **Frontend**: HTML5, CSS3, JavaScript
- **UI Framework**: Custom CSS with responsive design
- **Icons**: Font Awesome
- **Fonts**: Orbitron, Roboto

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git (optional, for cloning)

### Installation

1. **Clone the repository** (or download the ZIP file):
```bash
git clone https://github.com/kuachar/LuxuryCarShare.git
cd LuxuryCarShare
```

2. **Create and activate a virtual environment**:
```bash
# On Windows
python -m venv .venv
.venv\Scripts\activate

# On macOS/Linux
python -m venv .venv
source .venv/bin/activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Initialize the database**:
```bash
python app.py
```
The database will be automatically created in the `instance` folder.

5. **Run the application**:
```bash
python app.py
```

6. **Access the application**:
Open your browser and navigate to `http://127.0.0.1:5000`

### Configuration

- The application uses a SQLite database located in the `instance` directory
- To change the database configuration, modify the `SQLALCHEMY_DATABASE_URI` in `app.py`
- For production deployment, update the `SECRET_KEY` in `app.py` to a secure value

## Deployment

### Local Deployment

The application can be run locally using the setup instructions above.

### Production Deployment

For production deployment, consider the following platforms:

- **Heroku**: Easy deployment with minimal configuration
- **AWS Elastic Beanstalk**: Scalable solution for production environments
- **PythonAnywhere**: Simple hosting for Flask applications

Deployment steps will vary based on the platform chosen. For production, ensure you:

1. Set environment variables for sensitive information
2. Configure a production-ready database (PostgreSQL recommended)
3. Use a WSGI server like Gunicorn
4. Set `DEBUG=False` in production

## Test Plan

### Manual Testing

1. **User Authentication Tests**:
   - Register a new user with valid credentials
   - Attempt to register with an existing email (should fail)
   - Login with valid credentials
   - Attempt to login with invalid credentials (should fail)
   - Test password change functionality
   - Test logout functionality

2. **Car Management Tests**:
   - Add a new car with valid details
   - Edit an existing car
   - Verify car appears in search results
   - Test car filtering by location

3. **Booking System Tests**:
   - Create a booking for an available car
   - Attempt to book an unavailable date (should fail)
   - Approve a booking as a car owner
   - Reject a booking as a car owner
   - Verify booking appears in user's profile

4. **Messaging System Tests**:
   - Send a message to another user
   - Verify notification badge appears
   - Test "Mark All as Read" functionality
   - Verify conversation history is maintained

5. **Review System Tests**:
   - Submit a review for a completed booking
   - Verify rating calculation is correct
   - Test review editing functionality

### Automated Testing

While the current implementation doesn't include automated tests, here's how you could implement them:

1. **Install testing dependencies**:
```bash
pip install pytest pytest-flask
```

2. **Create a test directory**:
```bash
mkdir tests
touch tests/__init__.py
touch tests/test_routes.py
touch tests/test_models.py
```

3. **Run tests**:
```bash
pytest
```

### Test User Accounts

For testing purposes, you can use these credentials:
- Email: `admin@example.com`, Password: `password`
- Email: `lebron@example.com`, Password: `password`
- Email: `kushal@example.com`, Password: `password`

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Flask and SQLAlchemy communities for excellent documentation
- Unsplash for luxury car images
- Font Awesome for the icon set
- Indiana University S428 course staff for guidance and support#   L u x u r y C a r S h a r e 
 
 #   L u x u r y C a r S h a r e 
 
 #   L u x u r y C a r S h a r e 
 
 
