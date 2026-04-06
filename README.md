SeniorCare : Patient Management System

SeniorCare is a simple web app built with Python and Flask. It helps staff in senior living homes track patient vitals, medications, and daily notes.

Features

1. Patient Dashboard: Quick view of all residents.

2. Vitals Tracker: Log blood pressure and temperature with a full history.

3. Medication Checklist: Track which meds were given each day.

4. Doctor's Report: A one-page summary for doctors to review.

5. Health Alerts: Highlights patients with high BP or fever.

 How to run it locally

1. Requirements

Make sure you have Python 3 installed on your computer.

2. Setup

Follow these steps to get the code onto your machine:

Step A: Clone the project Open your terminal or command prompt and run:

git clone https://github.com/tdorcas-akim/SeniorCare_WebApp.git

cd SeniorCare_WebApp

Step B: Install dependencies 

Install everything required using the requirements file:

pip install -r "Senior Care_app/requirements.txt"

3. Start the Application

Navigate into the application folder and start the server:

cd "Senior Care_app"

python care.py

(Note: If python doesn't work, try python3 care.py or py care.py)

4. Access the App

Once the terminal shows "Running on...", open your browser and go to:
 http://127.0.0.1:5000

Project Structure

1. care.py: The core logic.

2. templates/: HTML files (Jinja2) for the dashboard, login, and patient details.

3. static/: The CSS file for the design.

4. Seniorcare.db: The database where all patient info is saved.

5. requirements.txt: List of necessary Python libraries for the project.
