import base64
import json
import os
import zlib
from datetime import datetime
from typing import List, Tuple

from google.cloud import storage
from google.oauth2.service_account import Credentials


import os


###############
# 환경 변수 로드 #
###############
import yaml
import os

# .env.yaml 파일 로드 함수
def load_env_yaml(yaml_path):
    with open(yaml_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
        for key, value in config.items():
            os.environ[key] = str(value)  # 환경 변수로 설정

# .env.yaml 파일 로드
load_env_yaml("configs/.env.yaml")

def hash_string(string_to_hash: str) -> str:
    return str(zlib.crc32(string_to_hash.encode()))

encoded_google_secret = os.environ.get("GOOGLE_TRANSLATE_SECRET")
decoded_google_secret = base64.b64decode(encoded_google_secret).decode("utf-8")
google_secret_json = json.loads(decoded_google_secret)

credentials = Credentials.from_service_account_info(google_secret_json)
storage_client = storage.Client(credentials=credentials)


def download_blob(bucket_name: str, source_blob_name: str) -> Tuple[str, dict]:
    """Downloads a blob from the bucket."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.patch()
    metadata = blob.metadata
    if not metadata:
        metadata = {}
    metadata["id"] = hash_string(source_blob_name)
    extension = source_blob_name.split(".")[-1]
    download_path = f"./tmp/{hash_string(source_blob_name)}.{extension}"
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
    bucket = storage_client.bucket(bucket) # GCS에서 해당 버킷을 가져옴
    # 원본 PDF와 동일한 디렉터리 구조를 유지하면서 텍스트 파일로 변환
    destination_path = (filename
                        .replace("/article/", "/article_chunks/")
                        .replace(".pdf", ".txt"))
    blob = bucket.blob(destination_path) # GCS에서 해당 파일(blob)을 가져옴
    blob.metadata = metadata # GCS에 업로드할 파일(blob)에 추가적인 정보를 저장
    analysis_text = "" # 업로드할 텍스트를 저장할 변수 초기화
    # 텍스트 청크를 하나의 문자열로 변환
    for i, contents_chunk in enumerate(contents_chunks):
        analysis_text += f"chunk {i}: {contents_chunk}\n\n"
    analysis_text = analysis_text.strip()
    # GCS에 텍스트 파일 업로드
    blob.upload_from_string(analysis_text, content_type="text/plain; charset=utf-8")
    return destination_path
