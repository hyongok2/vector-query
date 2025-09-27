 py -3.11 -m venv .venv311

  . .\.venv311\Scripts\Activate.ps1

  python -m pip install --upgrade pip

  pip install streamlit sqlalchemy pandas numpy jinja2 qdrant-client sentence-transformers
