import os
from dotenv import load_dotenv

load_dotenv()

DBSERVER = os.getenv("DBSERVER")
DBUSER = os.getenv("DBUSER")
DBPWD = os.getenv("DBPWD")
DBHOST = os.getenv("DBHOST")
DBPORT = os.getenv("DBPORT")
DBNAME = os.getenv("DBNAME")
# DBURL = f"{DBSERVER}://{DBUSER}:{DBPWD}@{DBHOST}:{DBPORT}/{DBNAME}"
DBURL = os.getenv("DBURL")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MIN = int(os.getenv("ACCESS_TOKEN_EXPIRE_MIN"))

CLOUD_NAME = os.getenv("CLOUD_NAME")
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
CLOUD_USER_IMG = os.getenv("CLOUD_USER_IMG")
