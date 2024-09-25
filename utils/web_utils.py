from langchain_community.document_loaders import ArxivLoader
from bs4 import BeautifulSoup
import requests
from typing import List
from uuid import uuid4
from langchain_core.documents import Document

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
    papers = soup.find("div", id=f"{year}{event}-{paper_type}").select("strong > a")
    paper_list = [paper.get_text() for paper in papers]
    paper_list = paper_list[1:]
    return paper_list


def fetch_title_and_abstract(event: str, year:str, paper_type: str) -> List:
    nlp= ['acl', 'emnlp', 'eacl', 'naacl']
    ml = ['icml', 'iclr', 'neurips', 'aaai']
    if event in nlp:
        output = nlp_fetcher(event=event, year=year, paper_type=paper_type)
    else:
        pass
    return output

def ml_fetcher(event:str, year:str, paper_type: str) -> List:
    event = event.capitalize()
    url = f"https://openreview.net/group?id={event}.cc/2024/Conference#tab-accept-oral"
    response = requests.get(url)
    if response.status_code == 200:
        html= response.text
        soup = BeautifulSoup(html, 'html.parser')
    else:
        raise Exception(f"{url} does not exist")
    papers = soup.find("div", 'tab-content')
    pass
    # todo need to modify a bit (use selenium)
    # https://jimmy-ai.tistory.com/396
    # use selenium


def nlp_fetcher(event: str, year:str, paper_type: str) -> List:
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
    title_num=[]
    title_dict={}
    abstract_num=[]
    abstract_dict={}
    for title in titles:
        title_num.append(int(title.attrs['href'].split('.')[-1][:-1]))
        title_dict[int(title.attrs['href'].split('.')[-1][:-1])] = title.get_text()
    for abstract in abstracts:
        abstract_num.append(int(abstract.attrs['id'].split('--')[-1]))
        abstract_dict[int(abstract.attrs['id'].split('--')[-1])] = abstract.get_text()
    final_num = list(set(title_num) & set(abstract_num))
    output=[]
    for idx, num in enumerate(final_num):
        # output.append((title_dict[num], abstract_dict[num]))
        document = Document(
            page_content=abstract_dict[num],
            metadata={'title': title_dict[num]},
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
    
