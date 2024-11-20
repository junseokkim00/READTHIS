from dotenv import find_dotenv, load_dotenv
import os
from langchain_openai import OpenAIEmbeddings
from langchain.embeddings import HuggingFaceBgeEmbeddings
from uuid import uuid4

# when testing in local file comment it!
# __import__('pysqlite3')
# import sys
# sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

from langchain_chroma import Chroma
import chromadb.api




def get_embeddings(name="openai", api_key="Your-Api-Key"):
    load_dotenv(find_dotenv())
    if name == "openai":
        # os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
        embeddings = OpenAIEmbeddings(api_key=api_key)
    elif name == "huggingface":
        model_name="BAAI/bge-small-en"
        model_kwargs = {'device': 'cpu'}
        encode_kwargs = {'normalize_embeddings': True}
        embeddings = HuggingFaceBgeEmbeddings(
            model_name=model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs
        )
    else:
        raise Exception(f'{name} is not currently supported as embeddings')
    return embeddings

def load_db(name: str, embeddings):
    persist_directory=f"./db/{name}"
    if os.path.isdir(persist_directory):
        return Chroma(
            collection_name=name,
            embedding_function=embeddings,
            persist_directory=persist_directory,
        )
    else:
        raise Exception(f"db named {name} does not exist.")

def set_db(name: str, embeddings, save_local=True):
    if save_local:
        if not os.path.isdir('./db'):
            os.mkdir('./db')
        chromadb.api.client.SharedSystemClient.clear_system_cache()
        vector_db = Chroma(
            collection_name=name,
            embedding_function=embeddings,
            persist_directory=f"./db/{name}"
        )
        return vector_db
    else:
        vector_db = Chroma(
            collection_name=name,
            embedding_function=embeddings,
        )
        return vector_db

def add_documents(db, documents):
    uuids = [str(uuid4()) for _ in range(len(documents))]
    print("uuids ready")
    db.add_documents(documents=documents, ids=uuids)
    return db