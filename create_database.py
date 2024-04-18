from langchain_community.document_loaders import S3DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores.chroma import Chroma
import os
import shutil
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
S3_bucket = os.getenv("S3_BUCKET_NAME")


def load_documents(prefix):
    try:
        loader = S3DirectoryLoader(S3_bucket, prefix=prefix)
        documents = loader.load()
        return documents
    except Exception as e:
        print("Unable to load documents.", e)
        return []


def split_text(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=10000,
        chunk_overlap=100,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)

    return chunks


def save_to_chroma(chunks: list[Document], prefix):
    chroma_path = f"chroma/{prefix}"
    # Clear out the database first.
    if os.path.exists(chroma_path):
        shutil.rmtree(chroma_path)

    # Create a new DB from the documents.
    db = Chroma.from_documents(
        chunks, OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY), persist_directory=chroma_path
    )
    db.persist()


def generate_data_store(prefix):

    try:
        documents = load_documents(prefix)
        chunks = split_text(documents)
        save_to_chroma(chunks, prefix)
        return True
    except Exception as e:
        print("Unable to generate the data store.", e)
        return False


generate_data_store("safety/")
