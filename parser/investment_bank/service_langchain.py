from typing import List

from langchain.text_splitter import RecursiveCharacterTextSplitter


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=20,
    length_function=len,
    is_separator_regex=False,
    keep_separator=True,
)


def split_text_into_chunks(text: str) -> List[str]:
    chunks = text_splitter.split_text(text)
    chunks = [x for x in chunks if len(x) > 500]
    return chunks
