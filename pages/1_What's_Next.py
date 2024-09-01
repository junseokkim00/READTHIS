import streamlit as st
import os
from utils.db_utils import set_db, get_embeddings, add_documents
from utils.semantic_scholar_utils import get_cited_papers, recommend_paper
from utils.LLM_utils import set_model, query_rewrite, judge_paper
from langchain_community.document_loaders import ArxivLoader
from utils.web_utils import load_paper
st.title("What's :red[Next]? 📄")
st.subheader("find the next paper to read based on their `abstract`", divider=True)

# sidebar setting


# main side
arxiv_number = st.text_input("Enter arxiv number (e.g. 1706.03762)")
query = st.chat_input("Enter the prompt")
if arxiv_number and query:
    with st.chat_message('user'):
        with st.status(f"Searching paper of arxiv number {arxiv_number}...", expanded=True):
            metadata = load_paper(arxiv_id=arxiv_number)
            title = metadata['Title']
            st.write(f"Title: `{title}`")
        with st.status(f"retrieving cited paper...", expanded=True):
            embeddings = get_embeddings()
            db = set_db(name=arxiv_number,
                        embeddings=embeddings,
                        save_local=False)
            documents, cnt = get_cited_papers(arxiv_number)
            st.write(f"There is :red[{cnt}] papers highly related to the given paper.")
            # rec_documents,rec_cnt = recommend_paper(paper_title=title)
            # st.write(f"There is :red[{rec_cnt}] papers highly related to the given paper.")
        with st.status(f"adding documents..."):
            db = add_documents(db=db,
                            documents=documents)
            
        # REWRITE PROMPT
        llm = set_model(name="llama3-8b-8192")
        with st.status(f"Rewriting query", expanded=True):
            st.write(f"Original query: {query}")
            rewrite_query = query_rewrite(model=llm,
                                        query=query)
            st.write(f"Rewritten query: {rewrite_query}")
        # RETRIEVE
        with st.status(f"Retrieving...", expanded=True):
            result = db.similarity_search_with_score(rewrite_query, k=10)
        # JUDGE PAPER
        response = []
        progress_bar = st.progress(
            0, text=f"Filtering documents from retrieved documents (0 / {len(result)})")
        for idx, doc in enumerate(result):
            abstract, title = doc[0].page_content, doc[0].metadata['title']
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
                    'score': doc[1]
                }
                response.append(inst)
            progress_bar.progress(int(100 * (idx+1) / len(result)),
                                text=f"Filtering documents from retrieved documents ({idx+1} / {len(result)})")
    with st.chat_message('assistant'):
        with st.container(border=True):
            for recommendation in response:
                st.markdown(f'''
                # {recommendation['title']}

                Score {recommendation['score']}

                [Link]({recommendation['link']})
                ## Abstract
                {recommendation['abstract']}
                ## Insights
                {recommendation['insights']}
                ''')
