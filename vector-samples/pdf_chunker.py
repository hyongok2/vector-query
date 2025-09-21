import re
from pathlib import Path
from typing import List, Dict
from pypdf import PdfReader

def read_pdf_text(pdf_path: str) -> List[str]:
    """PDF에서 페이지별 텍스트 추출 (page_texts[page_idx])"""
    reader = PdfReader(pdf_path)
    texts = []
    for page in reader.pages:
        # extract_text()가 None일 수 있어 대비
        t = page.extract_text() or ""
        # 공백 정리
        t = re.sub(r"[ \t]+", " ", t)
        t = re.sub(r"\n{2,}", "\n", t).strip()
        texts.append(t)
    return texts

def split_into_chunks(
    text: str,
    max_chars: int = 800,
    overlap: int = 120,
    min_chars: int = 200
) -> List[str]:
    """
    단락 기준으로 쪼개되, 너무 길면 슬라이딩 윈도우로 더 쪼갬.
    """
    # 1) 우선 큰 단락으로 나누기
    paras = re.split(r"\n{2,}", text)
    chunks: List[str] = []
    for p in paras:
        p = p.strip()
        if not p:
            continue
        if len(p) <= max_chars:
            chunks.append(p)
        else:
            # 2) 너무 길면 슬라이딩 윈도우로 분할
            start = 0
            while start < len(p):
                end = start + max_chars
                piece = p[start:end]
                # 문장 경계에 가깝게 자르기(가벼운 휴리스틱)
                last_punct = max(piece.rfind("."), piece.rfind("。"), piece.rfind("!"), piece.rfind("?"))
                if last_punct > min_chars:
                    piece = piece[:last_punct+1]
                    end = start + len(piece)
                chunks.append(piece.strip())
                start = max(end - overlap, end)  # 음수가 안 되도록
    # 너무 짧은 조각 합치기(인접 조각과 병합)
    merged: List[str] = []
    buf = ""
    for c in chunks:
        if not buf:
            buf = c
        elif len(buf) < min_chars:
            buf = (buf + " " + c).strip()
        else:
            merged.append(buf)
            buf = c
    if buf:
        merged.append(buf)
    return merged

def pdf_to_chunks(pdf_path: str, max_chars=800, overlap=120) -> List[Dict]:
    """
    [{"text": "...", "page": 1, "chunk_index": 0, "source": "<file>"} ...]
    """
    pdf_path = str(pdf_path)
    file_name = Path(pdf_path).name
    page_texts = read_pdf_text(pdf_path)

    out: List[Dict] = []
    for i, page_text in enumerate(page_texts, start=1):
        if not page_text.strip():
            continue
        chunks = split_into_chunks(page_text, max_chars=max_chars, overlap=overlap)
        for j, ch in enumerate(chunks):
            out.append({
                "text": ch,
                "page": i,
                "chunk_index": j,
                "source": file_name,
            })
    return out
