from sqlalchemy import create_engine
import os

DB_USER = os.getenv('DB_USER', "root")
DB_PASS = os.getenv('DB_PASS', "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "PortManager")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo = True, future = True)


