**Project Title**: Senior Care Web App

** Description**: A web app to help care staff track residents, their blood pressure, medications, and notes. It is simple and easy to run on a local machine.

**How to run locally (Windows)**
1. Install Python 3.13 or newer from python.org.
2. Open PowerShell and go to the project folder (where this README.md is):

```powershell
cd "c:\Users\Akim\Downloads\SeniorCare_WebApp\Senior Care_app"
```

3. Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

4. Install required packages:

```powershell
pip install Flask werkzeug
```

5. Run the app:

```powershell
python care.py or py care.py
```

6. Open a browser and go to `http://127.0.0.1:5000/`.

7. First time: register a user at the Register page, then log in and try the features.


- The app uses a local SQLite database file created automatically: `Seniorcare.db` in the same folder as `care.py`.
- Change the secret key in `care.py` before deploying to production (do not leave the default)

## How to run it 

### 1. Get the code

Clone the repo, or download and unzip it, then open a terminal **inside the project folder** (the folder that contains `Senior Care_app`).

### 2. Create a virtual environment

```bash
python -m venv .venv
```

If `python` does not work, try:

```bash
py -m venv .venv
```

### 3. Turn the virtual environment on

**Windows (PowerShell):**

```bash
.\.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**

```bash
.\.venv\Scripts\activate.bat
```

You should see `(.venv)` at the start of your terminal line when it worked.

### 4. Install the packages

```bash
pip install flask werkzeug
```

### 5. Start the app

From the **same project root** (not inside `Senior Care_app` unless you adjust the path):

```bash
python "Senior Care_app/care.py"
```

If `python` does not work:

```bash
py "Senior Care_app/care.py"
```

### 6. Open it in the browser

Go to:

**http://127.0.0.1:5000**

The first time you run the app, it creates a local SQLite database file (`Seniorcare.db`) next to where the app runs.

### 7. Stop the server

In the terminal where the app is running, press **Ctrl + C**.

---

## Troubleshooting

- **“Python was not found”** — Install Python from [python.org](https://www.python.org/downloads/) and tick “Add Python to PATH”, or use the `py` launcher as shown above.
- **“No module named flask”** — Make sure the virtual environment is activated (step 3), then run `pip install flask werkzeug` again.
- **Wrong folder** — The command in step 5 must be run from the folder that contains the `Senior Care_app` directory.

---

