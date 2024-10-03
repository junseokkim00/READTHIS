from fastapi import FastAPI
from utils.db_utils import set_db, get_embeddings, add_documents
from utils.semantic_scholar_utils import get_cited_papers, recommend_paper, get_citations
from utils.LLM_utils import set_model, query_rewrite, judge_paper
from langchain_community.document_loaders import ArxivLoader
from utils.arxiv_utils import load_paper_arxiv_api, retrieve_paper, load_paper_arxiv_title
from utils.web_utils import duckduckgoSearch
from utils.zotero_utils import Zotero
from collections import defaultdict
import time
import os
import shutil
from pydantic import BaseModel, Field


# instance for POST METHOD
app = FastAPI()

if not os.path.isdir('./db'):
    os.mkdir('./db')


class nextPaperParams(BaseModel):
    query: str
    arxiv_number: str


class nextCollectionPaperParams(BaseModel):
    library_id: str
    library_type: str  # 'user' or 'group
    zotero_api_key: str
    collection_name: str
    query: str


@app.get("/")
def hi():
    return {
        "Hello!": "CITE4"
    }


@app.post("/whatsNext/")
def next_paper(params: nextPaperParams):
    query = params.query
    arxiv_number = params.arxiv_number
    print(f"query: {query}")
    print(f"arxiv_number: {arxiv_number}")
    print(f"Searching paper of arxiv number {arxiv_number}...")
    metadata = load_paper_arxiv_api(arxiv_id=arxiv_number)
    title = metadata.title
    categories = metadata.categories
    print(f"title: {title}")
    print(f"categories: {categories}")
    print("retrieving paper")
    time.sleep(1)
    embeddings = get_embeddings()
    if os.path.isdir(f'./db/{arxiv_number}'):
        shutil.rmtree(f'./db/{arxiv_number}')
    db = set_db(
        name=arxiv_number,
        embeddings=embeddings,
        save_local=True
    )
    documents, cnt = get_cited_papers(arxiv_number)
    time.sleep(2.05)
    citations, cite_cnt = get_citations(arxiv_number)
    time.sleep(2.05)
    searchOutput = duckduckgoSearch(query=query)
    db = add_documents(db=db,
                       documents=documents)
    db = add_documents(db=db,
                       documents=citations)
    db = add_documents(
        db=db,
        documents=searchOutput
    )
    print("add documents COMPLETE")
    result = db.similarity_search_with_score(query=query, k=10)
    response = []
    for doc in result:
        abstract, title = doc[0].page_content, doc[0].metadata['title']
        inst = {
            'title': title,
            'abstract': abstract,
            'insights': None,
            'link': doc[0].metadata['url'],
            'score': doc[1],
            'type': doc[0].metadata['type']
        }
        response.append(inst)
    return response


@app.post("/DailyPaper/")
def next_collection_paper(params: nextCollectionPaperParams):
    library_id = params.library_id
    library_type = params.library_type
    zotero_api_key = params.zotero_api_key
    collection_name = params.collection_name
    query = params.query
    zot = Zotero(
        library_id=library_id,
        library_type=library_type,
        api_key=zotero_api_key
    )
    collection_dict = zot.retrieve_collection()
    collection_names = [name for name in collection_dict]
    print(f"collections: {collection_names}")
    db_name = collection_name.replace(" ", "_")
    if os.path.isdir(f"./db/{db_name}"):
        shutil.rmtree(f"./db/{db_name}")
    key = collection_dict[collection_name]
    paper = zot.retrieve_collection_papers(key=key)
    arxivIds = []
    titles = []
    for title, DOI in paper:
        metadata = load_paper_arxiv_title(paper_name=title)
        arxivId = metadata.entry_id.split('/')[-1]
        if 'v' in arxivId:
            arxivId = arxivId.split('v')[0]
        arxivIds.append((title, arxivId))
        titles.append(title)
    
    total_paper_db= []
    title_set= set()
    for title, arxivId in arxivIds:
        time.sleep(2.05)
        citations, cite_cnt = get_citations(arxiv_id=arxivId)
        for citation in citations:
            if citation.metadata['title'] not in title_set and citation.metadata['title'] not in titles:
                title_set.add(citation.metadata['title'])
                total_paper_db.append(citation)
    
    for title, arxivId in arxivIds:
        time.sleep(2.05)
        cited_papers, cited_cnt = get_cited_papers(arxiv_id=arxivId)
        for cited_paper in cited_papers:
            if cited_paper.metadata['title'] not in title_set and cited_paper.metadata['title'] not in titles:
                title_set.add(cited_paper.metadata['title'])
                total_paper_db.append(cited_paper)

    searchOutput = duckduckgoSearch(query=query)
    for doc in searchOutput:
        if doc.metadata['title'] not in title_set and doc.metadata['title'] not in titles:
            title_set.add(doc.metadata['title'])
            total_paper_db.append(doc)
    embeddings = get_embeddings()
    db = set_db(
        name=db_name,
        embeddings=embeddings,
        save_local=True
    )
    db = add_documents(
        db=db,
        documents=total_paper_db
    )
    result = db.similarity_search_with_score(query, k=10)
    response = []
    for doc in result:
        abstract, title = doc[0].page_content, doc[0].metadata['title']
        inst = {
            'title': title,
            'abstract': abstract,
            'insights': None,
            'link': doc[0].metadata['url'],
            'score': doc[1],
            'type': doc[0].metadata['type']
        }
        response.append(inst)
    return response

