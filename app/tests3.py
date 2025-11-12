# test_s3.py
import boto3, os
from dotenv import load_dotenv

load_dotenv()
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_S3_REGION_NAME")
)
try:
    response = s3.list_buckets()
    print("✅ Buckets:", [b['Name'] for b in response['Buckets']])
except Exception as e:
    print("❌ Error:", e)

