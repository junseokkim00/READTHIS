from fastapi import FastAPI
from utils.db_utils import get_embeddings, load_db
from utils.LLM_utils import set_model, query_rewrite, judge_paper

app = FastAPI()

@app.get('/')
def read_root():
    return {
        "Hello": "Cite4"
    }

@app.get('/chat/{db_name}/{query}')
def chat(db_name: str, query: str):
    embeddings = get_embeddings()
    db = load_db(name=db_name,
                 embeddings=embeddings)
    retriever = db.as_retriever(search_kwargs={'k': 10})
    llm = set_model(name='llama3-8b-8192')
    rewrite_query = query_rewrite(model=llm,
                          query=query)
    result = retriever.invoke(rewrite_query)
    response=[]
    for idx, doc in enumerate(result):
        abstract, title = doc.page_content, doc.metadata['title']
        output = judge_paper(model=llm, title=title, abstract=abstract, query=query)
        if output['read'] == 'yes':
            # get link for each paper
            inst = {
                'title': title,
                'abstract': abstract,
                'insights': output['insights'],
                'link': "https://arxiv.org/"
            }
            response.append(inst)
    return {
        'response': response
    }

