SeniorCare - Patient Management System

SeniorCare is a simple web app built with Python and Flask. It helps staff in senior living homes track patient vitals, medications, and daily notes.

Features

1. Patient Dashboard: Quick view of all residents.

2. Vitals Tracker: Log blood pressure and temperature with a full history.

3. Medication Checklist: Track which meds were given each day.

4. Doctor's Report: A one-page summary for doctors to review.

5. Health Alerts: Highlights patients with high BP or fever.

 How to run it locally

1. Requirements
Make sure you have Python installed on your computer.

2. Setup
Clone the project or download the files.

Install Flask by typing this in your terminal:

Bash
pip install flask
3. Start the app
Run the main file:

Bash
python care.py or py care.py
Once it starts, open your browser and go to: http://127.0.0.1:5000

Project Structure
care.py: The main Python code.

templates/: All the HTML pages.

static/: The CSS file for the design.

Seniorcare.db: The database where all patient info is saved.

Note for Deployment
Before you put this online (like on Render, Railway, or PythonAnywhere):

Change the secret_key in care.py to something unique.

Make sure your host supports SQLite (most do by default).

Add a requirements.txt file by running:
pip freeze > requirements.txt