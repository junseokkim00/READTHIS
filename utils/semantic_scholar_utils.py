import requests
import os
from dotenv import find_dotenv, load_dotenv
from langchain_core.documents import Document
BASE_URL = "https://api.semanticscholar.org"
academic_graph_url = BASE_URL+"/graph/v1"
recommendation_url = BASE_URL + "/recommendations/v1"


def search_query(query: str):
    load_dotenv(find_dotenv())
    api_key = os.getenv('SEMANTIC_SCHOLAR_API_KEY')
    query_search = academic_graph_url + "/paper/search"
    query_params = {
        'query': query, 'fields': 'title,abstract,authors,year,url,citationStyles', 'fieldsOfStudy': "Computer Science,Engineering" ,'limit': 100}
    headers = {'x-api-key': api_key}

    response = requests.get(query_search, params=query_params, headers=headers)
    if response.status_code == 200:
        response_data = response.json()
    else:
        print(
            f"Request failed with status code {response.status_code}: {response.text}")

    papers = []
    topic = set()
    cnt = 0
    for inst in response_data['data']:
        print(f"title: {inst['title']}")
        if inst['abstract'] is not None and inst['title'] not in topic and inst['citationStyles']['bibtex'] is not None and inst['year'] is not None and inst['url'] is not None:
            topic.add(inst['title'])
            papers.append(Document(
                page_content=inst['abstract'],
                metadata={
                    'title': inst['title'],
                    'year': inst['year'],
                    'url': inst['url'],
                    'bibtex': inst['citationStyles']['bibtex']
                },
                id=cnt
            ))
            cnt += 1
    return papers, cnt

    # TODO search paper


def get_cited_papers(arxiv_id: str):
    load_dotenv(find_dotenv())
    citations = academic_graph_url + f"/paper/ARXIV:{arxiv_id}/citations"
    params = {'limit': 1000, 'fields': 'title,abstract,year,isInfluential,url'}
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    headers = {'x-api-key': api_key}
    response = requests.get(citations, params=params, headers=headers)

    if response.status_code == 200:
        response_data = response.json()
    else:
        raise Exception(
            f"Request failed with status code {response.status_code}: {response.text}")

    # filtering data
    influential_papers = []
    topic = set()
    cnt = 0
    for inst in response_data['data']:
        if inst['isInfluential'] and inst['citingPaper']['abstract'] is not None and inst['citingPaper']['title'] not in topic:
            cnt += 1
            topic.add(inst['citingPaper']['title'])
            influential_papers.append(Document(
                page_content=inst['citingPaper']['abstract'],
                metadata={'title': inst['citingPaper']['title'],
                          'year': inst['citingPaper']['year'],
                          'url': inst['citingPaper']['url']},
                id=cnt
            ))
            # TODO should Document id be unique?
    return influential_papers, cnt


def convert_to_paper_id(paper_title: str):
    load_dotenv(find_dotenv())
    title_search = academic_graph_url + '/paper/search/match'
    params = {'query': paper_title, 'fields': 'title,paperId'}
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    headers = {'x-api-key': api_key}
    response = requests.get(title_search, params=params, headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(data)
        return data['data'][0]['paperId']
    else:
        raise Exception(
            f"Request failed with status code {response.status_code}")
    

def get_embeddings(papers: list, batch_size=16):
    """
    papers parameter format
    keys
    - paper_id (str)
    - title (str)
    - abstract (str)
    """
    embeddings_by_paper_id = {}
    URL = "https://model-apis.semanticscholar.org/specter/v1/invoke"
    MAX_BATCH_SIZE = batch_size
    cnt=0
    while cnt < len(papers):
        upper_bound = min(cnt + MAX_BATCH_SIZE, len(papers))
        chunk = papers[cnt:upper_bound]
        response = requests.post(URL, json=chunk)
        if response.status_code != 200:
            raise RuntimeError("Sorry, something went wrong, please try later!")

        for paper in response.json()["preds"]:
            embeddings_by_paper_id[paper["paper_id"]] = paper["embedding"]
        cnt = upper_bound
    
    return embeddings_by_paper_id


def recommend_paper(paper_title: str):
    load_dotenv(find_dotenv())
    paper_id = convert_to_paper_id(paper_title)
    print(paper_id)
    recommend = recommendation_url + f"/papers/forpaper/{paper_id}"
    params = {'fields': "title,url,year,abstract"}
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    headers = {'x-api-key': api_key}
    response = requests.get(recommend, params=params, headers=headers)
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        # Extract the list of recommended papers from the response
        data = data.get("recommendedPapers", [])
    else:
        # Handle the error, e.g., print an error message
        raise Exception(
            f"Request failed with status code {response.status_code}")
    cnt = 0
    print(len(data))
    recommended_papers = []
    topic = set()
    for inst in data:
        if inst['abstract'] is not None and inst['title'] not in topic:
            cnt += 1
            topic.add(inst['title'])
            recommended_papers.append(Document(
                page_content=inst['abstract'],
                metadata={'title': inst['title'],
                          'year': inst['year'],
                          'url': inst['url']},
                id=cnt
            ))
    return recommended_papers, cnt
