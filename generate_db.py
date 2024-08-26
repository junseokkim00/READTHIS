from utils.web_utils import fetch_title_and_abstract
from utils.db_utils import set_db, add_documents
from langchain_openai import OpenAIEmbeddings
import os
from dotenv import find_dotenv, load_dotenv

if __name__ == '__main__':
    event=input("Enter event name: ")
    year=input("Enter year: ")
    paper_type = input("Enter paper_type: ")

    print(f"Fetching paper for the following...\nevent:{event}\nyear:{year}\npaper_type:{paper_type}\n")
    Documents = fetch_title_and_abstract(event=event,
                                         year=year,
                                         paper_type=paper_type
                                        )
    print(f"Fetching paper done (length: {len(Documents)})")
    # set embeddings
    load_dotenv(find_dotenv())
    os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
    embeddings = OpenAIEmbeddings()
    db = set_db(name=f"{year}{event}-{paper_type}",
                embeddings=embeddings)
    print("Adding Document...")
    db = add_documents(db, documents=Documents)
    print("Adding Document DONE")
    print(f"{year}{event}-{paper_type} db generated!")