```markdown
# SmartCook

SmartCook is an AI-powered meal planning dashboard for university hostels. It predicts expected meal attendance, recommends cooking quantities, tracks actual attendance, and shows food waste analytics to help reduce overcooking.

## Features

- Predicts headcount for Breakfast, Lunch, and Dinner
- Calculates recommended cooking quantities
- Detects event impact such as weekends, exams, and festivals
- Logs actual attendance and cooked portions
- Shows food waste and savings analytics
- Includes dashboard and history pages
- Provides REST API endpoints for predictions, logs, analytics, and calendar events

## Tech Stack

- Python
- Flask
- Pandas
- NumPy
- Scikit-learn
- Joblib
- Matplotlib
- Pytest
- HTML, CSS, JavaScript
- Chart.js

## Project Structure

```text
Smart_Cook/
├── api/
│   └── app.py
├── analytics/
├── data_loader/
├── model/
│   ├── predictor.py
│   ├── train_model.py
│   ├── smartcook_model.pkl
│   └── smartcook_scaler.pkl
├── models/
├── static/
├── templates/
├── tests/
├── utils/
├── requirements.txt
├── Procfile
└── README.md
```

## Installation

```bash
git clone https://github.com/Akshat-240/Smart_Cook.git
cd Smart_Cook
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run Locally

```bash
python api/app.py
```

Open:

```text
http://localhost:5000
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/` | Dashboard page |
| GET | `/history` | Prediction history page |
| GET | `/api` | API overview |
| GET/POST | `/predict` | Live prediction endpoint |
| POST | `/cooking-plan` | Generate cooking plan |
| GET | `/cooking-plan/tomorrow` | Tomorrow's meal plan |
| POST | `/logs` | Add attendance log |
| GET | `/logs` | Read attendance logs |
| DELETE | `/logs` | Delete attendance log |
| GET | `/analytics/waste-graph` | Waste chart data |
| GET | `/analytics/savings` | Savings summary |
| GET | `/calendar/upcoming` | Upcoming event flags |
| GET | `/calendar/detect` | Detect event for a date |

## Example Prediction Request

```bash
curl "http://localhost:5000/predict?date=2026-06-10&meal=Dinner"
```

## Run Tests

```bash
python -m pytest -q
```

## Deployment

The project includes a `Procfile` for deployment platforms that support Gunicorn:

```text
web: gunicorn api.app:app
```

Make sure the dependencies in `requirements.txt` are installed during deployment.

## Note

The app currently stores attendance logs in CSV files. For production deployment, using a persistent database is recommended so logs are not lost on platforms with temporary filesystems.
