import os
from datetime import datetime
from glob import glob
from typing import List

import zipfile
from service_pinecone import index_vectors
from service_discord import send_message
from service_google import download_blob, upload_contents_chunks
from service_pdf import read_pdf_text, split_text_into_chunks
from service_openai import paginated_get_embedding


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

def parse_datetime(file_name: str) -> datetime:
    file_name_without_prefix = file_name.replace("zipfiles/", "")
    file_name_without_extension = file_name_without_prefix.split('.')[0]
    date_format = "%Y/%b %d"
    date_obj = datetime.strptime(file_name_without_extension, date_format)
    return date_obj


def parse_pdf_path_list(unzip_dir: str) -> List[str]:
    path_iterator = glob(f"{unzip_dir}/**/*", recursive=True)
    pdf_path_list = []
    for path in path_iterator:
        if not path.endswith(".pdf"):
            continue
        pdf_path_list.append(path)
    return pdf_path_list


def parse_metadata(pdf_path_list: List[str], published_dt: datetime) -> List[dict]:
    data = []
    for pdf_path in pdf_path_list:
        path_arr = pdf_path.split("/")
        publiser = path_arr[-2]
        pdf_filename = path_arr[-1]
        upload_path = f"{published_dt.strftime('%Y%m%d')}/article/{publiser}/{pdf_filename}"
        metadata = {
            "published_at": published_dt,
            "publisher": publiser,
            "filename": pdf_filename
        }
        data.append({
            "local_path": pdf_path,
            "upload_path": upload_path,
            "metadata": metadata
        })
    return data


def index_report(bucket_name: str, file_name: str) -> str:
    # 1. pdf 파일 다운로드
    download_path, metadata = download_blob(bucket_name, file_name)

    # 2. pdf 텍스트 추출
    pdf_text = read_pdf_text(download_path)
    pdf_text_chunks = split_text_into_chunks(pdf_text)

    # 3. 추출된 텍스트 업로드
    chunk_url = upload_contents_chunks(bucket_name, file_name, pdf_text_chunks, metadata)
    url_prefix = "https://storage.googleapis.com"
    metadata["chunk_url"] = f"{url_prefix}/{bucket_name}/{chunk_url}"
    metadata["public_url"] = f"{url_prefix}/{bucket_name}/{file_name}"

    # 4. 임베딩 추출
    embeddings = paginated_get_embedding(pdf_text_chunks)

    # 5. 추출한 임베딩 메타데이터와 함께 저장하기
    response = index_vectors(pdf_text_chunks, embeddings, metadata)

    # 6. 메세지 전송
    message = f"[INVESTMENT BANK - INDEX] {metadata['id']} {file_name} {response}"
    print(message)
    #send_message(message)

    # 7. 다운로드 파일 삭제
    os.remove(download_path)


def run(data, context):
    file_name = data['name']
    bucket_name = data['bucket']
    if file_name.endswith(".pdf"):
        index_report(bucket_name, file_name)
    return {"msg": "parse analysis complete"}

#
# if __name__ == '__main__':
#     filename = "20250318/article/JPM/mi-weekly-market-brief-en.pdf"
#     data = {
#         "name": filename,
#         "bucket": "ib_report_pdf_v1"
#     }
#     run(data, None)
