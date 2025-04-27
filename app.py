from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os

# Get the base directory of the application
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "instance", "carshare.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Constants
ALLOWED_CITIES = ['Dallas, TX', 'Miami, FL', 'Los Angeles, CA', 'New York, NY', 'Las Vegas, NV']

# Add validation helpers
def validate_email(email):
    """Validate email format."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password_strength(password):
    """Validate password strength."""
    errors = []
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number")
    return errors

def validate_car_data(make, model, price_per_day, image_url):
    """Validate car data."""
    errors = []
    if not make or len(make.strip()) < 2:
        errors.append("Make is required and must be at least 2 characters")
    if not model or len(model.strip()) < 2:
        errors.append("Model is required and must be at least 2 characters")
    
    try:
        price = float(price_per_day)
        if price <= 0 or price > 10000:
            errors.append("Price must be a positive number less than $10,000 per day")
    except (ValueError, TypeError):
        errors.append("Price must be a valid number")
    
    if not image_url or not image_url.strip():
        errors.append("Image URL is required")
    
    return errors

def validate_booking_dates(start_date_str, end_date_str):
    """Validate booking dates."""
    errors = []
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        if start_date < today:
            errors.append("Start date cannot be in the past")
        
        if end_date < start_date:
            errors.append("End date must be after start date")
            
        if (end_date - start_date).days > 30:
            errors.append("Booking duration cannot exceed 30 days")
            
    except ValueError:
        errors.append("Invalid date format. Please use YYYY-MM-DD format")
    
    return errors, start_date if 'start_date' in locals() else None, end_date if 'end_date' in locals() else None

def validate_message_content(content):
    """Validate message content."""
    errors = []
    if not content or not content.strip():
        errors.append("Message content cannot be empty")
    elif len(content) > 1000:
        errors.append("Message is too long (maximum 1000 characters)")
    return errors

def validate_review(rating, comment):
    """Validate review data."""
    errors = []
    try:
        rating_val = int(rating)
        if rating_val < 1 or rating_val > 5:
            errors.append("Rating must be between 1 and 5 stars")
    except (ValueError, TypeError):
        errors.append("Rating must be a valid number")
    
    if comment and len(comment) > 500:
        errors.append("Review comment is too long (maximum 500 characters)")
    
    return errors

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    location = db.Column(db.String(100))
    bio = db.Column(db.Text)
    is_driver = db.Column(db.Boolean, default=False)
    cars = db.relationship('Car', backref='owner', lazy=True)
    bookings = db.relationship('Booking', backref='user', lazy=True)
    reviews_received = db.relationship('Review', backref='reviewed_user', lazy=True, foreign_keys='Review.reviewed_user_id')
    reviews_given = db.relationship('Review', backref='reviewer', lazy=True, foreign_keys='Review.reviewer_id')
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy=True)
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy=True)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

    def average_rating(self):
        reviews = Review.query.filter_by(reviewed_user_id=self.id).all()
        if not reviews:
            return 0
        return sum(review.rating for review in reviews) / len(reviews)

class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    make = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    price_per_day = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200))
    location = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    bookings = db.relationship('Booking', backref='car', lazy=True)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending') # pending, approved, rejected

    def is_approved(self):
        return self.status == 'approved'

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reviewed_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Database initialization
with app.app_context():
    db.create_all()
    print("Database tables created successfully!")

# Routes
@app.route('/')
def home():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    cars = Car.query.order_by(Car.created_at.desc()).all()
    return render_template('index.html', cars=cars, allowed_cities=ALLOWED_CITIES)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
            
        if not validate_email(email):
            flash('Invalid email format')
            return redirect(url_for('register'))
            
        errors = validate_password_strength(password)
        if errors:
            for error in errors:
                flash(error)
            return redirect(url_for('register'))
            
        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            name=name
        )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/profile')
@login_required
def profile():
    try:
        # Get user's cars, bookings and reviews
        user_cars = Car.query.filter_by(owner_id=current_user.id).order_by(Car.created_at.desc()).all()
        print(f"DEBUG - User ID: {current_user.id}, User Name: {current_user.name}, Cars Count: {len(user_cars)}")
        
        user_bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.start_date.desc()).all()
        print(f"DEBUG - Bookings Count: {len(user_bookings)}")
        
        reviews = Review.query.filter_by(reviewed_user_id=current_user.id).all()
        avg_rating = sum(review.rating for review in reviews) / len(reviews) if reviews else 0
        
        # Get booking requests for the user's cars
        car_ids = [car.id for car in user_cars]
        print(f"DEBUG - Car IDs: {car_ids}")
        
        booking_requests = Booking.query.filter(Booking.car_id.in_(car_ids), Booking.status == 'pending').all() if car_ids else []
        print(f"DEBUG - Booking Requests Count: {len(booking_requests)}")
        
        # Get approved bookings for the user's cars (for calendar view)
        approved_bookings = Booking.query.filter(Booking.car_id.in_(car_ids), Booking.status == 'approved').all() if car_ids else []
        print(f"DEBUG - Approved Bookings Count: {len(approved_bookings)}")
        
        # Calculate total earnings from approved bookings
        total_earnings = sum(booking.total_price for booking in approved_bookings)
        
        # Format booking data for calendar
        calendar_bookings = []
        for booking in approved_bookings:
            car = Car.query.get(booking.car_id)
            calendar_bookings.append({
                'id': booking.id,
                'car': f"{car.make} {car.model}",
                'start_date': booking.start_date.strftime('%Y-%m-%d'),
                'end_date': booking.end_date.strftime('%Y-%m-%d'),
                'renter': User.query.get(booking.user_id).name,
                'price': booking.total_price
            })
        
        # Get unread messages count
        unread_count = Message.query.filter_by(receiver_id=current_user.id, is_read=False).count()
        
        return render_template('profile.html', 
                            user=current_user, 
                            user_cars=user_cars,
                            user_bookings=user_bookings, 
                            booking_requests=booking_requests,
                            reviews=reviews,
                            avg_rating=avg_rating,
                            unread_count=unread_count,
                            approved_bookings=approved_bookings,
                            calendar_bookings=calendar_bookings,
                            total_earnings=total_earnings,
                            Review=Review)
    except Exception as e:
        print(f"ERROR in profile route: {str(e)}")
        import traceback
        traceback.print_exc()
        return render_template('profile.html', 
                            user=current_user, 
                            Review=Review,
                            user_cars=[], 
                            user_bookings=[], 
                            booking_requests=[],
                            reviews=[], 
                            avg_rating=0,
                            unread_count=0,
                            approved_bookings=[],
                            calendar_bookings=[],
                            total_earnings=0)

@app.route('/user/<int:user_id>')
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    user_cars = Car.query.filter_by(owner_id=user.id).order_by(Car.created_at.desc()).all()
    reviews = Review.query.filter_by(reviewed_user_id=user.id).all()
    avg_rating = sum(review.rating for review in reviews) / len(reviews) if reviews else 0
    
    # Check if the current user has completed bookings with this user
    can_review = False
    if current_user.is_authenticated and current_user.id != user.id:
        # Check if current user has booked cars from this user
        if user.cars:
            completed_bookings = Booking.query.filter(
                Booking.car_id.in_([car.id for car in user.cars]),
                Booking.user_id == current_user.id,
                Booking.status == 'approved'
            ).all()
            
            if completed_bookings:
                can_review = True
        
        # Check if this user has booked cars from current user
        if current_user.cars and not can_review:
            completed_bookings = Booking.query.filter(
                Booking.car_id.in_([car.id for car in current_user.cars]),
                Booking.user_id == user.id,
                Booking.status == 'approved'
            ).all()
            
            if completed_bookings:
                can_review = True
    
    return render_template('profile.html', 
                          user=user, 
                          user_cars=user_cars, 
                          reviews=reviews, 
                          avg_rating=avg_rating,
                          can_review=can_review,
                          Review=Review,
                          user_bookings=[], 
                          booking_requests=[],
                          unread_count=0,
                          approved_bookings=[],
                          calendar_bookings=[],
                          total_earnings=0)

@app.route('/write-review/<int:user_id>')
@login_required
def write_review(user_id):
    user = User.query.get_or_404(user_id)
    
    # Check if current user can review this user
    if user.id == current_user.id:
        flash('You cannot review yourself!')
        return redirect(url_for('user_profile', user_id=user_id))
    
    # Check if the current user has completed bookings with this user
    can_review = False
    
    # Check if current user has booked cars from this user
    if user.cars:
        completed_bookings = Booking.query.filter(
            Booking.car_id.in_([car.id for car in user.cars]),
            Booking.user_id == current_user.id,
            Booking.status == 'approved'
        ).all()
        
        if completed_bookings:
            can_review = True
    
    # Check if this user has booked cars from current user
    if current_user.cars and not can_review:
        completed_bookings = Booking.query.filter(
            Booking.car_id.in_([car.id for car in current_user.cars]),
            Booking.user_id == user.id,
            Booking.status == 'approved'
        ).all()
        
        if completed_bookings:
            can_review = True
    
    if not can_review:
        flash('You can only review users after completing a booking with them!')
        return redirect(url_for('user_profile', user_id=user_id))
    
    # Check if user has already reviewed this user
    existing_review = Review.query.filter_by(
        reviewer_id=current_user.id,
        reviewed_user_id=user_id
    ).first()
    
    return render_template('review.html', user=user, existing_review=existing_review)

@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not check_password_hash(current_user.password_hash, current_password):
        flash('Current password is incorrect', 'error')
        return redirect(url_for('profile'))
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'error')
        return redirect(url_for('profile'))
    
    errors = validate_password_strength(new_password)
    if errors:
        for error in errors:
            flash(error, 'error')
        return redirect(url_for('profile'))
    
    current_user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    flash('Password updated successfully', 'success')
    return redirect(url_for('profile'))

@app.route('/update-about', methods=['POST'])
@login_required
def update_about():
    bio = request.form.get('bio', '').strip()
    current_user.bio = bio
    db.session.commit()
    flash('About section updated successfully!')
    return redirect(url_for('profile'))

@app.route('/cars')
def cars():
    location = request.args.get('location', 'All Locations')
    search_query = request.args.get('search', '').lower()
    
    # Get all cars first
    query = Car.query
    
    # Apply location filter if specified and not "All Locations"
    if location and location != 'All Locations':
        query = query.filter_by(location=location)
    
    # Sort by most recent first
    query = query.order_by(Car.created_at.desc())
    
    # Get all cars matching the criteria
    cars = query.all()
    
    # Apply search filter if provided
    if search_query:
        cars = [car for car in cars if 
                search_query in car.make.lower() or 
                search_query in car.model.lower() or 
                search_query in str(car.price_per_day)]
    
    print(f"Found {len(cars)} cars" + (f" in {location}" if location != 'All Locations' else ""))
    
    # Add "All Locations" to the allowed cities list for the template
    locations_with_all = ['All Locations'] + list(ALLOWED_CITIES)
    return render_template('cars.html', cars=cars, location=location, allowed_cities=locations_with_all)

@app.route('/book/<int:car_id>', methods=['GET', 'POST'])
@login_required
def book_car(car_id):
    car = Car.query.get_or_404(car_id)
    
    # Check if user is trying to book their own car
    if car.owner_id == current_user.id:
        flash('You cannot book your own car.')
        return redirect(url_for('car_details', car_id=car_id))
    
    if request.method == 'POST':
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        
        errors, start_date, end_date = validate_booking_dates(start_date_str, end_date_str)
        if errors:
            for error in errors:
                flash(error)
            return redirect(url_for('book_car', car_id=car_id))
        
        # Validate dates
        if start_date < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
            flash('Start date cannot be in the past.')
            return redirect(url_for('book_car', car_id=car_id))
        
        if end_date < start_date:
            flash('End date must be after start date.')
            return redirect(url_for('book_car', car_id=car_id))
        
        # Check if car is available for the requested dates
        overlapping_bookings = Booking.query.filter_by(car_id=car_id).filter(
            (Booking.start_date <= end_date) & (Booking.end_date >= start_date)
        ).filter(Booking.status.in_(['pending', 'approved'])).all()
        
        if overlapping_bookings:
            flash('Car is not available for the selected dates.')
            return redirect(url_for('book_car', car_id=car_id))
        
        days = (end_date - start_date).days + 1
        total_price = car.price_per_day * days
        
        booking = Booking(
            car_id=car_id,
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            total_price=total_price,
            status='pending'
        )
        db.session.add(booking)
        db.session.commit()
        
        # Send notification message to car owner
        notification_message = Message(
            sender_id=current_user.id,
            receiver_id=car.owner_id,
            content=f"I've requested to book your {car.make} {car.model} from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} for ${total_price:.2f}. Please approve the booking once payment is received.",
            is_read=False
        )
        db.session.add(notification_message)
        db.session.commit()
        
        flash('Booking request sent! The owner will be notified and must approve your booking.')
        return redirect(url_for('profile'))
    
    # Get unavailable dates for the car
    unavailable_dates = []
    bookings = Booking.query.filter_by(car_id=car_id).filter(Booking.status.in_(['pending', 'approved'])).all()
    for booking in bookings:
        current_date = booking.start_date
        while current_date <= booking.end_date:
            unavailable_dates.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
    
    return render_template('book.html', car=car, today=datetime.now().strftime('%Y-%m-%d'), unavailable_dates=unavailable_dates)

@app.route('/add_car', methods=['GET', 'POST'])
@login_required
def add_car():
    if request.method == 'POST':
        location = request.form.get('location')
        # Ensure the location is one of the allowed cities
        if location not in ALLOWED_CITIES:
            flash('Please select a valid location from the provided options.')
            return redirect(url_for('add_car'))
            
        make = request.form.get('make')
        model = request.form.get('model')
        price_per_day = request.form.get('price_per_day')
        image_url = request.form.get('image_url')
        
        errors = validate_car_data(make, model, price_per_day, image_url)
        if errors:
            for error in errors:
                flash(error)
            return redirect(url_for('add_car'))
        
        car = Car(
            owner_id=current_user.id,
            make=make,
            model=model,
            price_per_day=float(price_per_day),
            image_url=image_url,
            location=location
        )
        db.session.add(car)
        db.session.commit()
        flash('Car added successfully!')
        return redirect(url_for('profile'))
    return render_template('add_car.html', allowed_cities=ALLOWED_CITIES)

@app.route('/edit_car/<int:car_id>', methods=['GET', 'POST'])
@login_required
def edit_car(car_id):
    car = Car.query.get_or_404(car_id)
    if car.owner_id != current_user.id:
        flash('You can only edit your own cars!')
        return redirect(url_for('profile'))
    
    if request.method == 'POST':
        location = request.form.get('location')
        # Ensure the location is one of the allowed cities
        if location not in ALLOWED_CITIES:
            flash('Please select a valid location from the provided options.')
            return redirect(url_for('edit_car', car_id=car_id))
            
        make = request.form.get('make')
        model = request.form.get('model')
        price_per_day = request.form.get('price_per_day')
        image_url = request.form.get('image_url')
        
        errors = validate_car_data(make, model, price_per_day, image_url)
        if errors:
            for error in errors:
                flash(error)
            return redirect(url_for('edit_car', car_id=car_id))
        
        car.make = make
        car.model = model
        car.price_per_day = float(price_per_day)
        car.image_url = image_url
        car.location = location
        db.session.commit()
        flash('Car updated successfully!')
        return redirect(url_for('profile'))
    
    return render_template('edit_car.html', car=car, allowed_cities=ALLOWED_CITIES)

@app.route('/delete_car/<int:car_id>', methods=['POST'])
@login_required
def delete_car(car_id):
    car = Car.query.get_or_404(car_id)
    if car.owner_id != current_user.id:
        flash('You can only delete your own cars.')
        return redirect(url_for('profile'))
    
    db.session.delete(car)
    db.session.commit()
    flash('Car deleted successfully!')
    return redirect(url_for('profile'))

@app.route('/cancel_booking/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        flash('You can only cancel your own bookings.')
        return redirect(url_for('profile'))
    
    booking.status = 'cancelled'
    db.session.commit()
    
    # Send cancellation notification to the car owner
    car = Car.query.get(booking.car_id)
    cancellation_message = Message(
        sender_id=current_user.id,
        receiver_id=car.owner_id,
        content=f"I've cancelled my booking for your {car.make} {car.model} from {booking.start_date.strftime('%Y-%m-%d')} to {booking.end_date.strftime('%Y-%m-%d')}.",
        is_read=False
    )
    db.session.add(cancellation_message)
    db.session.commit()
    
    flash('Booking cancelled successfully!')
    return redirect(url_for('profile'))

@app.route('/car/<int:car_id>')
def car_details(car_id):
    car = Car.query.get_or_404(car_id)
    return render_template('car_details.html', car=car, today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/messages')
@login_required
def messages():
    # Mark all messages as read
    unread_messages = Message.query.filter_by(receiver_id=current_user.id, is_read=False).all()
    for message in unread_messages:
        message.is_read = True
    db.session.commit()
    
    # Get all conversations (users the current user has exchanged messages with)
    sent_to = db.session.query(Message.receiver_id).filter_by(sender_id=current_user.id).distinct().all()
    received_from = db.session.query(Message.sender_id).filter_by(receiver_id=current_user.id).distinct().all()
    
    # Combine and remove duplicates
    conversation_ids = set([id[0] for id in sent_to + received_from])
    conversations = []
    
    for user_id in conversation_ids:
        user = User.query.get(user_id)
        if user:
            # Get the most recent message in this conversation
            latest_message = Message.query.filter(
                ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
                ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
            ).order_by(Message.created_at.desc()).first()
            
            conversations.append({
                'user': user,
                'latest_message': latest_message
            })
    
    # Sort conversations by the latest message time
    conversations.sort(key=lambda x: x['latest_message'].created_at, reverse=True)
    
    return render_template('messages.html', conversations=conversations)

@app.route('/conversation/<int:user_id>')
@login_required
def conversation(user_id):
    other_user = User.query.get_or_404(user_id)
    
    # Get all messages between the current user and the other user
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at).all()
    
    # Mark messages from the other user as read
    for message in messages:
        if message.sender_id == user_id and message.receiver_id == current_user.id and not message.is_read:
            message.is_read = True
    
    db.session.commit()
    
    return render_template('conversation.html', other_user=other_user, messages=messages)

@app.route('/send_message/<int:receiver_id>', methods=['POST'])
@login_required
def send_message(receiver_id):
    content = request.form.get('content')
    if not content:
        flash('Message cannot be empty.')
        return redirect(url_for('conversation', user_id=receiver_id))
    
    errors = validate_message_content(content)
    if errors:
        for error in errors:
            flash(error)
        return redirect(url_for('conversation', user_id=receiver_id))
    
    message = Message(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        content=content,
        is_read=False
    )
    
    db.session.add(message)
    db.session.commit()
    
    return redirect(url_for('conversation', user_id=receiver_id))

@app.route('/send_message', methods=['POST'])
@login_required
def send_message_new():
    receiver_id = request.form.get('receiver_id')
    content = request.form.get('content')
    if receiver_id and content:
        errors = validate_message_content(content)
        if errors:
            for error in errors:
                flash(error)
            return redirect(url_for('messages'))
        
        message = Message(sender_id=current_user.id, receiver_id=receiver_id, content=content)
        db.session.add(message)
        db.session.commit()
        flash('Message sent successfully!')
    return redirect(url_for('messages'))

@app.route('/approve_booking/<int:booking_id>', methods=['POST'])
@login_required
def approve_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    car = Car.query.get_or_404(booking.car_id)
    
    if car.owner_id != current_user.id:
        flash('You can only approve bookings for your own cars.')
        return redirect(url_for('profile'))
    
    # Check if there are any overlapping approved bookings
    overlapping_bookings = Booking.query.filter_by(car_id=booking.car_id, status='approved').filter(
        (Booking.start_date <= booking.end_date) & (Booking.end_date >= booking.start_date)
    ).all()
    
    if overlapping_bookings:
        flash('Cannot approve this booking as it overlaps with an already approved booking.')
        return redirect(url_for('profile'))
    
    booking.status = 'approved'
    db.session.commit()
    
    # Send confirmation message to the renter
    confirmation_message = Message(
        sender_id=current_user.id,
        receiver_id=booking.user_id,
        content=f"Your booking for {car.make} {car.model} from {booking.start_date.strftime('%Y-%m-%d')} to {booking.end_date.strftime('%Y-%m-%d')} has been approved. Thank you for your payment!",
        is_read=False
    )
    db.session.add(confirmation_message)
    db.session.commit()
    
    flash('Booking approved and renter notified!')
    return redirect(url_for('profile'))

@app.route('/reject_booking/<int:booking_id>', methods=['POST'])
@login_required
def reject_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    car = Car.query.get_or_404(booking.car_id)
    
    if car.owner_id != current_user.id:
        flash('You can only reject bookings for your own cars.')
        return redirect(url_for('profile'))
    
    booking.status = 'rejected'
    db.session.commit()
    
    # Send rejection message to the renter
    rejection_message = Message(
        sender_id=current_user.id,
        receiver_id=booking.user_id,
        content=f"Your booking request for {car.make} {car.model} from {booking.start_date.strftime('%Y-%m-%d')} to {booking.end_date.strftime('%Y-%m-%d')} has been rejected.",
        is_read=False
    )
    db.session.add(rejection_message)
    db.session.commit()
    
    flash('Booking rejected and renter notified.')
    return redirect(url_for('profile'))

@app.route('/review/<int:user_id>', methods=['POST'])
@login_required
def review_user(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('You cannot review yourself!', 'error')
        return redirect(url_for('user_profile', user_id=user_id))
    
    rating = request.form.get('rating')
    comment = request.form.get('comment', '').strip()
    
    errors = validate_review(rating, comment)
    if errors:
        for error in errors:
            flash(error, 'error')
        return redirect(url_for('user_profile', user_id=user_id))
    
    # Check if user has already reviewed this user
    existing_review = Review.query.filter_by(
        reviewer_id=current_user.id,
        reviewed_user_id=user_id
    ).first()
    
    if existing_review:
        # Update existing review
        existing_review.rating = int(rating)
        existing_review.comment = comment
        existing_review.created_at = datetime.utcnow()
        flash('Your review has been updated!', 'success')
    else:
        # Create new review
        review = Review(
            reviewer_id=current_user.id,
            reviewed_user_id=user_id,
            rating=int(rating),
            comment=comment
        )
        db.session.add(review)
        flash('Your review has been posted!', 'success')
    
    db.session.commit()
    return redirect(url_for('user_profile', user_id=user_id))

@app.route('/mark_all_read')
@login_required
def mark_all_read():
    """Mark all messages as read for the current user"""
    unread_messages = Message.query.filter_by(receiver_id=current_user.id, is_read=False).all()
    for message in unread_messages:
        message.is_read = True
    db.session.commit()
    flash('All messages marked as read')
    return redirect(url_for('messages'))

@app.context_processor
def inject_unread_count():
    """Inject unread message count into all templates"""
    if current_user.is_authenticated:
        unread_count = Message.query.filter_by(receiver_id=current_user.id, is_read=False).count()
        return {'unread_message_count': unread_count}
    return {'unread_message_count': 0}

if __name__ == '__main__':
    print("Starting application...")
    app.run(debug=True)