## 가상 환경 생성
  - 환경별 버전 매핑이 중요함.
py -3.11 -m venv .venv311
. .\.venv311\Scripts\Activate.ps1
python -V

## 가상 환경 실행 명령어

. .\.venv311\Scripts\Activate.ps1

## 평가용 주요 명령어

python .\index_pdf_to_qdrant.py .\pdf-sample.pdf

python .\query_pdf.py pdf__pdf-sample.pdf "MCP는 AI Agent에게 유용한 기능을 제공한다." "pdf-sample.pdf"