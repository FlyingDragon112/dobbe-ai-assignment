from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_agent
from typing import List, Dict
import psycopg2
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import base64
from email.mime.text import MIMEText
import requests

from langchain_community.utilities import SQLDatabase
from datetime import datetime, timedelta

# Initializing FastAPI
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Postgres DB INFO
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = ""
DB_USER = ""
DB_PASS = ""

# Calendar Info
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.send'
]

context_chain: Dict[str, List[dict]] = {}

def get_db_conn():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

def get_google_service(service_name: str, version: str):
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build(service_name, version, credentials=creds)

def get_calendar_service():
    return get_google_service('calendar', 'v3')

def get_gmail_service():
    return get_google_service('gmail', 'v1')

def send_email(to_email: str, subject: str, body: str) -> str:
    """Send an email using Gmail API"""
    try:
        service = get_gmail_service()
        message = MIMEText(body)
        message['to'] = to_email
        message['subject'] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        send_message = service.users().messages().send(
            userId='me',
            body={'raw': raw}
        ).execute()
        return f"Email sent successfully! Message ID: {send_message['id']}"
    except Exception as e:
        return f"Error sending email: {str(e)}"

llm = ChatOpenAI(
    base_url="https://models.github.ai/inference",
    model="openai/gpt-4.1",
    api_key=""
)

# Patient Tool 1
@tool
def doctor_availability_tool(doctorid: str) -> str:
    """
    Returns available timeslots for a doctor given their doctorid.
    Use this tool when the user asks about a doctor's availability.
    """
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT startTime, endTime FROM appointments WHERE doctorid = %s AND available = TRUE;",
            (doctorid,)
        )
        slots = cur.fetchall()
        cur.close()
        conn.close()
        if not slots:
            return f"No available timeslots for doctor {doctorid}."
        return "\n".join([f"{slot[0]} - {slot[1]}" for slot in slots])
    except Exception as e:
        return f"Error fetching timeslots: {str(e)}"

# Patient Tool 2
@tool
def schedule_appointment_tool(doctorid: str, start_time: str, end_time: str, patient_name: str, patient_email: str) -> str:
    """
    Schedules an appointment with a doctor via Google Calendar and sends email confirmation.
    Use this tool when the user wants to book an appointment.
    Args:
        doctorid: The doctor's ID
        start_time: Start time in format 'YYYY-MM-DDTHH:MM:SS'
        end_time: End time in format 'YYYY-MM-DDTHH:MM:SS'
        patient_name: The patient's name
        patient_email: The patient's email address for confirmation\
    
    Always ask for patient name and email
    """
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM appointments WHERE doctorid = %s AND startTime = %s AND endTime = %s AND available = TRUE;",
            (doctorid, start_time, end_time)
        )
        slot = cur.fetchone()
        
        if not slot:
            cur.close()
            conn.close()
            return "This timeslot is not available."
        
        slot_id = slot[0]
        cur.close()
        conn.close()

        service = get_calendar_service()
        event = {
            'summary': f'Appointment with Doctor {doctorid}',
            'description': f'Patient: {patient_name}\nEmail: {patient_email}',
            'start': {
                'dateTime': start_time,
                'timeZone': 'Asia/Kolkata',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'Asia/Kolkata',
            },
        }
        created_event = service.events().insert(calendarId='primary', body=event).execute()

        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(
            "UPDATE appointments SET available = FALSE WHERE id = %s;",
            (slot_id,)
        )
        conn.commit()
        cur.close()
        conn.close()

        email_subject = "Appointment Confirmation"
        email_body = f"""
            Dear {patient_name},

            Your appointment has been confirmed!

            Details:
            - Doctor: {doctorid}
            - Date/Time: {start_time} to {end_time}
            - Calendar Event: {created_event.get('htmlLink')}

            Thank you for booking with us.

            Best regards,
            Medical Appointment System
        """
        email_result = send_email(patient_email, email_subject, email_body)

        return f"Appointment scheduled successfully!\nEvent ID: {created_event.get('id')}\nCalendar Link: {created_event.get('htmlLink')}\n{email_result}"
    
    except Exception as e:
        return f"Error scheduling appointment: {str(e)}"

# Patient Tool 3
@tool
def send_email_tool(to_email: str, subject: str, body: str) -> str:
    """
    Sends an email to the specified email address.
    Use this tool when the user wants to send an email.
    Args:
        to_email: Recipient's email address
        subject: Email subject
        body: Email body content
    """
    return send_email(to_email, subject, body)

# Patient Agent
tools = [doctor_availability_tool, schedule_appointment_tool, send_email_tool]

agent = create_agent(llm, tools)

class LoginRequest(BaseModel):
    login_id: str
    password: str
    type: str

class ChatRequest(BaseModel):
    message: str
    login_id: str

@app.post("/login")
async def login(data: LoginRequest):
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT login_id, password, type FROM users WHERE login_id = %s AND password = %s AND type = %s;",
            (data.login_id, data.password, data.type)
        )
        result = cur.fetchone()
        cur.close()
        conn.close()
        if result:
            context_chain[data.login_id] = []
            return {
                "login_id": result[0],
                "password": result[1],
                "type": result[2]
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Patient Chat Endpoint
@app.post("/chat")
async def chat(data: ChatRequest):
    try:
        login_id = data.login_id

        if login_id not in context_chain:
            context_chain[login_id] = []

        context_chain[login_id].append({
            "role": "user",
            "content": data.message
        })

        response = agent.invoke({"messages": context_chain[login_id]})
        messages = response["messages"]

        assistant_reply = ""
        for msg in reversed(messages):
            if hasattr(msg, 'content') and msg.content:
                assistant_reply = msg.content
                break

        context_chain[login_id].append({
            "role": "assistant",
            "content": assistant_reply
        })
        
        return {"response": assistant_reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/context/{login_id}")
async def get_context(login_id: str):
    if login_id in context_chain:
        return {"context": context_chain[login_id]}
    return {"context": []}


# Postgres Connection for Doctor Chat
db = SQLDatabase.from_uri(f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# Doctor Tool 1
@tool
def ask_database(question: str) -> str:
    """
    Answers questions about appointments, patients, and schedules.
    Use this for ANY question about appointments, patients, or schedule data.
    
    Args:
        question: The question about appointments or patients
    """
    try:
        doctorid = "doctor1"
        if "[My Doctor ID is:" in question:
            start = question.find("[My Doctor ID is:") + len("[My Doctor ID is:")
            end = question.find("]", start)
            doctorid = question[start:end].strip()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Get table info from database
        table_info = db.get_table_info()
        
        sql_prompt = f"""Generate a PostgreSQL SELECT query.

            Tables:
            {table_info}

            Today: {today}
            Doctor ID: '{doctorid}'
            Booked appointments: available = FALSE
            Available slots: available = TRUE

            Return ONLY the SQL query, no explanation.

            Question: {question}

            SQL:"""

        sql_response = llm.invoke(sql_prompt)
        sql_query = sql_response.content.strip()
        
        if "```" in sql_query:
            parts = sql_query.split("```")
            for part in parts:
                if "select" in part.lower():
                    sql_query = part.replace("sql", "").strip()
                    break
        
        sql_query = sql_query.strip('"\'')
        print(f"Generated SQL: {sql_query}")

        sql_lower = sql_query.lower()
        if not sql_lower.strip().startswith("select"):
            return "Error: Only SELECT queries allowed."
        
        forbidden = ["insert", "update", "delete", "drop", "alter", "create", "truncate"]
        for word in forbidden:
            if word in sql_lower:
                return "Error: Operation not allowed."

        result = db.run(sql_query)
        return f"Result:\n{result}"
    
    except Exception as e:
        return f"Error: {str(e)}"

# Doctor Tool 2
@tool
def get_today_info() -> str:
    """
    Returns current date and time.
    """
    now = datetime.now()
    return f"Today: {now.strftime('%A, %B %d, %Y')} ({now.strftime('%Y-%m-%d')})"

# Report Generation
def generate_doctor_report(doctorid: str) -> str:
    """Generate human-readable report for doctor"""
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        
        today = datetime.now().date()
        week_end = today + timedelta(days=7)

        cur.execute("""
            SELECT starttime, endtime 
            FROM appointments 
            WHERE doctorid = %s AND DATE(starttime) = %s AND available = FALSE
            ORDER BY starttime
        """, (doctorid, today))
        today_appointments = cur.fetchall()

        cur.execute("""
            SELECT starttime, endtime 
            FROM appointments 
            WHERE doctorid = %s AND DATE(starttime) > %s AND DATE(starttime) <= %s AND available = FALSE
            ORDER BY starttime
        """, (doctorid, today, week_end))
        week_appointments = cur.fetchall()
        
        cur.close()
        conn.close()

        report = f"""
📋 TODAY'S REPORT ({today.strftime('%A, %B %d, %Y')})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 SCHEDULED APPOINTMENTS TODAY
"""
        
        if today_appointments:
            for start, end in today_appointments:
                start_str = start.strftime('%H:%M') if start else 'N/A'
                end_str = end.strftime('%H:%M') if end else 'N/A'
                report += f"  • {start_str} - {end_str}\n"
        else:
            report += "  No appointments scheduled for today.\n"
        
        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📆 APPOINTMENTS SCHEDULED FOR THE WEEK
"""
        
        if week_appointments:
            current_date = None
            for start, end in week_appointments:
                appt_date = start.date() if start else None
                if appt_date != current_date:
                    current_date = appt_date
                    report += f"\n  {appt_date.strftime('%A, %B %d')}:\n"
                start_str = start.strftime('%H:%M') if start else 'N/A'
                end_str = end.strftime('%H:%M') if end else 'N/A'
                report += f"    • {start_str} - {end_str}\n"
        else:
            report += "  No appointments scheduled for the week.\n"
        
        report += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        return report
    
    except Exception as e:
        return f"Error generating report: {str(e)}"

# Doctor Agent 
tools_doctor = [ask_database, get_today_info]

agent_doctor = create_agent(llm, tools_doctor)

# Doctor Chat Endpoint
@app.post("/chat-doctor")
async def chat_doctor(data: ChatRequest):
    try:
        login_id = data.login_id

        if login_id not in context_chain:
            context_chain[login_id] = []

        user_message = f"[My Doctor ID is: {login_id}] {data.message}"

        context_chain[login_id].append({
            "role": "user",
            "content": user_message
        })

        response = agent_doctor.invoke({"messages": context_chain[login_id]})
        messages = response["messages"]

        assistant_reply = ""
        for msg in reversed(messages):
            if hasattr(msg, 'content') and msg.content:
                if not hasattr(msg, 'tool_calls') or not msg.tool_calls:
                    assistant_reply = msg.content
                    break

        if not assistant_reply:
            assistant_reply = "I couldn't process your request. Please try again."

        context_chain[login_id].append({
            "role": "assistant",
            "content": assistant_reply
        })
        
        return {"response": assistant_reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Slack Communication
SLACK_WEBHOOK_URL = ""

def send_slack_notification(message: str) -> str:
    """Send notification to Slack"""
    try:
        if not SLACK_WEBHOOK_URL or SLACK_WEBHOOK_URL == "YOUR_SLACK_WEBHOOK_URL":
            return "Slack webhook not configured."
        
        payload = {"text": message}
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        
        if response.status_code == 200:
            return "Slack notification sent successfully!"
        else:
            return f"Slack error: {response.status_code}"
    except Exception as e:
        return f"Slack error: {str(e)}"

class ReportRequest(BaseModel):
    login_id: str
    send_to_slack: bool = True

# Report Generation Endpoint for Frontend
@app.post("/generate-report")
async def api_generate_report(data: ReportRequest):
    """Dashboard button endpoint to generate report"""
    try:
        report = generate_doctor_report(data.login_id)
        
        slack_status = ""
        if data.send_to_slack:
            slack_status = send_slack_notification(report)
        
        return {
            "report": report,
            "slack_status": slack_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    