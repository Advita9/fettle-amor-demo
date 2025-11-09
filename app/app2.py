from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from twilio.rest import Client
import os

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Twilio config
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
FROM_WHATSAPP = "whatsapp:+14155238886"  # Twilio sandbox number
TO_WHATSAPP = "whatsapp:+918052407029"   # Hospital admin number
client = Client(ACCOUNT_SID, AUTH_TOKEN)


@app.post("/webhook/escalation")
async def escalation_webhook(request: Request):
    data = await request.json()
    print("📩 Received escalation webhook:", data)

    try:
        args = (
            data.get("message", {})
            .get("toolCalls", [{}])[0]
            .get("function", {})
            .get("arguments", {})
        )
        patient_name = args.get("patient_name", "Unknown")
        issue_category = args.get("issue_category", "Unknown")
        issue_description = args.get("issue_description", "No details provided")

        msg_text = (
            f"⚠️ *Escalation Alert!*\n\n"
            f"👤 *Patient:* {patient_name}\n"
            f"📂 *Issue:* {issue_category}\n"
            f"📝 *Details:* {issue_description}\n\n"
            f"Please review this immediately."
        )

        message = client.messages.create(
            from_=FROM_WHATSAPP,
            to=TO_WHATSAPP,
            body=msg_text,
        )

        print(f"✅ WhatsApp alert sent: {message.sid}")
        return {"status": "success", "message_sid": message.sid}

    except Exception as e:
        print("❌ Error:", e)
        return {"status": "error", "details": str(e)}


@app.get("/")
async def root():
    return {"message": "Escalation webhook running ✅"}

