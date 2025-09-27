py -3.11 -m venv .venv311

. .\.venv311\Scripts\Activate.ps1

python -m pip install --upgrade pip

pip install streamlit sqlalchemy pandas numpy jinja2 qdrant-client sentence-transformers

pip install oracledb
pip install psycopg2-binary
pip install pymysql
pip install pyodbc (OS에 ODBC 드라이버 필요)