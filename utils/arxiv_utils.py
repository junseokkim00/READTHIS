import arxiv
from sklearn.neighbors import NearestNeighbors
import json
from langchain_core.documents import Document
from tqdm import tqdm
import feedparser


def load_paper_from_rss(category: str):
    try:
        url = "https://rss.arxiv.org/rss/"+category
        feed = feedparser.parse(url)
        feed_list = feed.entries
        papers = []
        for cnt, feed in enumerate(feed_list):
            title = feed['title']
            abstract = feed['summary'].split('\n')[-1]
            if abstract.startswith("Abstract:"):
                abstract = abstract.split("Abstract: ")[-1]
            abstract = abstract.strip()
            print(abstract)
            papers.append(Document(
                page_content=abstract,
                metadata={
                    'title': title,
                    'year': feed['published_parsed'].tm_year,
                    'url': feed['link'],
                    'identifier': feed['link'].split('/')[-1],
                },
                id=cnt
            ))
        return papers
    except Exception as e:
        print(e)
        return []


def load_paper_arxiv_api(arxiv_id: str):
    client = arxiv.Client()
    search_by_id = arxiv.Search(id_list=[arxiv_id])
    result = next(client.results(search_by_id))
    return result


def load_paper_arxiv_title(paper_name: str):
    try:
        client = arxiv.Client()
        search_by_query = arxiv.Search(query=paper_name, max_results=1)
        result = next(client.results(search_by_query))
        return result
    except:
        return None


def retrieve_paper(category_list: list):
    papers = []
    paperId = set()
    for category_name in category_list:
        with open(f'./arxiv/category/{category_name}.jsonl', 'r') as f:
            lines = f.readlines()
        for line in lines:
            data = json.loads(line)
            if data['id'] not in paperId:
                paperId.add(data['id'])
                inst = {
                    'id': data['id'],
                    'title': data['title'],
                    'abstract': data['abstract'],
                    'year': data['update_date'].split('-')[0]
                }
                papers.append(inst)

    return papers
