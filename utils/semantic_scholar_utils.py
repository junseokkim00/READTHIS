import requests
import os
from dotenv import find_dotenv, load_dotenv
from langchain_core.documents import Document
BASE_URL = "https://api.semanticscholar.org"
academic_graph_url = BASE_URL+"/graph/v1"
recommendation_url = BASE_URL + "/recommendations/v1"


def search_paper_batch(id_list):
    arxiv_id_list = [f"ARXIV:{id}" for id in id_list]
    load_dotenv(find_dotenv())
    api_key = os.getenv('SEMANTIC_SCHOLAR_API_KEY')
    query_batch = academic_graph_url + "/paper/batch"
    query_params = {'fields': 'title,abstract,authors,year,url,citationStyles'}
    headers = {'x-api-key': api_key}
    response = requests.post(
        query_batch,
        parms=query_params,
        headers=headers,
        json={"ids": arxiv_id_list}
    )
    if response.status_code == 200:
        response_data = response.json()
    else:
        print(
            f"Request failed with status code {response.status_code}: {response.text}")
        response_data=[]
    return response_data



def search_query(query: str):
    load_dotenv(find_dotenv())
    api_key = os.getenv('SEMANTIC_SCHOLAR_API_KEY')
    query_search = academic_graph_url + "/paper/search"
    query_params = {
        'query': query, 'fields': 'title,abstract,authors,year,url,citationStyles', 'fieldsOfStudy': "Computer Science,Engineering", 'limit': 100}
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


def get_citations(arxiv_id: str):
    load_dotenv(find_dotenv())
    references = academic_graph_url + f"/paper/ARXIV:{arxiv_id}/references"
    params = {'limit': 1000,
              'fields': 'title,abstract,year,isInfluential,url,citationCount'}
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    headers = {'x-api-key': api_key}
    response = requests.get(references, params=params, headers=headers)

    if response.status_code == 200:
        response_data = response.json()
    else:
        # request failed
        return [], 0
    influential_papers = []
    paperId = set()
    cnt = 0
    for inst in response_data['data']:
        # if inst['isInfluential'] and inst['citingPaper']['abstract'] is not None and inst['citingPaper']['paperId'] not in paperId:
        if inst['citedPaper']['abstract'] is not None and inst['citedPaper']['title'] not in paperId and inst['citedPaper']['url'] is not None and inst['citedPaper']['year'] is not None:
            cnt += 1
            paperId.add(inst['citedPaper']['paperId'])
            influential_papers.append(Document(
                page_content=inst['citedPaper']['abstract'],
                metadata={'paperId': inst['citedPaper']['paperId'],
                          'title': inst['citedPaper']['title'],
                          'year': inst['citedPaper']['year'],
                          'url': inst['citedPaper']['url'],
                          'citationCount': inst['citedPaper']['citationCount'],
                          'type': 'citation'},

                id=cnt
            ))
            # TODO should Document id be unique?
    return influential_papers, cnt


def get_cited_papers(arxiv_id: str):
    load_dotenv(find_dotenv())
    citations = academic_graph_url + f"/paper/ARXIV:{arxiv_id}/citations"
    params = {'limit': 1000,
              'fields': 'title,abstract,year,isInfluential,url,citationCount'}
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    headers = {'x-api-key': api_key}
    response = requests.get(citations, params=params, headers=headers)

    if response.status_code == 200:
        response_data = response.json()
    else:
        # raise Exception(
        #     f"Request failed with status code {response.status_code}: {response.text}")
        return [], 0

    # filtering data
    influential_papers = []
    paperId = set()
    cnt = 0
    citationCnt = 0
    for inst in response_data['data']:
        # if inst['isInfluential'] and inst['citingPaper']['abstract'] is not None and inst['citingPaper']['paperId'] not in paperId:
        if inst['citingPaper']['abstract'] is not None and inst['citingPaper']['title'] not in paperId and inst['citingPaper']['url'] is not None and inst['citingPaper']['year'] is not None:
            citationCnt+=inst['citingPaper']['citationCount']
            cnt += 1
            paperId.add(inst['citingPaper']['paperId'])
            influential_papers.append(Document(
                page_content=inst['citingPaper']['abstract'],
                metadata={'paperId': inst['citingPaper']['paperId'],
                          'title': inst['citingPaper']['title'],
                          'year': inst['citingPaper']['year'],
                          'url': inst['citingPaper']['url'],
                          'citationCount': inst['citingPaper']['citationCount'],
                          'type': 'cited paper'},
                id=cnt
            ))
            # TODO should Document id be unique?
    print(citationCnt)
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

# def fetch_citation_num(paperId: str)->int:
#     load_dotenv(find_dotenv())
#     paper_detail_url = academic_graph_url + f"/paper/{paperId}"
#     params = {'fields': 'title,paperId,citationCount'}
#     api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
#     headers = {'x-api-key': api_key}
#     response = requests.get(paper_detail_url, params=params, headers=headers)
#     if response.status_code == 200:
#         data = response.json()
#         print(data)
#         return 0
#     else:
#         raise Exception(
#             f"Request failed with status code {response.status_code}")


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
    cnt = 0
    while cnt < len(papers):
        upper_bound = min(cnt + MAX_BATCH_SIZE, len(papers))
        chunk = papers[cnt:upper_bound]
        response = requests.post(URL, json=chunk)
        if response.status_code != 200:
            raise RuntimeError(
                "Sorry, something went wrong, please try later!")

        for paper in response.json()["preds"]:
            embeddings_by_paper_id[paper["paper_id"]] = paper["embedding"]
        cnt = upper_bound

    return embeddings_by_paper_id


def recommend_paper(paper_title: str):
    load_dotenv(find_dotenv())
    paper_id = convert_to_paper_id(paper_title)
    print(paper_id)
    recommend = recommendation_url + f"/papers/forpaper/{paper_id}"
    params = {'fields': "title,url,year,abstract,citationCount"}
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
        if inst['abstract'] is not None and inst['title'] not in topic and inst['url'] is not None and inst['year'] is not None:
            cnt += 1
            topic.add(inst['title'])
            recommended_papers.append(
                Document(
                    page_content=inst['abstract'], 
                    metadata={
                        'paperId': inst['paperId'],
                        'title': inst['title'],
                        'year': inst['year'],
                        'url': inst['url'],
                        'citationCount': inst['citationCount'],
                        'type': 'S2ORC'},
                    id=cnt
                )
            )
    return recommended_papers, cnt

    # influential_papers.append(Document(
    #     page_content=inst['citingPaper']['abstract'],
    #     metadata={'paperId': inst['citingPaper']['paperId'],
    #               'title': inst['citingPaper']['title'],
    #               'year': inst['citingPaper']['year'],
    #               'url': inst['citingPaper']['url'],
    #               'citationCount': inst['citingPaper']['citationCount'],
    #               'type': 'cited paper'},
    #     id=cnt
    # ))
