# Imports
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

import os
import datetime
import math

# Imports from other files
from security_utils import (validate_input, validate_password, validate_email_address,
                            validate_youtube_link, sanitize_input)
from genres import genres

# Create the flask app
app = Flask(__name__)

# Loads the .env file that is created by running setup.py, which contains the secret key
load_dotenv()

# Configuring the flask app
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Sets up the database and csrf protection apps
db = SQLAlchemy(app)
csrf = CSRFProtect(app)

# Creating the login manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Loads users from the database
@login_manager.user_loader
def load_user(user_id):
    if user_id.startswith('band_'):
        return BandUser.query.get(int(user_id[5:]))
    elif user_id.startswith('host_'):
        return HostUser.query.get(int(user_id[5:]))
    return None

# The band type user class that defines the columns of the band user database
class BandUser(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    band_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    youtube_link = db.Column(db.String(100), nullable=False)
    likes = db.Column(db.Integer, nullable=False, default=0)
    dislikes = db.Column(db.Integer, nullable=False, default=0)

    # Returns the band user's ID with an identifier to separate it from a host with the same ID
    def get_id(self):
        return f'band_{self.id}'

    # Debug statement that allows useful information to be outputted when the class is printed
    def __repr__(self):
        return f"<User {self.band_name}>"

# The host type user class that defines the columns of the host user database
class HostUser(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

    # Returns the host user's ID with an identifier to separate it from a band with the same ID
    def get_id(self):
        return f'host_{self.id}'

    # Debug statement that allows useful information to be outputted when the class is printed
    def __repr__(self):
        return f"<User {self.name}>"

# A database class used to track the bookings made
class Booking(db.Model):
    booking_id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, nullable=False)
    host_email = db.Column(db.String, nullable=False)
    band_id = db.Column(db.Integer, nullable=False)
    band_name = db.Column(db.String, nullable=False)
    band_email = db.Column(db.String, nullable=False)
    booking_location = db.Column(db.String, nullable=False)
    booking_date = db.Column(db.String, nullable=False)
    message = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False, default="pending")

# Creates the databases
with app.app_context():
    db.create_all()

# The home page route
@app.route('/')
def welcome():
    return render_template('welcome.html')

# The submit route for the band account creation form
@app.route('/submit-band', methods=['POST'])
def submit_band():
    band_name = request.form.get('band_name')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm-password')
    genre = request.form.get('genre')
    location = request.form.get('location')
    youtube_link = request.form.get('youtube_link')

    # As the return of the band creation render template is used many times, it is in its own function
    def return_band_temp():
        # A render template for the relevant signup page is returned with the previously filled out values filled
        # It also passes in the dictionary of genres so that it can be used to fill out the genre selection box
        print("REDIRECTED BACK TO BAND CREATION PAGE")
        return render_template("band-creation.html", band_name=band_name,
                               email=email, genre=genre, location=location,
                               youtube_link=youtube_link, genres=genres)

    # Validation of each of the fields
    # If a field does not pass the validation then flash() is used to send a warning
    if not validate_input(band_name):
        flash('Band must require a name')
        return return_band_temp()

    if not validate_input(email):
        flash('A contact email is required')
        return return_band_temp()
    if not validate_email_address(email):
        flash('Entered email address is not valid')
        return return_band_temp()
    # Searching the two user databases for the email inputted to make sure it is not already in use
    existing_user_band = BandUser.query.filter_by(email=email).first()
    existing_user_host = HostUser.query.filter_by(email=email).first()
    if existing_user_band or existing_user_host:
        flash('Entered email address is already in use by another account')
        return return_band_temp()

    if not validate_input(password):
        flash('A password is required')
        return return_band_temp()
    if not validate_password(password):
        flash('The inputted password does not match the requirements for a secure password')
        return return_band_temp()

    if not validate_input(confirm_password):
        flash('Confirmation of password is required')
        return return_band_temp()

    if not validate_input(genre):
        flash('A genre is required')
        return_band_temp()

    if not validate_input(location):
        flash('A location is required')
        return return_band_temp()

    if not validate_input(youtube_link):
        flash('A youtube link is required')
        return return_band_temp()
    if not validate_youtube_link(youtube_link):
        flash('A valid youtube link is required')
        return return_band_temp()

    # Sanitize inputs
    band_name = sanitize_input(band_name)
    email = sanitize_input(email)
    password = sanitize_input(password)
    confirm_password = sanitize_input(confirm_password)
    genre = sanitize_input(genre)
    location = sanitize_input(location)
    youtube_link = sanitize_input(youtube_link)

    # Confirms that the passwords match before submitting
    if confirm_password == password:
        # Hashes the password before submitting it to the database
        password = generate_password_hash(password)
        # Creates the user, sends it to the database, and logs the user in before redirecting them
        new_user = BandUser(band_name=band_name, email=email, password=password, genre=genre, location=location, youtube_link=youtube_link)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('dashboard'))
    else:
        flash("Passwords do not match")
        return return_band_temp()

# The submit route for the host account creation form
@app.route('/submit-host', methods=['POST'])
def submit_host():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm-password')

    # As the return of the host account creation render template is used many times, it is in its own function
    def return_host_temp():
        # A render template for the relevant signup page is returned with the previously filled out values filled
        # It also passes in the dictionary of genres so that it can be used to fill out the genre selection box
        return render_template("host-account-creation.html", name=name, email=email, genres=genres)

    # Validation of each of the fields
    # If a field does not pass the validation then flash() is used to send a warning
    if not validate_input(name):
        flash('A name is required for this account')
        # A render template for the relevant signup page is returned with the previously filled out values filled
        return return_host_temp()

    if not validate_input(email):
        flash('A contact email is required')
        return return_host_temp()
    if not validate_email_address(email):
        flash('Entered email address is not valid')
        return return_host_temp()

    # Searching the two user databases for the email inputted to make sure it is not already in use
    existing_user_band = BandUser.query.filter_by(email=email).first()
    existing_user_host = HostUser.query.filter_by(email=email).first()

    if existing_user_band or existing_user_host:
        flash('Entered email address is already in use by another account')
        return return_host_temp()

    if not validate_input(password):
        flash('A password is required')
        return return_host_temp()
    if not validate_password(password):
        flash('The inputted password does not match the requirements for a secure password')
        return return_host_temp()

    if not validate_input(confirm_password):
        flash('Confirmation of password is required')
        return return_host_temp()

    # Sanitize inputs
    name = sanitize_input(name)
    email = sanitize_input(email)
    password = sanitize_input(password)
    confirm_password = sanitize_input(confirm_password)

    # Confirms that the passwords match before submitting
    if confirm_password == password:
        # Hashes the password before submitting it to the database
        password = generate_password_hash(password)
        # Creates the user, sends it to the database, and logs the user in before redirecting them
        new_user = HostUser(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('dashboard'))
    else:
        flash('Passwords do not match')
        return return_host_temp()

# The about page route
@app.route('/about')
def about():
    return render_template('about.html')

# The sign-up page route
@app.route('/sign-up')
def sign_up():
    # If the user trys to go to the sign-up page without logging out first, they are redirected
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('sign-up.html')

# The login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    # If the user hits the submit button on the form
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Checks the user exists
        user = BandUser.query.filter_by(email=email).first()
        if not user:
            user = HostUser.query.filter_by(email=email).first()

        if not validate_input(email):
            flash("Please supply an email address")
            return render_template('login.html', email=email, password=password)

        if not validate_input(password):
            flash("Please supply a password")
            return render_template('login.html', email=email, password=password)

        # Checks the password is the same as the one in the database
        # This uses the check_password_hash() function of werkzeug
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials")
            return render_template('login.html')
        
    return render_template('login.html')

# The route for the band creation page
@app.route('/band-creation')
def band_creation():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('band-creation.html', genres=genres)

# The route for the host account creation page
@app.route('/host-account-creation')
def host_account_creation():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('host-account-creation.html')

# This route automatically sends the user to either dashboard route depending on what account type is logged in
@app.route('/dashboard')
@login_required
def dashboard():
    if isinstance(current_user, BandUser):
        return redirect(url_for('band_dashboard'))
    else:
        return redirect(url_for('host_dashboard'))

# The route for the band user dashboard. A logged in band user is required to visit this page
@app.route('/band-dashboard')
@login_required
def band_dashboard():
    if isinstance(current_user, HostUser):
        return redirect(url_for('dashboard'))

    band = BandUser.query.filter_by(id=current_user.id).first()
    overall_rating = round(band.likes / (band.dislikes + band.likes) * 100)
    stats = [overall_rating, band.likes, band.dislikes]

    # All the types of notification that should show up on the band dashboard are listed here
    all_notifs = ["pending", "host-seen-pending", "band-deny", "host-seen-band-deny", "band-accept", "host-deny", "host-seen-host-deny", "confirmed", "host-seen"]
    # Those statuses are then fed into the query
    notifications = Booking.query.filter(Booking.band_id == current_user.id, Booking.status.in_(all_notifs)).all()
    return render_template('band-dashboard.html', notifications=notifications, stats=stats)

# The route for the host user dashboard. A logged in host user is required to visit this page
@app.route('/host-dashboard')
@login_required
def host_dashboard():
    if isinstance(current_user, BandUser):
        return redirect(url_for('dashboard'))

    # Gets today's date
    date_today = datetime.datetime.strptime(datetime.datetime.now().date().strftime('%Y-%m-%d'), '%Y-%m-%d').date()
    # Checks each notification to see if the date is right to display the review prompt
    for notification in Booking.query:
        date_to_show = datetime.datetime.strptime(notification.booking_date, "%Y-%m-%d").date()
        print(f"{date_to_show}, {date_today}")
        if date_to_show < date_today and notification.status == "all-seen":
            notification.status = "unreviewed"
            db.session.commit()

    # All the types of notification that should show up on the host dashboard are listed here
    all_notifs = ["pending", "band-deny", "band-seen-band-deny", "band-accept", "band-seen-band-accept", "host-deny",
                  "band-seen-host-deny", "confirmed", "band-seen", "unreviewed"]
    # Those statuses are then fed into the query
    notifications = Booking.query.filter(Booking.host_id == current_user.id, Booking.status.in_(all_notifs)).all()

    return render_template('host-dashboard.html', notifications=notifications)

# This route is for the page that hosts will use to browse potential bands to hire
@app.route('/band-browse')
@login_required
def band_browse():
    if isinstance(current_user, BandUser):
        return redirect(url_for('dashboard'))

    # Calculates a score to decide what order the bands get displayed in
    def score(band):
        views = band.likes + band.dislikes
        likes = band.likes
        dislikes = band.dislikes
        return ((likes - dislikes) / (views + 1)) * math.log(views + 1)

    bands = BandUser.query.order_by(BandUser.band_name).all()
    ordered_bands = sorted(bands, key=score, reverse=True)

    return render_template('band-browse.html', bands=ordered_bands, genres=genres)

# This route is what allows the JavaScript that dynamically updates the bands to run
@app.route('/api/bands')
@login_required
def api_bands():
    # Setting some variable for the different search parameters
    search = request.args.get('band-search', '')
    genre_filter = request.args.get('genres', '')
    location_filter = request.args.get('location', '')

    def score(band):
        views = band.likes + band.dislikes
        likes = band.likes
        dislikes = band.dislikes
        return ((likes - dislikes) / (views + 1)) * math.log(views + 1)

    # Creates the query
    query = BandUser.query

    # The following three if statements slowly narrow down the results based on the parameters
    if search:
        query = query.filter(BandUser.band_name.ilike(f'%{search}%'))
    if genre_filter:
        genre_list = genre_filter.split(',')
        query = query.filter(BandUser.genre.in_(genre_list))
    if location_filter:
        query = query.filter(BandUser.location.ilike(f'%{location_filter}%'))

    # Orders the query by alphabetical
    bands = query.order_by(BandUser.band_name).all()
    ordered_bands = sorted(bands, key=score, reverse=True)

    # Returns a json response that gets sent to the JavaScript function
    return jsonify([{
        'id': band.id,
        'band_name': band.band_name,
        'genre': band.genre,
        'location': band.location,
        'likes': band.likes,
        'dislikes': band.dislikes
    } for band in ordered_bands])

# This route is where a host user can view the information about the band
@app.route('/band/<int:band_id>')
@login_required
def band_profile(band_id):
    if isinstance(current_user, BandUser):
        return redirect(url_for('dashboard'))
    band = BandUser.query.get_or_404(band_id)

    # Gets the video id for the different possible youtube video links
    if 'v=' in band.youtube_link:
        video_id = band.youtube_link.split('v=')[-1]
    elif 'youtu.be/' in band.youtube_link:
        video_id = band.youtube_link.split('youtu.be/')[-1]
    else:
        video_id = None

    # Creates the embed url and sends it to the page
    embed_url = f"https://www.youtube.com/embed/{video_id}"
    return render_template('band-info.html', band=band, embed_url=embed_url)

# This route sends a booking form to the database
@app.route('/book/<int:band_id>', methods=['POST'])
@login_required
def book_band(band_id):
    if isinstance(current_user, BandUser):
        return redirect(url_for('dashboard'))

    # Get the booking data from the form
    booking_location = request.form.get('location')
    booking_date = request.form.get('date')
    message = request.form.get('message')

    # Find the band data from the database
    band = BandUser.query.get_or_404(band_id)
    band_email = band.email
    band_name = band.band_name

    # Create a database entry object with the booking data
    new_booking = Booking(
        host_id=current_user.id,
        host_email=current_user.email,
        band_id=band_id,
        band_email=band_email,
        band_name=band_name,
        booking_location=booking_location,
        booking_date=booking_date,
        message=message
    )

    # Commit the booking data
    db.session.add(new_booking)
    db.session.commit()

    flash('Booking request successful!')
    return redirect(url_for('band_profile', band_id=band_id))

# The route for when the deny button is pressed on a notification
@app.route('/book/deny/<int:booking_id>', methods=['POST'])
@login_required
def band_deny_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    # All uses of the accept button by the band are programmed in here
    if isinstance(current_user, BandUser):
        if booking.status == 'pending' or booking.status == 'host-seen-pending':
            booking.status = 'band-deny'


    # All uses of the accept button by the host are programmed in here
    if isinstance(current_user, HostUser):
        if booking.status == 'band-accept' or booking.status == 'band-seen-band-accept':
            booking.status = 'host-deny'
        elif booking.status == 'unreviewed':
            band = BandUser.query.get_or_404(booking.band_id)
            band.dislikes += 1
            db.session.commit()
            booking.status = 'reviewed'

    db.session.commit()
    return redirect(url_for('dashboard'))

# The route for when the accept button is pressed on a notification
@app.route('/book/accept/<int:booking_id>', methods=['POST'])
@login_required
def band_accept_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    # All uses of the accept button by the band are programmed in here
    if isinstance(current_user, BandUser):
        if booking.status == 'pending' or booking.status == 'host-seen-pending':
            booking.status = 'band-accept'
        elif booking.status == 'band-deny':
            booking.status = 'band-seen-band-deny'
        elif booking.status == 'host-seen-band-deny':
            booking.status = 'all-seen-band-deny'
        elif booking.status == 'band-accept':
            booking.status = 'band-seen-band-accept'
        elif booking.status == 'host-deny':
            booking.status = 'band-seen-host-deny'
        elif booking.status == 'host-seen-host-deny':
            booking.status = 'all-seen-host-deny'
        elif booking.status == 'confirmed':
            booking.status = 'band-seen'
        elif booking.status == 'host-seen':
            booking.status = 'all-seen'


    # All uses of the accept button by the host are programmed in here
    if isinstance(current_user, HostUser):
        if booking.status == 'pending':
            booking.status = 'host-seen-pending'
        elif booking.status == 'band-deny':
            booking.status = 'host-seen-band-deny'
        elif booking.status == 'band-seen-band-deny':
            booking.status = 'all-seen-band-deny'
        elif booking.status == 'band-accept' or booking.status == 'band-seen-band-accept':
            booking.status = 'confirmed'
        elif booking.status == 'host-deny':
            booking.status = 'host-seen-host-deny'
        elif booking.status == 'band-seen-host-deny':
            booking.status = 'all-seen-host-deny'
        elif booking.status == 'confirmed':
            booking.status = 'host-seen'
        elif booking.status == 'band-seen':
            booking.status = 'all-seen'
        elif booking.status == 'unreviewed':
            band = BandUser.query.get_or_404(booking.band_id)
            band.likes += 1
            db.session.commit()
            booking.status = 'reviewed'

    # Commits the database changes to the database
    db.session.commit()
    return redirect(url_for('dashboard'))

# The logout route that logs the user out as soon as it is visited
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('welcome'))

# A debug route that shows some useful information for testing purposes
@app.route('/debug')
def debug():
    return f"User logged in: {current_user.is_authenticated}"

if __name__ == '__main__':
    # To disable HTTPS, change the line below to "app.run(debug=True)"
    app.run(debug=True, ssl_context='adhoc')