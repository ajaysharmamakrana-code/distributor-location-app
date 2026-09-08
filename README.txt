# Distributor Location Web App

## What it does
SO -> mapped Distributor -> photo -> mandatory GPS -> submit -> Completed.
Data is saved in SQLite and can be downloaded as an Excel report.

## Run on Windows
1. Install Python 3.
2. Open Command Prompt in this folder.
3. Run:
   pip install -r requirements.txt
4. Run:
   python app.py
5. On the same laptop open:
   http://127.0.0.1:5000

## Important for mobile GPS
Modern mobile browsers require HTTPS for geolocation, except localhost.
For real mobile use by field users, deploy this project to an HTTPS host
(e.g. Render, Railway, PythonAnywhere, or your company's server with HTTPS).

## Local same-WiFi testing
The app binds to 0.0.0.0:5000, so the phone can open the laptop's IP address.
However, mobile browser GPS may be blocked on plain HTTP. For full GPS testing,
use an HTTPS tunnel or deploy it to an HTTPS host.

## Files
- app.py: Flask backend
- templates/index.html: mobile UI
- Distributor_Master.xlsx: your SO/distributor master
- submissions.db: created automatically
- uploads/: captured photos
- /report: Excel report download
