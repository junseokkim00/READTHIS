from langchain_community.document_loaders import ArxivLoader
from bs4 import BeautifulSoup
import requests
from typing import List
from uuid import uuid4
from langchain_core.documents import Document
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from tavily import TavilyClient
from utils.arxiv_utils import load_paper_arxiv_api
from utils.semantic_scholar_utils import search_paper_batch
# from dotenv import load_dotenv, find_dotenv
# import os
import streamlit as st


def tavilySearch(query: str, max_results=20):
    # try:
    # load_dotenv()
    # api_key = os.getenv('TAVILY_API_KEY')
    api_key = st.secrets["TAVILY_API_KEY"]
    client = TavilyClient(api_key=api_key)
    response_arxiv = client.search(query, search_depth="advanced", include_domains=[
                                    'arxiv.org'], max_results=20)
    response = response_arxiv['results']
    results = []
    arxivSet = set()
    idx = 0
    for resp in response:
        link = resp['url']
        arxivId = link.split('/')[-1]
        if 'v' in arxivId:
            arxivId = arxivId.split('v')[0]
        if arxivId not in arxivSet:
            arxivSet.add(arxivId)
    paper_infos = search_paper_batch(list(arxivSet))
    for paper_info in paper_infos:
        if paper_info is not None and paper_info['title'] is not None and paper_info['abstract'] is not None and paper_info['year'] is not None and paper_info['url'] is not None:
            document = Document(
                page_content=paper_info['abstract'],
                metadata={
                    'paperId': paper_info['paperId'],
                    'title': paper_info['title'],
                    'year': paper_info['year'],
                    'url': paper_info['url'],
                    'citationCount': paper_info['citationCount'],
                    'type': "internet"
                },
                id=idx
            )
            results.append(document)
            idx += 1
    return results
    # except:
    #     return None


def duckduckgoSearch(query: str, max_results=100):
    """
    fetch paper from the web browser (duckduckgo)
    ## args
    - query: query for the browser
    - max_results: number of result
    """
    try:
        wrapper = DuckDuckGoSearchAPIWrapper()
        output = wrapper.results(query=query, max_results=max_results)
        print(len(output))
        arxivSet = set()
        result = []
        idx = 0
        # for inst in output:
        #     if 'arxiv.org' in inst['link'] and 'ar5iv' not in inst['link']:
        #         arxivId = inst['link'].split('/')[-1]
        #         if 'v' in arxivId:
        #             arxivId = arxivId.split('v')[0]
        #         if arxivId not in arxivSet:
        #             arxivSet.add(arxivId)
        #             paper_info = load_paper_arxiv_api(arxiv_id=arxivId)
        #             document = Document(
        #                 page_content=paper_info.summary,
        #                 metadata={'title': paper_info.title,
        #                         'year': paper_info.published.strftime("%Y"),
        #                         'url':paper_info.entry_id,
        #                         'type': "internet"},
        #                 id=idx
        #             )
        #             result.append(document)
        #             idx+=1
        for inst in output:
            if 'arxiv.org' in inst['link'] and 'ar5iv' not in inst['link']:
                arxivId = inst['link'].split('/')[-1]
                if 'v' in arxivId:
                    arxivId = arxivId.split('v')[0]
                if arxivId not in arxivSet:
                    arxivSet.add(arxivId)
        paper_infos = search_paper_batch(list(arxivSet))
        for paper_info in paper_infos:
            document = Document(
                page_content=paper_info['abstract'],
                metadata={
                    'paperId': paper_info['paperId'],
                    'title': paper_info['title'],
                    'year': paper_info['year'],
                    'url': paper_info['url'],
                    'citationCount': paper_info['citationCount'],
                    'type': "internet"
                },
                id=idx
            )
            result.append(document)
            idx += 1
        return result
    except:
        return None


def quickSearch(query: str, max_results=100):
    """
    fetch paper from the web browser (duckduckgo)
    ## args
    - query: query for the browser
    - max_results: number of result
    """
    wrapper = DuckDuckGoSearchAPIWrapper()
    output = wrapper.results(query=query, max_results=max_results)
    print(len(output))
    arxivSet = set()
    idx = 0
    for inst in output:
        if 'arxiv.org' in inst['link'] and 'ar5iv' not in inst['link']:
            print("arxiv")
            arxivId = inst['link'].split('/')[-1]
            if 'v' in arxivId:
                arxivId = arxivId.split('v')[0]
            paper_info = load_paper_arxiv_api(arxiv_id=arxivId)
            document = {
                'title': paper_info.title,
                'abstract': paper_info.summary,
                'url': paper_info.entry_id,
                'arxiv_id': arxivId
            }
            return document
    return {}


def fetch_paper_list(event: str, year: str, paper_type: str) -> List:
    """
    fetch paper by web-scraping using `BeautifulSoup`
    ## Args:
    - event (str): the name of the conference
    - year (str): the year of the conference
    - paper_type: the ype of the paper
    ## return:
    List of the title of the paper
    """
    url = f"https://aclanthology.org/events/{event}-{year}/"
    response = requests.get(url)
    if response.status_code == 200:
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
    else:
        return []
    papers = soup.find(
        "div", id=f"{year}{event}-{paper_type}").select("strong > a")
    paper_list = [paper.get_text() for paper in papers]
    paper_list = paper_list[1:]
    return paper_list


def fetch_title_and_abstract(event: str, year: str, paper_type: str) -> List:
    nlp = ['acl', 'emnlp', 'eacl', 'naacl']
    ml = ['icml', 'iclr', 'neurips', 'aaai']
    if event in nlp:
        output = nlp_fetcher(event=event, year=year, paper_type=paper_type)
    else:
        pass
    return output


def ml_fetcher(event: str, year: str, paper_type: str) -> List:
    event = event.capitalize()
    url = f"https://openreview.net/group?id={event}.cc/2024/Conference#tab-accept-oral"
    response = requests.get(url)
    if response.status_code == 200:
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
    else:
        raise Exception(f"{url} does not exist")
    papers = soup.find("div", 'tab-content')
    pass
    # todo need to modify a bit (use selenium)
    # https://jimmy-ai.tistory.com/396
    # use selenium


def nlp_fetcher(event: str, year: str, paper_type: str) -> List:
    url = f"https://aclanthology.org/events/{event}-{year}/"
    response = requests.get(url)
    if response.status_code == 200:
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
    else:
        raise Exception(f"{url} does not exist")
    papers = soup.find("div", id=f"{year}{event}-{paper_type}")
    titles = papers.select("span.d-block > strong > a.align-middle")
    # titles = papers.select("strong > a.align-middle")
    abstracts = papers.find_all(class_="card")
    title_num = []
    title_dict = {}
    
    abstract_num = []
    abstract_dict = {}
    for title in titles:
        title_num.append(int(title.attrs['href'].split('.')[-1][:-1]))
        title_num.append(title.attrs['href'])
        title_dict[int(title.attrs['href'].split('.')
                       [-1][:-1])] = title.get_text()
    for abstract in abstracts:
        abstract_num.append(int(abstract.attrs['id'].split('--')[-1]))
        abstract_dict[int(abstract.attrs['id'].split('--')[-1])
                      ] = abstract.get_text()
    final_num = list(set(title_num) & set(abstract_num))
    output = []
    for idx, num in enumerate(final_num):
        # output.append((title_dict[num], abstract_dict[num]))
        document = Document(
            page_content=abstract_dict[num],
            metadata={'title': title_dict[num],
                      'paper_type': paper_type
                      },
            id=idx
        )
        output.append(document)
    return output


def load_paper(arxiv_id: str):
    try:
        paper_load = ArxivLoader(
            query=arxiv_id,
            load_max_docs=1
        )
        docs = paper_load.load()
        return docs[0].metadata
    except Exception as e:
        return {}


def title_to_abstract(title: str) -> str:
    try:
        paper_load = ArxivLoader(
            query=title,
            load_max_docs=1
        )
        docs = paper_load.load()
        return docs[0].metadata['Summary']
    except Exception as e:
        print(e)
        return "Failed to get abstract."
