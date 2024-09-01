import streamlit as st
from utils.web_utils import fetch_title_and_abstract
from utils.db_utils import get_embeddings, load_db, set_db, add_documents
from utils.LLM_utils import set_model, query_rewrite, judge_paper
from langchain_community.document_loaders import ArxivLoader
import os

st.title("Read :red[This]📝")
st.subheader("find papers based on their `abstract`", divider=True)

# st.set_page_config(
#     page_title="What's new",
#     page_icon="📄",
# )

# sidebar setting
event = st.sidebar.selectbox(
    "Select event",
    ("acl", "emnlp")
)
year = st.sidebar.selectbox(
    "Select year",
    ("2024", "2023")
)
paper_type = st.sidebar.selectbox(
    "Select paper type",
    ("long", "short", "main")
)
with st.sidebar:
    openai_api_key = st.text_input(
        "OpenAI API Key", key="langchain_search_api_key_openai", type="password")
    groq_api_key = st.text_input(
        "GROQ_API_KEY", key="groq_api_key", type='password')
    

prompt = st.chat_input("Enter your query")
if prompt and event and year and paper_type:
    with st.chat_message('user'):
        st.write(prompt)
    db_name = f"{year}{event}-{paper_type}"
    query = prompt
    embeddings = get_embeddings()
    if os.path.exists(f'./db/{db_name}/'):
        with st.status(f"Loading {db_name} db...", expanded=True):
            db = load_db(name=db_name,
                         embeddings=embeddings)
    else:
        with st.status(f"Generating {db_name} db...", expanded=True):
            db = set_db(name=db_name,
                        embeddings=embeddings)
        with st.status(f"Fetching paper based on the event of {db_name}...", expanded=True):
            Documents = fetch_title_and_abstract(event=event,
                                                 year=year,
                                                 paper_type=paper_type
                                                 )
        with st.status("Adding documents...", expanded=True):
            db = add_documents(db=db,
                               documents=Documents)
    # db = load_db(name=db_name,
    #              embeddings=embeddings)



    # retriever = db.as_retriever(search_kwargs={'k': 10})



    llm = set_model(name='llama3-8b-8192')
    with st.status(f"Rewriting query", expanded=True):
        st.write(f"Original query: {query}")
        rewrite_query = query_rewrite(model=llm,
                                      query=query)
        st.write(f"Rewritten query: {rewrite_query}")
    # rewrite_query = query_rewrite(model=llm,
    #                       query=query)
    with st.status(f"Retrieving...", expanded=True):
        # result = retriever.invoke(rewrite_query)
        result = db.similarity_search_with_score(rewrite_query, k=10) # cosine distance
    # result = retriever.invoke(rewrite_query)
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

                from `{db_name}`
                ''')
