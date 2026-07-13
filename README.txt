Welcome to my project! This project is a prototype for a website that connects people with local bands to hire for performances.
There are two types of account: a host account and a band account. The host account is owned by the people who want to hire a band while the band account is a shared account for the band.
This prototype includes:
    - A login page
    - Extensive security features such as password hashing, csrf tokens, and HTTPS
    - A dashboard for both band and host accounts
    - A search area to allow hosts to find bands to hire
    - A system for hosts to send a performance request to any band they wish
    - Notifications on the dashboard to know where your active booking requests are up to
    - The ability for a host to leave a review on bands that have performed for them

To run the server, the following things need to be done first:
    - Install requirements.txt
    - Run setup.py, this will create an .env file that contains a secret key to be used by flask for security
    - Run seed.py, this will populate the band database with 60 different band accounts for testing purposes

To run the webserver use the command "python app.py" in the terminal.

When you visit the dev server, the browser will likely pop up with a warning. This is because HTTPS is in use in this project.
As you are the one hosting the server, it is perfectly safe to continue despite the warning.
If it causes you problems, you can disable HTTPS by editing the last line of app.py.
Further instructions are found in the comment at the bottom of app.py

The password for all the band accounts has been set to "H3ll0w0rld!"