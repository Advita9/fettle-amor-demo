from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import boto3
import psycopg2
import os
from datetime import datetime

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME") or "fettle-transcript"
AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME") or "ap-south-1"
print(AWS_ACCESS_KEY_ID,AWS_SECRET_ACCESS_KEY,AWS_STORAGE_BUCKET_NAME,AWS_S3_REGION_NAME)
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_S3_REGION_NAME
)

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")

def get_db_connection():
    """Establish PostgreSQL connection"""
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        sslmode="require"
    )

@app.get("/")
async def root():
    return {"message": "Transcript upload service running"}

@app.post("/upload-transcript")
async def upload_transcript(request: Request):
    """
    Receives JSON payload from Make/Vapi,
    converts transcript to .txt,
    uploads to S3,
    stores link in Postgres.
    """
    data = await request.json()

    vapi_call_id = data.get("vapi_call_id")
    patient_name = data.get("patient_name", "Unknown")
    transcript = data.get("transcript", "")

    if not transcript:
        return {"error": "Transcript missing in payload"}

    try:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_name = f"{patient_name}_{timestamp}.txt"

        formatted_transcript = transcript.replace("\\n", "\n").strip()

        s3.put_object(
            Bucket=AWS_STORAGE_BUCKET_NAME,
            Key=file_name,
            Body=formatted_transcript.encode("utf-8"),
            ContentType="text/plain"
        )

        s3_url = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/{file_name}"

        conn = get_db_connection()
        cur = conn.cursor()

        insert_query = """
        INSERT INTO public.call_logs (vapi_call_id, hospital, status, summary)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
        """
        cur.execute(insert_query, (vapi_call_id, "Amor", False, s3_url))
        conn.commit()

        cur.close()
        conn.close()

        print(f"Transcript uploaded to S3: {s3_url}")
        return {
            "status": "success",
            "vapi_call_id": vapi_call_id,
            "s3_url": s3_url
        }

    except Exception as e:
        print(" Error:", e)
        return {"error": str(e)}

