import os
import shutil
from datetime import datetime
from glob import glob
from typing import List



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


from service_google import upload_pdf_files, download_blob, hash_string
# from service_discord import send_message
import zipfile


###################
# ZIP 파일 압축 해제 #
###################

# Google storage에 있는 zjp파일을 가져와서 extract_to_dir 폴더에서 합축 해제
## download_path, metadata = download_blob(bucket_name, file_name)에서 filepath 인자를 찾음. 즉, google storge에 저장되어있는 zip파일을 가져오는 것임


def unzip_file(filepath: str, extract_to_dir: str):
    # ZIP파일을 읽기 모드 열기
    with zipfile.ZipFile(filepath, 'r') as zip_ref:
        # 모든 파일을 extract_to_dir 폴더에 압축 해제
        zip_ref.extractall(extract_to_dir)
    return filepath

###########################
# 파일 이름을 기반으로 날짜 분석 #
###########################
def parse_datetime(file_name: str) -> datetime:
    file_name_without_prefix = file_name.replace("zipfiles/", "")
    file_name_without_extension = file_name_without_prefix.split('.')[0]
    date_format = "%Y/%b %d"
    date_obj = datetime.strptime(file_name_without_extension, date_format)
    return date_obj

####################
# PDF 파일 목록을 추출 #
####################
# 압축 해제된 폴더에서 모든 PDF 파일을 찾아 리스트로 반환
def parse_pdf_path_list(unzip_dir: str) -> List[str]:
    # 파일 경로 패턴을 검색하는 함수. unzip_dir 안에 있는 모든 파일과 폴더를 재귀적으로 검색. 하위 폴더까지 포함해서 검색
    path_iterator = glob(f"{unzip_dir}/**/*", recursive=True)
    pdf_path_list = []
    # PDF 파일만 필터링
    for path in path_iterator:
        if not path.endswith(".pdf"):
            continue
        pdf_path_list.append(path)
    return pdf_path_list

#########################
# PDF 파일의 메타데이터 생성 #
#########################
# 파일 경로, 출판사 정보, 업로드 경로 등의 메타데이터를 생성
def parse_metadata(pdf_path_list: List[str], published_dt: datetime) -> List[dict]:
    data = []
    for pdf_path in pdf_path_list:
        path_arr = pdf_path.split("/")
        # PDF가 위치한 폴더명을 출처로 간주
        publisher = path_arr[-2]
        pdf_filename = path_arr[-1]
        upload_path = f"{published_dt.strftime('%Y%m%d')}/article/{publisher}/{pdf_filename}"
        metadata = {
            "id": hash_string(pdf_filename),
            "published_at": published_dt,
            "publisher": publisher,
            "filename": pdf_filename
        }
        data.append({
            "local_path": pdf_path,
            "upload_path": upload_path,
            "metadata": metadata
        })
    return data


##########################
# 파일 다운로드 및 업로드 흐름 #
##########################
# GCP 버킷에서 ZIP 파일을 다운로드하고, 압축을 해제한 후, PDF 파일을 업로드
def unzip_and_upload(bucket_name: str, file_name: str):
    # 0. 날짜 파싱
    published_dt = parse_datetime(file_name)

    # 1. zip 파일 다운로드
    download_path, metadata = download_blob(bucket_name, file_name)

    # 2. zip 파일 압축 해제
    unzip_dir = download_path.replace(".zip", "")
    unzip_file(download_path, unzip_dir)

    # 3. list path(pdf파일 별로 경로를 리스트 형식으로 저장)
    pdf_path_list = parse_pdf_path_list(unzip_dir)

    # 4. metadata 설정
    upload_path_metadata = parse_metadata(pdf_path_list, published_dt)
    upload_bucket_name = "ib_report_pdf_v1"
    success, failed = upload_pdf_files(upload_bucket_name, upload_path_metadata)

    # 5. remove downloaded files
    os.remove(download_path)
    shutil.rmtree(unzip_dir)

    # 5. 메세지 전송
    # message = f"[INVESTMENT BANK - UNZIP] {file_name} success: {len(success)} failed: {len(failed)}"
    # print(message)
    # send_message(message)


#######
# 최종 #
#######
def run(data, context):
    file_name = data['name']
    bucket_name = data['bucket']
    if file_name.endswith(".zip"):
        unzip_and_upload(bucket_name, file_name)
    return {"msg": "parse analysis complete"}

#
# if __name__ == "__main__":
#     data = {
#         "name": "2025/Mar 17.zip",
#         "bucket": "ib_report_v1"
#     }
#     run(data)