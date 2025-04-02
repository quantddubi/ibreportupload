import base64
import json

# 서비스 계정 JSON 파일 읽기
with open("investmentbankreport-d8ec3ecac542.json", "r", encoding="utf-8") as file:
    json_content = file.read()

# Base64로 인코딩
encoded_secret = base64.b64encode(json_content.encode()).decode()

# .env 파일에 저장할 Base64 문자열 출력
print(encoded_secret)
