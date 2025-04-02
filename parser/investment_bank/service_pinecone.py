import os
from typing import List

from pinecone import Pinecone
from pinecone import UpsertResponse


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

pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
index = pc.Index('ibbank-test2')


def paginated_upsert(vectors: List[dict], namespace: str, page_size: int = 5) -> List[UpsertResponse]:
    results = []
    for i in range(0, len(vectors), page_size):
        paginated_vectors = vectors[i:i+page_size]
        response = index.upsert(
            vectors=paginated_vectors,
            namespace=namespace
        )
        results.append(response)
    return results


def index_vectors(
        contents_chunks: List[str],
        embeddings: List[List[float]],
        metadata: dict,
) -> List[UpsertResponse]:
    vectors = []
    for i in range(len(embeddings)):
        cur_key = f"{metadata['id']}_{i}"
        cur_metadata = metadata.copy()
        cur_metadata["content"] = contents_chunks[i]
        vectors.append({
            "id": cur_key,
            "values": embeddings[i],
            "metadata": cur_metadata
        })
    result = paginated_upsert(vectors, namespace="investment_bank_v2")
    return result
