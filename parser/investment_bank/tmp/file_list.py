from google.cloud import storage
from google.oauth2.service_account import Credentials

from dotenv import load_dotenv
import base64
import json
import os

# .env 파일 로드
load_dotenv("tmp/.env")

encoded_google_secret = os.environ.get("GOOGLE_TRANSLATE_SECRET")
decoded_google_secret = base64.b64decode(encoded_google_secret).decode("utf-8")
google_secret_json = json.loads(decoded_google_secret)

credentials = Credentials.from_service_account_info(google_secret_json)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcs-key.json"  # 서비스 계정 JSON 경로

def list_files_in_gcs(bucket_name, prefix=""):
    """
    특정 GCS 버킷 내 특정 경로(prefix)에 있는 모든 파일 리스트를 가져오는 함수
    :param bucket_name: GCS 버킷 이름 (예: 'ib-report-jy')
    :param prefix: 특정 경로 (예: '2024/Mar 11/')
    :return: 파일명 리스트
    """
    client = storage.Client(credentials=credentials)
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)  # 특정 경로의 파일 리스트 가져오기

    file_list = [blob.name for blob in blobs]
    return file_list

# 2️⃣ 버킷 이름과 특정 경로 설정
bucket_name = "investment_bank_pdf_jy"  # 사용자의 GCS 버킷 이름
prefix = "20240312/article/tmp"  # 특정 경로 지정 (폴더처럼 사용 가능)

# 3️⃣ 실행 및 출력
files = list_files_in_gcs(bucket_name, prefix)
print("📂 GCS 내 파일 리스트:")
for file in files:
    print(file)
