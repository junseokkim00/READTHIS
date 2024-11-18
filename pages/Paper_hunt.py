import streamlit as st
import pandas as pd
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
    layout="wide"
)
st.title("Paper :red[Hunt] 🕵️‍♂️")
st.subheader(
    "find the latest paper to read from daily :orange[rss feed]", divider=True)


with st.sidebar:
    # category = st.selectbox(
    #     "select category for new arxiv papers",
    #     (key for key in category_map),
    #     index=None,
    #     placeholder="select category"
    # )
    embed_name = st.selectbox(
        "select embeddings",
        ("openai", "huggingface"),
        index=None,
        placeholder="select embeddings"
    )
    if embed_name == 'openai':
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
        elif embed_name == 'huggingface':
            pass
        else:
            st.error("OpenAI_api_key is not configured!", icon='🚨')


def check_config():
    if embed_name == "openai":
        return 'openai_api_key' in st.session_state and st.session_state['openai_api_key'] != ""
    elif embed_name == "huggingface":
        return True
    else:
        return False


category = st.selectbox(
    "select category for new arxiv papers",
    (key for key in category_map),
    index=None,
    placeholder="select category"
)

if category and check_config():
    with st.status(f"Fetching the latest rss feed", expanded=True):
        feed_list = load_paper_from_rss(category=category)
        st.write(
            f"you have :red[{len(feed_list)}] papers from the latest feed")
    if len(feed_list) == 0:
        st.error("Try to visit next time!")
    else:
        prompt = st.text_input(
            "Describe the idea of a paper you want to find.")
        if prompt:
            with st.chat_message('user'):
                st.write(prompt)
            with st.status("setting up database for the latest paper..."):
                # embeddings = get_embeddings(
                #     api_key=st.session_state['openai_api_key']
                # )
                if embed_name == "openai":
                    embeddings = get_embeddings(
                        api_key=st.session_state['openai_api_key']
                    )
                else:
                    embeddings = get_embeddings(
                        name=embed_name
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
                        'score': doc[1],
                        'identifier': doc[0].metadata['identifier'],
                        'abstract': abstract,
                        'link': doc[0].metadata['url'],
                        'type': "rss"
                    }
                    response.append(inst)
            list_view, dataframe_view = st.tabs(['list', 'dataframe'])
            with list_view:
                with st.container(border=True):
                    for idx, recommendation in enumerate(response):
                        with st.expander(f"{idx}. {recommendation['title']} :orange[{recommendation['type']}] ({recommendation['score']}%) "):
                            st.markdown(f'''# {recommendation['title']}

Score {recommendation['score']}

Identifier: {recommendation['identifier']}

[Link]({recommendation['link']})
## Abstract
{recommendation['abstract']}''')
            with dataframe_view:
                df = pd.DataFrame(response)
                st.data_editor(
                    df,
                    column_config={
                        "link": st.column_config.LinkColumn(
                            "URL",
                            max_chars=100,
                            display_text="Open Link"
                        ),
                        "title": st.column_config.TextColumn(
                            "title", max_chars=100
                        ),
                        "abstract": st.column_config.TextColumn(
                            "abstract", max_chars=100
                        ),
                        "score": st.column_config.NumberColumn(
                            "score", format="%f %%"
                        ),
                    },
                )
            shutil.rmtree(f'./db/{db_name}')
else:
    with st.container(border=True):
        st.markdown("""## How to use Paper Hunt?
### 1. configure your setting
+ select category: categories denotation is presented [here](https://arxiv.org/category_taxonomy)
+ select embeddings
    + `openai`: Fast but require api_key
    + `huggingface`: slower but free! (we use [`bge-small-en`](https://huggingface.co/BAAI/bge-small-en) embeddings)
""")
