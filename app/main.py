from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from twilio.rest import Client
import requests
import os
from datetime import datetime, timezone

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
FROM_WHATSAPP = "whatsapp:+14155238886"  
TO_WHATSAPP = "whatsapp:+917032451866"   
client = Client(ACCOUNT_SID, AUTH_TOKEN)


BACKEND_LOGIN_URL = "http://13.204.53.17:8000/api/login/"
BACKEND_SYNC_URL = "http://13.204.53.17:8000/api/sync-call-data/"
BACKEND_TOKEN = None


def get_backend_token():
    """Authenticate admin and get JWT token from backend."""
    global BACKEND_TOKEN
    if BACKEND_TOKEN:
        return BACKEND_TOKEN

    payload = {
        "email": "admin@gmail.com",
        "password": "admin",
        "is_admin": True
    }
    try:
        resp = requests.post(BACKEND_LOGIN_URL, json=payload)
        resp.raise_for_status()
        BACKEND_TOKEN = resp.json().get("token")
        print("Logged into backend, got token.")
        return BACKEND_TOKEN
    except Exception as e:
        print("Failed to get backend token:", e)
        return None


@app.post("/webhook/appointment")
async def appointment_webhook(request: Request):
    """
    Receives appointment booking info from Vapi,
    sends WhatsApp message via Twilio,
    and posts call transcription + summary to backend.
    """
    data = await request.json()
    print("Incoming webhook data:", data)

    try:
        # Extract appointment details
        args = data.get("message", {}).get("toolCalls", [{}])[0].get("function", {}).get("arguments", {})
        patient_name = args.get("patient_name", "Unknown")
        doctor_name = args.get("doctor_name", "Unknown")
        speciality = args.get("speciality", "Unknown")
        date = args.get("date", "Unknown")
        time = args.get("time", "Unknown")
        caller_number = args.get("caller_number", "+91XXXXXXXXXX")

        # Send WhatsApp Message 
        msg_text = (
            f"📅 *New Appointment Booked!*\n\n"
            f"👤 *Patient:* {patient_name}\n"
            f"🩺 *Doctor:* {doctor_name}\n"
            f"🏥 *Speciality:* {speciality}\n"
            f"🕒 *Date:* {date}\n"
            f"🕘 *Time:* {time}\n\n"
            f"Please prepare accordingly and confirm in HMS."
        )
        message = client.messages.create(from_=FROM_WHATSAPP, to=TO_WHATSAPP, body=msg_text)
        print(f"WhatsApp message sent: {message.sid}")

        # Compose call log data (mock for now)
        started_at = datetime.now(timezone.utc).isoformat()
        ended_at = datetime.now(timezone.utc).isoformat()
        duration = 180  # assume 3 mins for demo
        summary = f"Patient {patient_name} scheduled appointment with {doctor_name} ({speciality})."

        # Post to backend 
        token = get_backend_token()
        if not token:
            raise Exception("No backend token available")

        headers = {"Authorization": f"Bearer {token}"}

        payload = {
            "call_log": {
                "status": "completed-by-agent",
                "started_at": started_at,
                "ended_at": ended_at,
                "cost": 0.0,
                "summary": summary,
                "caller_number": caller_number,
                "hospital": "Medicity"
            },
            "conversation_turns": [
                {"role": "user", "message": f"I want an appointment in {speciality}.", "timestamp": started_at},
                {"role": "assistant", "message": f"Scheduled with {doctor_name} at {time} on {date}.", "timestamp": ended_at}
            ]
        }

        resp = requests.post(BACKEND_SYNC_URL, json=payload, headers=headers)
        print(f"Sent data to backend ({resp.status_code}):", resp.text[:200])

        return {"status": "success", "sent_message": msg_text, "backend_sync": resp.status_code}

    except Exception as e:
        print(" Error processing webhook:", e)
        return {"status": "error", "error": str(e)}


@app.get("/")
async def root():
    return {"message": "Appointment webhook server running"}

