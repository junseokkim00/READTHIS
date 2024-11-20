import streamlit as st
import pandas as pd
from st_link_analysis import st_link_analysis, NodeStyle, EdgeStyle
import os
import shutil
from utils.db_utils import set_db, get_embeddings, add_documents
from utils.semantic_scholar_utils import get_cited_papers, recommend_paper, get_citations, convert_to_paper_id
from utils.LLM_utils import set_model, query_rewrite, judge_paper
from langchain_community.document_loaders import ArxivLoader
from utils.arxiv_utils import load_paper_arxiv_api, retrieve_paper
from utils.web_utils import duckduckgoSearch, tavilySearch
import time
from utils.category_list import category_map
import json

st.set_page_config(
    page_title="What's Next?",
    page_icon="📄",
    layout="wide"
)
st.title("What's :red[Next]? 📄")
st.subheader(
    "find the next paper to read based on their `abstract`", divider=True)


with st.sidebar:
    # judge_llm = st.checkbox("Use llm to judge paper", disabled=True)
    # rewrite_query = st.checkbox("rewrite query?", disabled=True)
    use_web_search = st.checkbox("use web search?")
    fetch_from_s2orc = st.checkbox("fetch from S2ORC")
    top_k = st.number_input("top k", value=10, min_value=1, max_value=100, step=1)
    st.write("[What is S2ORC?](https://github.com/allenai/s2orc)")
    # sort_by_citations = st.checkbox("sort by citation number?")
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

# main side
def check_config():
    if embed_name == "openai":
        return 'openai_api_key' in st.session_state and st.session_state['openai_api_key'] != ""
    elif embed_name == "huggingface":
        return True
    else:
        return False

judge_llm = False
rewrite_query = False
sort_by_citations = False

tab1, tab2 = st.tabs(['find by Arxiv id', 'find by title of the paper'])

with tab1:
    use_arxiv_id=True
    arxiv_number = st.text_input("Enter arxiv number (e.g. 1706.03762)")
    
with tab2:
    use_arxiv_id=False
    paper_title = st.text_input("Enter the title of the paper (e.g. Attention is all you need.)")
query = st.chat_input("Enter the prompt")
# settings

def paper_info_check():
    if use_arxiv_id:
        return arxiv_number
    else:
        return paper_title




if paper_info_check() and query and check_config():
    with st.chat_message('user'):
        st.write(query)
    if use_arxiv_id:
        with st.status(f"Searching paper of arxiv number {arxiv_number}...", expanded=True):
            metadata = load_paper_arxiv_api(arxiv_id=arxiv_number)
            paper_title = metadata.title
            categories = metadata.categories
            st.write(f"Title: `{paper_title}`")
            st.write(f"Categories: `{categories}`")
    else:
        with st.status(f"Searching paper id with the title of {paper_title}..", expanded=True):
            paper_id = convert_to_paper_id(paper_title=paper_title)
            st.write(f"paperId: `{paper_id}`")
            arxiv_number = paper_id
        
    with st.status(f"retrieving cited paper...", expanded=True):
        time.sleep(1)
        # embeddings = get_embeddings(api_key=st.session_state['openai_api_key'])
        if embed_name == "openai":
            embeddings = get_embeddings(
                api_key=st.session_state['openai_api_key']
            )
        else:
            embeddings = get_embeddings(
                name=embed_name
            )
        if os.path.isdir(f'./db/{arxiv_number}'):
            shutil.rmtree(f'./db/{arxiv_number}')
        db = set_db(name=arxiv_number,
                    embeddings=embeddings,
                    save_local=True)
            
        documents, cnt = get_cited_papers(arxiv_number, use_arxiv_id=use_arxiv_id)
        st.write(
            f"There is :red[{cnt}] papers highly related to the given paper.")

    with st.status(f"retrieving citations...", expanded=True):
        time.sleep(2.05)
        citations, cite_cnt = get_citations(arxiv_number, use_arxiv_id=use_arxiv_id)
        st.write(
            f"There is :red[{cite_cnt}] citation papers in the given paper."
        )
    if fetch_from_s2orc:
        with st.status(f"retrieving recommendation from Semantic Scholar Open Research Corpus(S2ORC)...", expanded=True):
            time.sleep(2.05)
            recommendation, recommendation_cnt = recommend_paper(paper_title=paper_title)
            st.write(
                f"There is :red[{recommendation_cnt}] papers in Semantic Scholar Open Research Corpus.")
    
    if use_web_search:
        with st.status(f"retrieving from the internet...", expanded=True):
            time.sleep(2.05)
            # searchOutput = duckduckgoSearch(query=query)
            searchOutput = tavilySearch(query=query)
            if searchOutput is None:
                st.write("web search not working due to api limitation")
                searchOutput=[]
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
        if use_web_search:
            if len(searchOutput) > 0:
                db = add_documents(
                    db=db,
                    documents=searchOutput
                )
        if fetch_from_s2orc:
            if len(recommendation) > 0:
                db = add_documents(db=db,
                                documents=recommendation)

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
            result = db.similarity_search_with_score(rewrite_query, k=top_k)
            result = [(r[0], round((1-r[1]) * 100, 2))for r in result] 
        except Exception as e:
            print(e)
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
                    'link': link,
                    'score': doc[1],
                    'type': f":red[{doc[0].metadata['type']}]" if doc[0].metadata['type'] == "citation" else f":blue[{doc[0].metadata['type']}]" if doc[0].metadata['type'] == "cited paper" else f":green[{doc[0].metadata['type']}]" if doc[0].metadata['type'] == 'internet' else f":violet[{doc[0].metadata['type']}]"
                }
                response.append(inst)
            else:
                pass
        else:
            inst = {
                'title': title,
                'score': doc[1],
                'abstract': abstract,
                'link': doc[0].metadata['url'],
                'citationCount': doc[0].metadata['citationCount'],
                'type': doc[0].metadata['type']
            }
            response.append(inst)
        progress_bar.progress(int(100 * (idx+1) / len(result)),
                              text=f"Filtering documents from retrieved documents ({idx+1} / {len(result)})")

    with st.chat_message('assistant'):

        list_view, dataframe_view = st.tabs(['list', 'dataframe'])
        with list_view:
            with st.container(border=True):
                for idx, recommendation in enumerate(response):
                    paper_type = f":red[{recommendation['type']}]" if recommendation['type'] == "citation" else f":blue[{recommendation['type']}]" if recommendation['type'] == "cited paper" else f":green[{recommendation['type']}]" if recommendation['type'] == 'internet' else f":violet[{recommendation['type']}]"
                    expander_title = f"{recommendation['title']} {paper_type} ({recommendation['score']}%)"
                    if recommendation['citationCount'] > 100:
                        expander_title = f"🧐 **{expander_title}**"
                    with st.expander(f"{idx}. "+expander_title):
                        st.markdown(f'''# {recommendation['title']}

Score {recommendation['score']}

Type {paper_type}

[Link]({recommendation['link']})

Citation count: {recommendation['citationCount']}

## Abstract
{recommendation['abstract']}''')
        with dataframe_view:
            df = pd.DataFrame(response)
            # st.dataframe(df)
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

        # with graph_view:
        #     st.write("let me show you")
        #     elements = {}
        #     nodes = []
        #     edges = []
        #     current_node = {
        #         "data": {"id": 0,
        #                  "title": title,
        #                  #  "abstract": metadata.summary,
        #                  #  "link": metadata.entry_id,
        #                  "score": 100,
        #                  "label": "ORIGIN"}
        #     }
        #     nodes.append(current_node)
        #     # add current paper

        #     for idx, resp in enumerate(response):
        #         id = idx+1
        #         inst_node = {
        #             "data": {
        #                 "id": id,
        #                 "title": resp['title'],
        #                 # "abstract": resp['abstract'],
        #                 # "link": resp['link'],
        #                 "score": resp['score'],
        #                 "label": "PAPER"
        #             }
        #         }
        #         nodes.append(inst_node)
        #         inst_edge = {
        #             "data": {
        #                 "id": id + len(response),
        #                 "label": "CITED" if resp['type'] == 'cited paper' else "REFERENCE",
        #                 "source": 0 if resp['type'] == 'cited paper' else id,
        #                 "target": id if resp['type'] == 'cited paper' else 0
        #             }
        #         }
        #         edges.append(inst_edge)

        #     elements['nodes'] = nodes
        #     elements['edges'] = edges

        #     node_styles = [
        #         NodeStyle(label="PAPER", color="#FF7F3E", caption="title", icon="description"),
        #         NodeStyle(label="ORIGIN", color="#2A629A", caption="title", icon="description"),
        #     ]
        #     edge_styles = [
        #         EdgeStyle(label="CITED", caption='label',
        #                   labeled=True, directed=True),
        #         EdgeStyle(label="REFERENCE", caption='label',
        #                   labeled=True, directed=True),
        #         EdgeStyle(label="SEMANTIC SCHOLARS", caption='label',
        #                   labeled=True, directed=True),
        #     ]
        #     layout = {"name": "cose", "animate": "end", "nodeDimensionsIncludeLabels": False}
        #     # print(elements)
        #     st_link_analysis(elements, layout, node_styles, edge_styles)

        copy_code = [f"{idx+1}. {resp['title']}" for idx,
                     resp in enumerate(response)]
        copy_code = '\n'.join(copy_code)
        st.code(copy_code, language='markdown')
        shutil.rmtree(f'./db/{arxiv_number}')
elif check_config():
    st.error(
        "Please enter your current paper's arxiv number and your query.", icon='🚨')
elif embed_name == 'openai':
    st.error('Please setup your **OpenAI configuration**(left sidebar) first if you want to use this service!', icon='🚨')
else:
    with st.container(border=True):
        st.markdown("""## How to use What's Next?
#### 1. check for advanced search
+ `use web search`: also retrieve relevant paper from duckduckgo search (:red[limited by api rate limit])
+ `fetch from S2ORC`: fetching relevant papers from Semantic Scholar's Open Research Corpus ([More info here](https://github.com/allenai/s2orc))
#### 2. select embeddings
+ `openai`: Fast but require api_key
+ `huggingface`: slower but free! (we use [`bge-small-en`](https://huggingface.co/BAAI/bge-small-en) embeddings)
#### 3. Enter the arxiv number of the paper you are currently reading.
+ find arxiv number from [here](https://www.arxiv.org/).
#### 4. Enter the prompt that you want to explore in the future.
+ Examples
    + `Types of Attention mechanism`
    + `Using Attention mechanism in computer vision task`""")
        st.markdown("## Video Tutorial")
        video_file = open("assets/whats_next.mp4", "rb")
        video_bytes = video_file.read()
        st.video(video_bytes)
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
