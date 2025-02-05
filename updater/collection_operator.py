import logging

from dotenv import load_dotenv

from updater import utils
from updater import db_queries
from updater import commit_cache
import os
from langchain_openai import AzureOpenAIEmbeddings
from langchain_postgres import PGVector


load_dotenv()

embedding = AzureOpenAIEmbeddings(
    model="text-embedding-3-small",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    openai_api_version="2023-07-01-preview",
    deployment=os.getenv("AZURE_DEPLOYMENT")
)

vector_store = PGVector(
    embeddings= embedding,
    connection=os.getenv("CONNECTION_STRING"),
    collection_name=os.getenv("COLLECTION")
)


logger = logging.getLogger(__name__)

def insert_collection():
    filenames = utils.load_md_files_from_repo()
    bbe_filenames = utils.load_files_from_bbe_repo()

    db_queries.drop_collection()
    print("entering insert collection")
    docs = utils.get_chunked_docs(filenames)
    bbe_docs = utils.get_chunked_bbe_docs(bbe_filenames)
    print(f"{len(docs) + len(bbe_docs)} chunks added to collection")
    db_queries.update_final_version()


def update_collection(latest_learn_commit, latest_bbe_commit):
    cache_history = commit_cache.retrieve_last_updated_commit()
    has_updater_field = False
    updater_version = "2.0"
    def check_drop_collection():
        # There are 2 more conditions to be included here
        if cache_history is None:
            logger.info("Replaced the whole collection since the last commit was missing")
            return True
        if str(cache_history['version']) != updater_version:
            logger.info("Dropping and inserting the docs collection")
            return True

    if check_drop_collection():
        insert_collection()
        db_queries.update_final_commits(latest_learn_commit, latest_bbe_commit)
    else:
        commit_learn_files = utils.compare_commits(cache_history['last_learn_commit'], latest_learn_commit, 'ballerina-platform/ballerina-dev-website')
        filtered_commit_learn_files = [file for file in commit_learn_files if ((file['filename']).split('/'))[0] == 'swan-lake' and ((file['filename']).split('/'))[-1].endswith('.md')]
        added, deleted = utils.get_diff(filtered_commit_learn_files)
        utils.process_learn_changes(added, deleted, "ballerina-platform/ballerina-dev-website")

        commit_bbe_files = utils.compare_commits(cache_history['last_bbe_commit'], latest_bbe_commit, 'ballerina-platform/ballerina-distribution')
        added_bbe_files, deleted_bbe_files = utils.process_bbe_changes(commit_bbe_files)

        db_queries.update_final_commits(latest_learn_commit, latest_bbe_commit)
        print(f"added: {added}, deleted: {deleted} in learn pages")
        print(f"added: {added_bbe_files}, deleted: {deleted_bbe_files} in ballerina by examples")


def update_docs_db():
    logger.info('start the scheduler task')
    has = db_queries.has_collection("learn-pages")
    latest_learn_commit = utils.get_latest_commit('ballerina-platform/ballerina-dev-website','swan-lake')
    latest_bbe_commit = utils.get_latest_commit('ballerina-platform/ballerina-distribution', 'examples')
    if has:
        logger.info(f"Updating the collection learn-pages")
        update_collection(latest_learn_commit, latest_bbe_commit)
        print("doc update ended")
    else:
        logger.info(f"Inserting collection")
        insert_collection()

    logger.info("Schedular task ended")
