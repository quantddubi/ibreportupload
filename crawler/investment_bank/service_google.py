import base64
import json
import os
import zlib
from datetime import datetime
from typing import List, Tuple
import yaml

from google.cloud import storage
from google.oauth2.service_account import Credentials


def hash_string(string_to_hash: str) -> str:
    return str(zlib.crc32(string_to_hash.encode()))

# .env.yaml 파일 로드 함수
def load_env_yaml(yaml_path):
    with open(yaml_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
        for key, value in config.items():
            os.environ[key] = str(value)  # 환경 변수 설정

# .env.yaml 파일 로드
load_env_yaml("configs/.env.yaml")


# 환경 변수 가져오기
encoded_google_secret = os.environ.get("GOOGLE_TRANSLATE_SECRET")

# 원래의 JSON 문자열을 복원
decoded_google_secret = base64.b64decode(encoded_google_secret).decode("utf-8")


# JSON을 Python 딕셔너리로 변환
google_secret_json = json.loads(decoded_google_secret)
credentials = Credentials.from_service_account_info(google_secret_json)
storage_client = storage.Client(credentials=credentials)


def download_blob(bucket_name: str, source_blob_name: str) -> Tuple[str, dict]:
    """Downloads a blob from the bucket."""
    # Google Cloud Storage(GCS) 클라이언트를 사용하여 지정된 버킷(bucket_name)에 접근
    bucket = storage_client.bucket(bucket_name)
    # GCS에서 지정된 파일(source_blob_name)을 가져옴
    blob = bucket.blob(source_blob_name)
    # GCS에서 최신 메타데이터를 가져오고 업데이트
    blob.patch()
    metadata = blob.metadata
    # 로컬 저장 경로 설정
    extension = source_blob_name.split(".")[-1]
    download_path = f"./{hash_string(source_blob_name)}.{extension}"
    # 파일 다운로드
    blob.download_to_filename(download_path)
    return download_path, metadata


def upload_pdf_files(bucket_name: str, upalod_path_metadata: List[dict]) -> Tuple[List[str], List[str]]:
    bucket = storage_client.bucket(bucket_name)
    success = []
    failed = []
    for data in upalod_path_metadata:
        local_path = data["local_path"]
        upload_path = data["upload_path"]
        metadata = data["metadata"]
        try:
            blob = bucket.blob(upload_path)
            blob.metadata = metadata
            blob.upload_from_filename(local_path)
            success.append(local_path)
        except Exception as e:
            print(e, local_path)
            failed.append(local_path)
    return success, failed


def upload_contents_chunks(bucket: str, filename: str, contents_chunks: List[str], metadata: dict) -> str:
    bucket = storage_client.bucket(bucket)
    destination_path = (filename
                        .replace("/article/", "/article_chunks/")
                        .replace(".pdf", ".txt"))
    blob = bucket.blob(destination_path)
    blob.metadata = metadata
    analysis_text = ""
    for i, contents_chunk in enumerate(contents_chunks):
        analysis_text += f"chunk {i}: {contents_chunk}\n\n"
    analysis_text = analysis_text.strip()
    blob.upload_from_string(analysis_text, content_type="text/plain; charset=utf-8")
    return destination_path