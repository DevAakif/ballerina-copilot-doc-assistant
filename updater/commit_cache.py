import logging
import time
from updater import db_queries


logger = logging.getLogger(__name__)

def retrieve_last_updated_commit():
    retries = 3
    sleep = 1
    attempt = 0
    while attempt < retries:
        try:
            cached_commit = db_queries.get_commit_update()
            if cached_commit:
                return cached_commit
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed with error: {e}")
            sleep = sleep * 2
            time.sleep(sleep)
            attempt += 1
        logger.error(f"All {retries} retries failed for querying update table")
        return None

