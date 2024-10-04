import streamlit as st
import os
import shutil
from utils.db_utils import set_db, get_embeddings, add_documents
from utils.semantic_scholar_utils import get_cited_papers, recommend_paper, get_citations
from utils.LLM_utils import set_model, query_rewrite, judge_paper
from langchain_community.document_loaders import ArxivLoader
from utils.arxiv_utils import load_paper_arxiv_api, retrieve_paper
from utils.web_utils import duckduckgoSearch
import time
from utils.category_list import category_map

st.set_page_config(
    page_title="What's Next?",
    page_icon="📄",
)
st.title("What's :red[Next]? 📄")
st.subheader(
    "find the next paper to read based on their `abstract`", divider=True)


with st.sidebar:
    judge_llm = st.checkbox("Use llm to judge paper", disabled=True)
    rewrite_query = st.checkbox("rewrite query?", disabled=True)
    openai_api_key = st.text_input("OpenAI api key", type="password")

    st.markdown(
            "[Learn more about OpenAI API](https://platform.openai.com/api-keys)")

    save_configuration = st.button("Save OPENAI API KEY")
    if save_configuration and 'openai_api_key' in st.session_state:
        st.session_state['openai_api_key'] = openai_api_key
        st.success('OpenAI configuration saved!', icon="✅")
        st.toast('✅ OpenAI configuration saved!')
    else:
        st.error('OpenAI configuration is not initialized!', icon="🚨")

# main side
arxiv_number = st.text_input("Enter arxiv number (e.g. 1706.03762)")
query = st.chat_input("Enter the prompt")

if arxiv_number and query and 'openai_api_key' in st.session_state:
    with st.chat_message('user'):
        st.write(query)
        st.write(
            f"Config: judge_llm: `{judge_llm}` rewrite_query: `{rewrite_query}`")
    with st.status(f"Searching paper of arxiv number {arxiv_number}...", expanded=True):
        metadata = load_paper_arxiv_api(arxiv_id=arxiv_number)
        title = metadata.title
        categories = metadata.categories
        st.write(f"Title: `{title}`")
        st.write(f"Categories: `{categories}`")
    with st.status(f"retrieving cited paper...", expanded=True):
        time.sleep(1)
        embeddings = get_embeddings(api_key=st.session_state['openai_api_key'])
        db = set_db(name=arxiv_number,
                    embeddings=embeddings,
                    save_local=False)
        documents, cnt = get_cited_papers(arxiv_number)
        st.write(
            f"There is :red[{cnt}] papers highly related to the given paper.")

    with st.status(f"retrieving citations...", expanded=True):
        time.sleep(2.05)
        citations, cite_cnt = get_citations(arxiv_number)
        st.write(
            f"There is :red[{cite_cnt}] citation papers in the given paper."
        )
    # with st.status(f"retrieving un-cited paper...", expanded=True):
    #     uncited_papers = retrieve_paper(category_list=categories)
    #     st.write(
    #         f"There is :red[{len(uncited_papers)}] papers that has the same category with the given paper.")
    with st.status(f"retrieving from the internet...", expanded=True):
        time.sleep(2.05)
        searchOutput = duckduckgoSearch(query=query)
        st.write(
            f"There is :red[{len(searchOutput)}] papers searched from the internet."
        )
    with st.status(f"adding documents..."):
        if len(documents) > 0:
            db = add_documents(db=db,
                               documents=documents)
        print("ADDING CITATIONS...")
        if len(citations) > 0:
            db = add_documents(db=db,
                               documents=citations)
        print("ADDING INTERNET PAPERS...")
        if len(searchOutput) > 0:
            db = add_documents(
                db=db,
                documents=searchOutput
            )

    # REWRITE PROMPT
    llm = set_model(name="llama3-8b-8192")
    if rewrite_query:
        with st.status(f"Rewriting query", expanded=True):
            st.write(f"Original query: {query}")
            rewrite_query = query_rewrite(model=llm,
                                          query=query)
            st.write(f"Rewritten query: {rewrite_query}")
    else:
        rewrite_query = query
    # RETRIEVE
    with st.status(f"Retrieving...", expanded=True):
        try:
            result = db.similarity_search_with_score(rewrite_query, k=10)
        except:
            st.error("DB does not have documents.")
        for res in result:
            print(res[0].metadata['title'])
    # JUDGE PAPER
    response = []
    progress_bar = st.progress(
        0, text=f"Filtering documents from retrieved documents (0 / {len(result)})")
    for idx, doc in enumerate(result):
        print(doc[0].metadata)
        abstract, title = doc[0].page_content, doc[0].metadata['title']
        if judge_llm:
            output = judge_paper(model=llm, title=title,
                                 abstract=abstract, query=query)
            if output['read'] == 'yes':
                paper_load = ArxivLoader(
                    query=title,
                    load_max_docs=1,
                    load_all_available_meta=True
                )
                paper = paper_load.load()
                link = paper[0].metadata['links'][-1]
                inst = {
                    'title': title,
                    'abstract': abstract,
                    'insights': output['insights'],
                    'link': link,
                    'score': doc[1],
                    'type': f":red[{doc[0].metadata['type']}]" if doc[0].metadata['type'] == "citation" else f":blue[{doc[0].metadata['type']}]" if doc[0].metadata['type'] == "cited paper" else f":green[{doc[0].metadata['type']}]"
                }
                response.append(inst)
            else:
                pass
        else:
            inst = {
                'title': title,
                'abstract': abstract,
                'insights': None,
                'link': doc[0].metadata['url'],
                'score': doc[1],
                'type': f":red[{doc[0].metadata['type']}]" if doc[0].metadata['type'] == "citation" else f":blue[{doc[0].metadata['type']}]" if doc[0].metadata['type'] == "cited paper" else f":green[{doc[0].metadata['type']}]"
            }
            response.append(inst)
        progress_bar.progress(int(100 * (idx+1) / len(result)),
                              text=f"Filtering documents from retrieved documents ({idx+1} / {len(result)})")
    with st.chat_message('assistant'):
        with st.container(border=True):
            for idx, recommendation in enumerate(response):
                with st.expander(f"{idx}. {recommendation['title']} {recommendation['type']}"):
                    st.markdown(f'''# {recommendation['title']}

Score {recommendation['score']}

Type {recommendation['type']}

[Link]({recommendation['link']})
## Abstract
{recommendation['abstract']}
## Insights
{recommendation['insights']}''')
    copy_code = [f"{idx+1}. {resp['title']}" for idx,
                 resp in enumerate(response)]
    copy_code = '\n'.join(copy_code)
    st.code(copy_code, language='markdown')
elif 'openai_api_key' in st.session_state:
    st.error(
        "Please enter your current paper's arxiv number and your query.", icon='🚨')
else:
    st.error('Please setup your **OpenAI configuration**(left sidebar) first if you want to use this service!', icon='🚨')

#     col1, col2 = st.columns(2)
#     with col1:
#         st.header('pdf')

#     with col2:
#         st.header('Recommended papers')
#         for idx, recommendation in enumerate(response):
#             with st.expander(f"{idx}. {recommendation['title']}"):
#                 st.markdown(f'''# {recommendation['title']}

# Score {recommendation['score']}

# Type {recommendation['type']}

# [Link]({recommendation['link']})
# ## Abstract
# {recommendation['abstract']}
# ## Insights
# {recommendation['insights']}''')
