import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# GOOGLE
GOOGLE_TRANSLATE_SECRET = os.getenv("GOOGLE_TRANSLATE_SECRET")

# Pinecone API Key 및 환경
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

