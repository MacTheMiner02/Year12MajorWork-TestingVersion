# This file contains all the input validation functions required by app.py

# Imports
import re
from email_validator import validate_email, EmailNotValidError
import bleach

# The validate input function just makes sure that each input is not empty
def validate_input(field):
    if not field or field.strip() == '':
        return False
    return True

# Validate password makes sure that the password is secure enough, for the user's benefit
def validate_password(password):
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True

# Validate email address uses the validate_email library to make sure the email is valid
def validate_email_address(email):
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False

# Validate YouTube link uses regex coding to ensure that the link given follows either of the two valid formats
def validate_youtube_link(link):
    if re.match(r'https://www\.youtube\.com/watch\?v=[a-zA-Z0-9\-_]{11}', link):
        return True
    if re.match(r'https://youtu\.be/[a-zA-Z0-9\-_]{11}', link):
        return True
    return False

def sanitize_input(value):
    return bleach.clean(value)