import os

DB_DIR = os.environ.get("DB_DIR", "/home/data")
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", os.path.join(DB_DIR, "comprobantes"))

os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

BINGO_DB_PATH = os.path.join(DB_DIR, "bingo.db")
BINGO2_DB_PATH = os.path.join(DB_DIR, "bingo2.db")
