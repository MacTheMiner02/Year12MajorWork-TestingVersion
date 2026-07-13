import secrets
import os

if not os.path.exists('.env'):
    secret_key = secrets.token_hex(32)
    with open('.env', 'w') as f:
        f.write(f"SECRET_KEY={secret_key}")
    print("Generated .env file")
else:
    print(".env file already exists, skipping")