# Gym Membership Management Website

This project is a simple gym membership management website built with Python and Flask.

## Features

- Login page with username and password
- Dashboard for adding new gym members
- Fee collection tracking
- Membership expiry date monitoring
- Expiring membership alert count
- Member deletion option
- SQLite database support

## Default Login

- Username: admin
- Password: admin123

## Run the Project

1. Open a terminal in the project folder
2. Install dependencies:
   python -m pip install -r requirements.txt
3. Start the app:
   python app.py
4. Open your browser and visit:
   http://127.0.0.1:5000/login

## Project Structure

- app.py: Main Flask application
- templates/login.html: Login page
- templates/dashboard.html: Membership dashboard
- static/style.css: Styling for the website
- gym_members.db: SQLite database generated automatically
