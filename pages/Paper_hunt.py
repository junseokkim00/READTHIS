import streamlit as st
import os
import shutil
import feedparser
from utils.db_utils import set_db, get_embeddings, add_documents
from utils.semantic_scholar_utils import get_cited_papers, recommend_paper, get_citations
from utils.LLM_utils import set_model, query_rewrite, judge_paper
from langchain_community.document_loaders import ArxivLoader
from utils.arxiv_utils import load_paper_arxiv_api, retrieve_paper, load_paper_from_rss
import time
from datetime import date
from utils.category_list import category_map

st.set_page_config(
    page_title="Paper Hunt",
    page_icon="🕵️‍♂️",
)
st.title("Paper :red[Hunt] 🕵️‍♂️")
st.subheader(
    "find the latest paper to read from daily rss feed", divider=True)


with st.sidebar:
    category = st.selectbox(
        "select category for new arxiv papers",
        (key for key in category_map),
        index=None,
        placeholder="select category"
    )

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


prompt = st.text_input("Describe the idea of a paper you want to find.")
if prompt and check_config():

    with st.chat_message('user'):
        st.write(prompt)

    with st.status(f"Fetching the latest rss feed", expanded=True):
        feed_list = load_paper_from_rss(category=category)
        st.write(
            f"you have :red[{len(feed_list)}] papers from the latest feed")
    with st.status("setting up database for the latest paper..."):
        embeddings = get_embeddings(
            api_key=st.session_state['openai_api_key']
        )
        today = date.today()
        today = today.strftime("%Y-%m-%d")
        db_name = f"{today}-{category}"
        if os.path.isdir(f'./db/{db_name}'):
            shutil.rmtree(f'./db/{db_name}')
        db = set_db(name=db_name,
                    embeddings=embeddings,
                    save_local=True)
        db = add_documents(
            db=db,
            documents=feed_list
        )
    with st.status(f"Retrieving...", expanded=True):
        try:
            result = db.similarity_search_with_score(prompt, k=100)
            result = [(r[0], round((1-r[1]) * 100, 2))for r in result]
        except:
            st.error("DB does not have documents.")
    
        response = []
        for idx, doc in enumerate(result):
            abstract, title = doc[0].page_content, doc[0].metadata['title']
            inst = {
                'title': title,
                'abstract': abstract,
                'identifier': None,
                'link': doc[0].metadata['url'],
                'score': doc[1],
                'type': f":orange[rss]"
            }
            response.append(inst)
    
    with st.container(border=True):
        for idx, recommendation in enumerate(response):
            with st.expander(f"{idx}. {recommendation['title']} {recommendation['type']} {recommendation['score']} %"):
                st.markdown(f'''# {recommendation['title']}

Score {recommendation['score']}

[Link]({recommendation['link']})
## Abstract
{recommendation['abstract']}''')
