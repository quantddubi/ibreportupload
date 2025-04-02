import os
from typing import List

from openai import OpenAI

openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def get_embedding(text: str) -> List[float]:
    response = openai_client.embeddings.create(
        input=[text],
        model="text-embedding-3-large",
        dimensions=1024
    )
    return response.data[0].embedding


def get_batch_embedding(text_list: List[str]) -> List[List[float]]:
    # OpenAI API를 사용하여 임베딩 벡터 생성
    response = openai_client.embeddings.create(
        input=text_list,
        model="text-embedding-3-large",
        dimensions=1024
    )
    return [x.embedding for x in response.data]


def paginated_get_embedding(text_list: List[str], page_size=5) -> List[List[float]]:
    result = [] # 결과 저장을 위한 빈 리스트 초기화
    for i in range(0, len(text_list), page_size):
        queries = text_list[i:i+page_size]
        embedding_result = get_batch_embedding(queries)
        result.extend(embedding_result)
    return result


def generate_image_caption(image_url: str, image_alt: str) -> str:
    if image_url.split(".")[-1] not in ["jpg", "jpeg", "png", "webp", "gif"]:
        return ""
    prompt = f"""
Analyze the attached image of a financial table and provide a concise summary or caption in 50 words.
Focus on key financial figures, trends, and any significant data points.
alt: {image_alt}
""".strip()
    response = openai_client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": image_url}
                ]
            }
        ],
        max_tokens=100,
    )
    generated_text = response.choices[0].message.content
    return f"[IMAGE CAPTION]: {generated_text}"
