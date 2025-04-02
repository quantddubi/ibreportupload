from functools import partial
from typing import List

import pdfplumber
import torch
from langchain.text_splitter import RecursiveCharacterTextSplitter
from transformers import AutoImageProcessor
from transformers import AutoModelForObjectDetection

processor = AutoImageProcessor.from_pretrained("microsoft/table-transformer-detection", use_safetensors=True)
model = AutoModelForObjectDetection.from_pretrained("microsoft/table-transformer-detection", use_safetensors=True)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=20,
    length_function=len,
    is_separator_regex=False,
    keep_separator=True,
    separators=["", "", "•", "▶", "\n\n", "\n", " "]
)


def detect_tables(page: pdfplumber.pdf.Page) -> List[List[float]]:
    page_image = page.to_image()
    inputs = processor(images=page_image.original, return_tensors="pt")
    outputs = model(**inputs)
    target_sizes = torch.tensor([page_image.original.size[::-1]])
    results = processor.post_process_object_detection(outputs, threshold=0.9, target_sizes=target_sizes)[0]
    bboxes = []
    for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
        box = [round(i, 2) for i in box.tolist()]
        bboxes.append(box)
    return bboxes


def not_within_bboxes(obj, bboxes):
    """Check if the object is in any of the table's bbox."""

    def obj_in_bbox(_bbox):
        """Define objects in box.

        See https://github.com/jsvine/pdfplumber/blob/stable/pdfplumber/table.py#L404
        """
        v_mid = (obj["top"] + obj["bottom"]) / 2
        h_mid = (obj["x0"] + obj["x1"]) / 2
        x0, top, x1, bottom = _bbox
        return (h_mid >= x0) and (h_mid < x1) and (v_mid >= top) and (v_mid < bottom)

    return not any(obj_in_bbox(__bbox) for __bbox in bboxes)


def filter_tables(page: pdfplumber.pdf.Page, bboxes: List[List[float]]) -> pdfplumber.pdf.Page:
    if bboxes:
        bbox_not_within_bboxes = partial(not_within_bboxes, bboxes=bboxes)
        page = page.filter(bbox_not_within_bboxes)
    return page


def read_pdf_text(pdf_file_path: str) -> str:
    # pdf파일 열기
    pdf = pdfplumber.open(pdf_file_path)
    # 텍스트를 저장할 빈 문자열
    text = ""


    for page in pdf.pages: # PDF의 모든 페이지에 대해 반복
        table_bboxes = detect_tables(page) # 테이블 영역 감지
        page = filter_tables(page, table_bboxes) # 테이블을 제외한 텍스트만 남김
        for c in page.chars: # 페이지 내 모든 문자에 대해 반복
            text += c["text"] # 문자 데이터를 TEXT변수에 추가
    return text


def split_text_into_chunks(text: str) -> List[str]:
    def _preprocess(chunk: str) -> str:
        chunk = chunk.replace("\uf075", "")
        chunk = chunk.replace("\uf02a", "")
        chunk = chunk.replace("\uf0fc", "")
        chunk = chunk.strip()
        return chunk
    chunks = text_splitter.split_text(text)
    chunks = [_preprocess(x) for x in chunks if len(x) > 200]
    return chunks
