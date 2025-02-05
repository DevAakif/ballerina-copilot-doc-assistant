import base64
import requests
import logging
import re
import os
from dotenv import load_dotenv
from langchain.text_splitter import MarkdownHeaderTextSplitter
from linkUpdater import get_doc_link
from updater import db_queries

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
headers_to_split_on = [
    ("#", "Header1"),
    ("##", "Header2")
]
markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
web_path = "https://ballerina.io/learn/"
path = "ballerina-learn-pages"


def text_to_anchor(text):
    anchor = text.lower()
    anchor = anchor.replace(" ", "-")
    anchor = re.sub("[^0-9a-zA-Z-]", "", anchor)
    anchor = "#" + anchor
    return anchor

def chunk_docs(filename, file_content):
    chunks = []
    chunked_doc = markdown_splitter.split_text(file_content)
    for chunk in chunked_doc:
        suffix = ""
        if "Header3" in chunk.metadata.keys():
            suffix = text_to_anchor(chunk.metadata["Header3"])
        elif "Header2" in chunk.metadata.keys():
            suffix = text_to_anchor(chunk.metadata["Header2"])
        #file_name = file[0].replace("ballerina-learn-pages", "")
        chunk.metadata["filename"] = filename

        if "Header2" in chunk.metadata:
            chunk.metadata["doc_link"] = get_doc_link(filename, chunk.metadata["Header2"])
        else:
            chunk.metadata["doc_link"] = get_doc_link(filename)

        chunk.page_content = chunk.page_content.replace("../../", f"{web_path}")
        chunk.page_content = chunk.page_content.replace("../", f"{web_path}")
        chunk.page_content = chunk.page_content.replace(".md", "")
        chunk.page_content = chunk.page_content.replace("{.cInlineImage-full}", "")
        header1_text = '#' + chunk.metadata["Header1"] if 'Header1' in chunk.metadata.keys() else ''
        header2_text = '\n##' + chunk.metadata["Header2"] if 'Header2' in chunk.metadata.keys() else ''
        header3_text = '\n###' + chunk.metadata["Header3"] if 'Header3' in chunk.metadata.keys() else ''
        content_text = '\n' + chunk.page_content
        chunk.page_content = f"{header1_text}{header2_text}{header3_text}{content_text}"
    chunks += chunked_doc
    #vector_store.add_documents(chunked_doc)
    return chunks


def retrieve_content(filename,repo):
    url = f"https://api.github.com/repos/{repo}/contents/{filename}?ref=master"
    headers = {"Authorization": f'token {os.getenv("GITHUB_TOKEN")}',
               "Accept": 'application/vnd.github.v3.raw'}
    response = requests.get(url, headers=headers, timeout=(10, 60))
    response.raise_for_status()
    if 'base64' in response.headers.get('Content-Encoding', ''):
        try:
            return base64.b64decode(response.content).decode('utf-8')
        except UnicodeDecodeError:
            logger.warning(f"UnicodeDecodeError occurred while decoding {response.content}")
            return ""
    return response.text


def delete_records(filename):
    primary_keys = []
    filtered_records = db_queries.get_primary_key(filename)
    print("deletion pk: ", filtered_records)
    print("deletion filename: ", filename)

    # In this line the query to delete the records with the above ids should be deleted - DONE
    for key in filtered_records:
        print("key:", key)
        #db_queries.delete_record(key)

    return f"Successfully deleted {len(filtered_records)} records of {filename}"

def add_records(filename, repo):
    file_content = retrieve_content(filename, repo)
    chunked_docs = chunk_docs(filename, file_content)
    return f"Successfully added {len(chunked_docs)} records from {filename}"


def get_latest_commit(repo, directory):
    url = f"https://api.github.com/repos/{repo}/commits?path={directory}/&&sha=master"
    headers = {"Authorization": f'token {os.getenv("GITHUB_TOKEN")}',
               "Accept": 'application/vnd.github.v3+json'}
    response = requests.get(url, headers=headers, timeout=(10, 30))
    response.raise_for_status()
    return response.json()[0]["sha"]


def load_md_files_from_repo():
    url = f"https://api.github.com/repos/ballerina-platform/ballerina-dev-website/git/trees/master?recursive=1"
    headers = {"Authorization": f'token {os.getenv("GITHUB_TOKEN")}',
               "Accept": 'application/vnd.github.v3+json'}
    response = requests.get(url, headers=headers, timeout=(10,60))
    response.raise_for_status()
    filenames = [item["path"] for item in response.json().get("tree", [])
                      if item["path"].endswith(".md") and "swan-lake/" in item["path"]]

    return filenames


def get_chunked_docs(filenames):
    chunked_docs = []
    for filename in filenames:
        content = retrieve_content(filename, "ballerina-platform/ballerina-dev-website")
        chunks = chunk_docs(filename, content)
        chunked_docs.extend(chunks)

    return chunked_docs


def compare_commits(base_sha, head_sha, repo):
    url = f"https://api.github.com/repos/{repo}/compare/{base_sha}...{head_sha}"
    headers = {"Authorization": f'token {os.getenv("GITHUB_TOKEN")}',
               "Accept": 'application/vnd.github.v3+json'}
    response = requests.get(url, headers=headers, timeout=(10, 30))
    response.raise_for_status()
    return list(response.json()['files'])


def get_diff(files):
    added = []
    deleted = []
    for file in files:
        if file['status'] in ['added', 'modified']:
            added.append(file['filename'])
        elif file['status'] == 'removed':
            deleted.append(file['filename'])
    return added, deleted

def process_learn_changes(added, deleted, repo):
    for file in added:
        msg = delete_records(file)
        logger.info(msg)
        msg = add_records(file, repo)
        logger.info(msg)
    for file in deleted:
        msg = delete_records(file)
        logger.info(msg)



# The below functions belong to the BBE pipeline

def load_files_from_bbe_repo():
    url = f"https://api.github.com/repos/ballerina-platform/ballerina-distribution/git/trees/master?recursive=1"
    headers = {"Authorization": f'token {os.getenv("GITHUB_TOKEN")}',
               "Accept": 'application/vnd.github.v3+json'}
    response = requests.get(url, headers=headers, timeout=(10,60))
    response.raise_for_status()
    filenames = [item["path"] for item in response.json().get("tree", []) if item["path"].startswith('examples') and item['type'] == 'blob']

    grouped_files = {}

    for file in filenames:
        parts = file.split("/")
        if len(parts) > 1:
            subfolder = parts[1]
            if subfolder not in grouped_files:
                grouped_files[subfolder] = []
            grouped_files[subfolder].append(file)
    return list(grouped_files.values())


def get_chunked_bbe_docs(filenames):
    chunked_docs = []
    md_filename = None
    for files in filenames:
        content = retrieve_bbe_content(files)
        if content is None:
            continue

        for file in files:
            if file.endswith('.md'):
                md_filename = file
                break
        chunks = chunk_docs(md_filename,content)
        chunked_docs.extend(chunks)
    return chunked_docs


def retrieve_bbe_content(files):
    md_file = next((file for file in files if file.endswith(".md")), None)
    if md_file is not None:
        md_file_content = retrieve_content(md_file, 'ballerina-platform/ballerina-distribution')
        placeholders = re.findall(r'::: (code|out) (.+?) :::', md_file_content)

        for placeholder_type, file_name in placeholders:
            file_path = next((file for file in files if file.endswith(file_name)),None)

            if file_path is None:
                continue

            file_content = retrieve_content(file_path, 'ballerina-platform/ballerina-distribution')

            if file_path.endswith('.bal'):
                code_block = f'```ballerina\n{file_content}\n```'
            else:
                code_block = f'```\n{file_content}\n```'

            md_file_content = md_file_content.replace(f'::: {placeholder_type} {file_name} :::', code_block)

        if len(md_file_content) > 0:
            return md_file_content



def process_bbe_changes(commit_files):
    directories, grouped_files = get_changed_bbe_directories(commit_files)
    deleted_files = remove_bbe_delete_files(directories, commit_files, grouped_files)
    added_files = add_bbe_files(directories)

    return added_files, deleted_files

def get_changed_bbe_directories(commit_files):
    filtered_commit_files = [file['filename'] for file in commit_files if
                             ((file['filename']).split('/'))[0] == 'examples']

    grouped_files = {}

    for file in filtered_commit_files:
        parts = file.split("/")
        if len(parts) > 1:
            subfolder = parts[1]
            if subfolder not in grouped_files:
                grouped_files[subfolder] = []
            grouped_files[subfolder].append(file)

    directories = [key for key in grouped_files.keys() if '.' not in key]
    return directories, grouped_files


def remove_bbe_delete_files(directories, commit_files, grouped_files):
    delete_files = []

    for key in directories:
        files = grouped_files[key]
        for file in files:
            if file.endswith('.md'):
                for commit in commit_files:
                    if commit['filename'] == file and commit['status'] == 'removed':
                        delete_files.append(file)
                        directories.pop(key)

    for file in delete_files:
        delete_records(file)

    return delete_files


def add_bbe_files(directories):
    chunks = []
    added_files = []
    for key in directories:
        url = f"https://api.github.com/repos/ballerina-platform/ballerina-distribution/git/trees/master?recursive=1"
        headers = {"Authorization": f'token {os.getenv("GITHUB_TOKEN")}',
                   "Accept": 'application/vnd.github.v3+json'}
        response = requests.get(url, headers=headers, timeout=(10, 60))
        response.raise_for_status()
        filenames = [item["path"] for item in response.json().get("tree", []) if item["path"].startswith(f'examples/{key}') and item['type'] == 'blob']

        content = retrieve_bbe_content(filenames)

        if content is not None:
            md_filename = None

            for file in filenames:
                if file.endswith('.md'):
                    md_filename = file
                    break
            delete_records(md_filename)
            chunked_docs = chunk_docs(md_filename, content)
            chunks.extend(chunked_docs)
            added_files.append(md_filename)

    return added_files