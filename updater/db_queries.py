import psycopg2
from langchain.smith.evaluation.runner_utils import logger
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(database=os.getenv("DATABASE"), user=os.getenv("USER"), password=os.getenv("PASSWORD"), host=os.getenv("HOST"), port=os.getenv("PORT"))
cursor = conn.cursor()

def has_collection(collection_name):
    cursor.execute("SELECT name FROM langchain_pg_collection")
    collection = cursor.fetchall()
    collection_names = [row[0] for row in collection]
    if collection_name in collection_names:
        return True
    else:
        return False

def get_commit_update():
    cursor.execute("SELECT last_commit, last_bbe_commit, final_version FROM updates")
    update = cursor.fetchall()
    return {"last_learn_commit":update[0][0],"last_bbe_commit":update[0][1], "version":update[0][2]}

def get_primary_key(filename):
    collection_id = os.getenv("COLLECTION_ID")
    query = f"SELECT id FROM langchain_pg_embedding WHERE collection_id = '{collection_id}' AND cmetadata->>'filename' = %s"
    cursor.execute(query, (filename,))
    ids = cursor.fetchall()
    id_list = [id[0] for id in ids]
    print("id_list: ", id_list)
    return id_list

def drop_collection():
    collection_id = os.getenv("COLLECTION_ID")
    cursor.execute(f"DELETE FROM langchain_pg_embedding WHERE collection_id = '{collection_id}'")
    conn.commit()


def delete_record(id):
    query = f"DELETE from langchain_pg_embedding WHERE id = '{id}'"
    cursor.execute(query)
    conn.commit()
    logger.info(f"deleted record of id {id}")

def update_final_version():
    query = "UPDATE updates SET final_version = final_version + 1  WHERE id = 1"
    cursor.execute(query)
    conn.commit()
    logger.info("Updated version")


def update_final_commits(latest_learn_commit, latest_bbe_commit):
    query = f"UPDATE updates SET last_commit = '{latest_learn_commit}', last_bbe_commit = '{latest_bbe_commit}' WHERE id = 1"
    cursor.execute(query)
    conn.commit()
    logger.info("Latest commits updated")

