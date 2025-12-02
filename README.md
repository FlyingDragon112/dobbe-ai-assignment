# 🏥 Doctor Appointment Scheduling System

An AI-powered medical appointment scheduling system with chatbot interface for patients and doctors.

## 📹 Demo Video

[![Dobbe AI Demo](https://img.youtube.com/vi/EFbpBs7OLt8/0.jpg)](https://www.youtube.com/watch?v=EFbpBs7OLt8)

[Watch the demo video on YouTube](https://www.youtube.com/watch?v=EFbpBs7OLt8)

## ✨ Features

### Patient Portal
- 🔐 Secure login system
- 💬 AI chatbot for appointment booking
- 📅 Check doctor availability
- 📧 Email confirmations via Gmail API
- 📆 Google Calendar integration

### Doctor Portal
- 🔐 Secure login system
- 💬 AI chatbot for queries (natural language to SQL)
- 📊 Generate appointment reports
- 📤 Send reports to Slack
- 📈 View today's and weekly schedules

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | React.js |
| Backend | FastAPI (Python) |
| Database | PostgreSQL |
| AI/LLM | LangChain + OpenAI GPT-4 |
| Calendar | Google Calendar API |
| Email | Gmail API |
| Notifications | Slack Webhooks |

## 📁 Project Structure

```
├── backend/
│   ├── app.py              # FastAPI server
│   ├── credentials.json    # Google API credentials
│   └── token.pickle        # Google auth token
├── my-app/
│   ├── src/
│   │   ├── App.js          # Main React app
│   │   ├── login.jsx       # Login page
│   │   ├── patient.jsx     # Patient portal
│   │   ├── doctor.jsx      # Doctor portal
│   │   └── *.css           # Stylesheets
│   └── public/
└── requirements.txt        # Python dependencies
```

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL
- Google Cloud Console account (for Calendar & Gmail APIs)

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/doctor-appointment-system.git
cd doctor-appointment-system
```

### 2. Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv .env
.env\Scripts\activate  # Windows
# source .env/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Start server
uvicorn app:app --reload
```

### 3. Setup Frontend

```bash
cd my-app

# Install dependencies
npm install

# Start development server
npm start
```

### 4. Setup Database

```sql
-- Create tables
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    login_id TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    type TEXT NOT NULL  -- 'patient' or 'doctor'
);

CREATE TABLE appointments (
    id SERIAL PRIMARY KEY,
    doctorid TEXT NOT NULL,
    startTime TIMESTAMP NOT NULL,
    endTime TIMESTAMP NOT NULL,
    available BOOLEAN NOT NULL
);

-- Add sample data
INSERT INTO users (login_id, password, type) VALUES 
    ('patient1', 'password123', 'Patient'),
    ('doctor1', 'password123', 'Doctor');

INSERT INTO appointments (doctorid, startTime, endTime, available) VALUES 
    ('doctor1', '2025-12-05T10:00:00', '2025-12-05T11:00:00', TRUE),
    ('doctor1', '2025-12-05T14:00:00', '2025-12-05T15:00:00', TRUE);
```

### 5. Setup Google APIs

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable **Google Calendar API** and **Gmail API**
4. Create OAuth 2.0 credentials
5. Download `credentials.json` to `backend/` folder
6. Add your email as a test user in OAuth consent screen

### 6. Setup Slack (Optional)

1. Go to [Slack API](https://api.slack.com/apps)
2. Create a new app with Incoming Webhooks
3. Copy webhook URL to `SLACK_WEBHOOK_URL` in `app.py`

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/login` | POST | User authentication |
| `/chat` | POST | Patient chatbot |
| `/chat-doctor` | POST | Doctor chatbot |
| `/generate-report` | POST | Generate doctor report |
| `/doctor/{id}/available-timeslots` | GET | Get available slots |

## 💬 Example Usage

### Patient
```
"Show me available slots for doctor1"
"Book an appointment for tomorrow at 10am"
```

### Doctor
```
"How many appointments do I have today?"
"Generate my report"
"How many patients visited yesterday?"
```

## 📄 License

MIT License

## 👤 Author

Arnav Agarwal