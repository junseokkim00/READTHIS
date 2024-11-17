import streamlit as st
import os
import shutil
from utils.db_utils import set_db, get_embeddings, add_documents
from utils.semantic_scholar_utils import get_cited_papers, recommend_paper, get_citations
from utils.LLM_utils import set_model, query_rewrite, judge_paper
from langchain_community.document_loaders import ArxivLoader
from utils.arxiv_utils import load_paper_arxiv_api, retrieve_paper
from utils.web_utils import duckduckgoSearch, quickSearch
import time
from utils.category_list import category_map

st.set_page_config(
    page_title="Describe it",
    page_icon="✍️",
    layout="wide"
)
st.title("Describe :red[it]!✍ ️")
st.subheader(
    "describe a paper you want to find!", divider=True
)

with st.sidebar:
    with st.expander("Openai api key setting"):
        openai_api_key = st.text_input("OpenAI api key", type="password")
        st.markdown(
            "[Learn more about OpenAI API](https://platform.openai.com/api-keys)")
        save_configuration = st.button("Save configuration")
        if save_configuration and openai_api_key != "":
            st.session_state['openai_api_key'] = openai_api_key
            st.toast("✅ Openai api key ready!")
    if 'openai_api_key' in st.session_state:
        st.success("OpenAI_api_key is configured!", icon='✅')
    else:
        st.error("OpenAI_api_key is not configured!", icon='🚨')


def check_config():
    return 'openai_api_key' in st.session_state and st.session_state['openai_api_key'] != ""



if True:
    st.error("Currently not available!", icon='🚨')
else:
    prompt = st.text_input("Describe the idea of a paper you want to find.")
    if prompt and check_config():
        with st.chat_message('user'):
            st.write(prompt)
        with st.status(f"Searching the idea on the internet...", expanded=True):
            document = quickSearch(query=prompt)
            print(document)
        if document is {}:
            st.error("Your idea looks novel. I cannot find it;;")
        else:
            with st.status(f"retrieving citations and cited papers...", expanded=True):
                time.sleep(1)
                embeddings = get_embeddings(
                    api_key=st.session_state['openai_api_key'])
                arxiv_number = document['arxiv_id']
                if os.path.isdir(f'./db/{arxiv_number}'):
                    shutil.rmtree(f'./db/{arxiv_number}')
                db = set_db(name=arxiv_number,
                            embeddings=embeddings,
                            save_local=True)
                documents, cnt = get_cited_papers(arxiv_number)
                st.write(f"There are :red[{cnt}] cited papers.")
                time.sleep(1)
                citations, cite_cnt = get_citations(arxiv_number)
                st.write(f"There are :red[{cite_cnt}] citations.")
            with st.status(f"Adding documents...", expanded=True):
                if cnt > 0:
                    db = add_documents(
                        db=db,
                        documents=documents
                    )
                if cite_cnt > 0:
                    db = add_documents(
                        db=db,
                        documents=citations
                    )
            with st.status(f"Retrieving...", expanded=True):
                try:
                    result = db.similarity_search_with_score(prompt, k=10)
                except:
                    st.error("DB does not have documents.")
            response = []
            inst = {
                'title': document['title'],
                'abstract': document['abstract'],
                'insights': None,
                'link': document['url'],
                'score': 0,
                'type': 'web search'
            }
            response.append(inst)
            for idx, doc in enumerate(result):
                abstract, title = doc[0].page_content, doc[0].metadata['title']
                inst = {
                    'title': title,
                    'abstract': abstract,
                    'insights': None,
                    'link': doc[0].metadata['url'],
                    'score': doc[1],
                    'type': f":red[{doc[0].metadata['type']}]" if doc[0].metadata['type'] == "citation" else f":blue[{doc[0].metadata['type']}]" if doc[0].metadata['type'] == "cited paper" else f":green[{doc[0].metadata['type']}]"
                }
                response.append(inst)
            with st.chat_message("assistant"):
                with st.container(border=True):
                    for idx, recommendation in enumerate(response):
                        with st.expander(f"{idx}. {recommendation['title']}"):
                            st.markdown(f'''# {recommendation['title']}

Score {recommendation['score']}

[Link]({recommendation['link']})
## Abstract
{recommendation['abstract']}
## Insights
{recommendation['insights']}''')
