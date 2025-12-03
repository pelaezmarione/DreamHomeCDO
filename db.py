import mysql.connector
from config import MAIN_DB, BRANCH_DBS

def get_main_connection():
    return mysql.connector.connect(
        host=MAIN_DB["host"],
        user=MAIN_DB["user"],
        password=MAIN_DB["password"],
        database=MAIN_DB["database"],
        port=MAIN_DB["port"]
    )

def get_branch_connection(branch_key):
    cfg = BRANCH_DBS.get(branch_key)
    return mysql.connector.connect(
        host=cfg["host"],
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        port=cfg["port"]
    )
