from app import app, db, BandUser
from werkzeug.security import generate_password_hash
import json


with open('seed_data.json') as f:
    data = json.load(f)

with app.app_context():
    BandUser.query.delete()
    db.session.commit()
    print("Database cleared")

    print("Seeding database. Please wait")

    bands = [BandUser(
        band_name=b['band_name'],
        email=b['email'],
        password=generate_password_hash(b['password']),
        genre=b['genre'],
        location=b['location'],
        youtube_link=b['youtube_link'],
        likes=b['likes'],
        dislikes=b['dislikes']
    ) for b in data]

    db.session.add_all(bands)
    db.session.commit()
    print("Database seeded successfully")