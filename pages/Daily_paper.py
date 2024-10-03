import streamlit as st
import os
from utils.zotero_utils import Zotero
from utils.arxiv_utils import load_paper_arxiv_title
from utils.semantic_scholar_utils import get_cited_papers, get_citations
from utils.db_utils import set_db, get_embeddings, add_documents
from utils.web_utils import duckduckgoSearch
from collections import defaultdict
import time
import shutil
import json

st.set_page_config(
    page_title="Daily Paper",
    page_icon="📝",
)

st.title("Daily :red[Paper] 📄")
st.subheader(
    "find the next paper to read based on your paper collection of Zotero", divider=True
)


def check_config():
    return ('library_id' in st.session_state and 'library_type' in st.session_state and 'zotero_api_key' in st.session_state)


with st.sidebar:
    with st.expander("Zotero Configuration", expanded=True):
        library_id = st.text_input("library_id", type="default")
        library_type = st.selectbox(
            "library_type",
            ["user", 'group']
        )
        zotero_api_key = st.text_input("Zotero API key", type="password")
        openai_api_key = st.text_input("OpenAI api key", type="password")

        st.markdown(
            "[Learn more about Zotero API](https://www.zotero.org/support/dev/web_api/v3/start)")
        st.markdown(
            f"[check out `pyzotero`](https://github.com/urschrei/pyzotero)")
        save_configuration = st.button("Save Zotero Configuration")
    if save_configuration and ('library_id' in st.session_state and 'library_type' in st.session_state and 'zotero_api_key' in st.session_state):
        if 'library_id' not in st.session_state:
            st.session_state['library_id'] = library_id
        if 'library_type' not in st.session_state:
            st.session_state['library_type'] = library_type
        if 'zotero_api_key' not in st.session_state:
            st.session_state['zotero_api_key'] = zotero_api_key
        if 'openai_api_key' not in st.session_state:
            st.session_state['openai_api_key'] = openai_api_key

        st.success('Zotero configuration saved!', icon="✅")
        st.toast('✅ Zotero configuration saved!')
    else:
        st.error('Zotero configuration is not initialized!', icon="🚨")

if check_config():
    with st.status('initializing Zotero...'):
        zot = Zotero(library_id=st.session_state['library_id'],
                     library_type=st.session_state['library_type'],
                     api_key=st.session_state['zotero_api_key'])
    with st.status('fetching collections...', expanded=True):
        collection_dict = zot.retrieve_collection()
        collection_names = [name for name in collection_dict]
        st.write(f"Found {len(collection_names)} collections in your Zotero")
    collection_select = st.selectbox(
        "Choose collection for your next recommendation.",
        collection_names,
        index=None,
        key="collection_select"
    )
    prompt = st.text_input("Please tell me the direction for your next paper.")
    print(collection_select)

    if collection_select and prompt:
        with st.chat_message('user'):
            st.write(prompt)
        db_name = collection_select.replace(" ", "_")
        paper_relationship = defaultdict(list)
        if os.path.isdir(f'./db/{db_name}'):
            shutil.rmtree(f'./db/{db_name}')
        with st.status(f'fetching paper from collection `{collection_select}`', expanded=True):
            key = collection_dict[collection_select]
            paper = zot.retrieve_collection_papers(key=key)
            paper_json = [{'title': title, 'DOI': DOI} for title, DOI in paper]
            if os.path.isdir(f'./collections/{key}'):
                with open(f'./collections/{key}', 'r') as f:
                    collections_json = json.load(f)
                if collections_json == paper_json:
                    print("not updated.")

            with open(f'./collections/{key}', 'w') as f:
                json.dump(paper_json, f)
            arxivIds = []
            titles = []
            for title, DOI in paper:
                metadata = load_paper_arxiv_title(paper_name=title)
                arxivId = metadata.entry_id.split('/')[-1]
                if 'v' in arxivId:
                    arxivId = arxivId.split('v')[0]
                arxivIds.append((title, arxivId))
                titles.append(title)
                # st.write(f"title: {title}\tarxivId: {arxivId}")
            st.write(
                f"You have {len(paper)} paper in collection `{collection_select}`")
        total_paper_db = []
        with st.status(f"retrieving citations...", expanded=True):
            title_set = set()
            total_cnt = 0
            for title, arxivId in arxivIds:
                st.write(f"fetching citations of `{title}`...")
                time.sleep(2.05)
                citations, cite_cnt = get_citations(arxiv_id=arxivId)
                for citation in citations:
                    paper_relationship[citation.metadata['title']].append(
                        title)
                    if citation.metadata['title'] not in title_set and citation.metadata['title'] not in titles:
                        title_set.add(citation.metadata['title'])
                        total_paper_db.append(citation)
                        total_cnt += 1
                    else:
                        cite_cnt -= 1
                st.write(f":red[{cite_cnt}] paper is added to the db.")
            st.write(f"total number of citation paper: {total_cnt}")

        with st.status(f"retrieving cited paper...", expanded=True):
            total_cnt = 0
            for title, arxivId in arxivIds:
                st.write(f"fetching cited papers of `{title}`...")
                time.sleep(2.05)
                cited_papers, cited_cnt = get_cited_papers(arxiv_id=arxivId)
                for cited_paper in cited_papers:
                    paper_relationship[cited_paper.metadata['title']].append(
                        title)
                    if cited_paper.metadata['title'] not in title_set and cited_paper.metadata['title'] not in titles:
                        title_set.add(cited_paper.metadata['title'])
                        total_paper_db.append(cited_paper)
                        total_cnt += 1
                    else:
                        cited_cnt -= 1
                st.write(f":red[{cited_cnt}] paper is added to the db.")
            st.write(f"total number of cited paper: {total_cnt}")
        with st.status(f"retrieving from the internet...", expanded=True):
            total_cnt = 0
            searchOutput = duckduckgoSearch(query=prompt)
            for doc in searchOutput:
                if doc.metadata['title'] not in title_set and doc.metadata['title'] not in titles:
                    title_set.add(doc.metadata['title'])
                    total_paper_db.append(doc)
                    total_cnt += 1
            st.write(f"You got {total_cnt} papers via browsing the internet.")

        st.write(
            f"You have :red[{len(total_paper_db)}] papers in your recommendation DB.")
        with st.status(f"Generating DB...", expanded=True):
            embeddings = get_embeddings(
                api_key=st.session_state['openai_api_key'])
            db = set_db(
                name=db_name,
                embeddings=embeddings,
                save_local=True
            )
            st.write("Adding Documents...")
            db = add_documents(
                db=db,
                documents=total_paper_db
            )
        with st.status("Retrieving...", expanded=True):
            result = db.similarity_search_with_score(prompt, k=10)
            for res in result:
                print(res[0].metadata['title'])
        response = []
        progress_bar = st.progress(
            0, text=f"Filtering documents from retrieved documents (0 / {len(result)})")
        for idx, doc in enumerate(result):
            print(doc[0].metadata)
            abstract, title = doc[0].page_content, doc[0].metadata['title']
            result_paper = load_paper_arxiv_title(paper_name=title)
            arxivId = result_paper.entry_id.split('/')[-1]
            if 'v' in arxivId:
                arxivId = arxivId.split('v')[0]
            inst = {
                'title': title,
                'abstract': abstract,
                'arxiv_info': result_paper,
                'arxiv_id': arxivId,
                'insights': None,
                'link': result_paper.entry_id,
                'score': doc[1],
                'type': f":red[{doc[0].metadata['type']}]" if doc[0].metadata['type'] == "citation" else f":blue[{doc[0].metadata['type']}]" if doc[0].metadata['type'] == "cited paper" else f":green[{doc[0].metadata['type']}]"
            }
            response.append(inst)
            progress_bar.progress(int(100 * (idx+1) / len(result)),
                                  text=f"Filtering documents from retrieved documents ({idx+1} / {len(result)})")
        with st.chat_message('assistant'):
            with st.container(border=True):
                for idx, recommendation in enumerate(response):
                    with st.expander(f"{idx}. {recommendation['title']} ({recommendation['type']})"):
                        st.markdown(f'''# {recommendation['title']}

Score {recommendation['score']}

Type {recommendation['type']}

[Link]({recommendation['link']})

arxiv id: {recommendation['arxiv_id']}

## Abstract
{recommendation['abstract']}
## Insights
{recommendation['insights']}

## Related papers
{paper_relationship[recommendation['title']]}''')
                        # create = st.button(f"add to {collection_select}", key=recommendation['arxiv_id'])
                        # TODO comment for a moment...
                        # template=zot.zot.item_template('preprint')
                        # template['title'] = recommendation['title']
                        # template['abstractNote'] = recommendation['abstract']
                        # authors=[]
                        # for author in recommendation['arxiv_info'].authors:
                        #     name = author.name.split()
                        #     inst = {
                        #         'creatorType': 'author',
                        #         'firstName': name[0],
                        #         'lastName': name[1]
                        #     }
                        #     authors.append(inst)
                        # template['creators'] = authors
                        # template['repository'] = 'arXiv'
                        # template['archiveID'] = f'arXiv:{recommendation["arxiv_id"]}'
                        # template['date'] = recommendation['arxiv_info'].published.strftime("%Y-%m-%d")
                        # template['url'] = recommendation['link']
                        # template['libraryCatalog'] = 'arXiv.org'
                        # template['extra'] = f"{template['archiveID']} [{recommendation['arxiv_info'].primary_category.split('.')[0]}]"
                        # template['collections'] = [key]

                        # if create:
                        #     print('create!')
                        #     print(template)
#                             """title
# creators
# abstractNote
# repository: 'arXiv'
# archiveID: 'arXiv:{number}'
# date
# url
# # accessDate: time
# libraryCatalog: 'arXiv.org'
# extra: archiveID [category]
# collections: key"""

else:
    st.error('Please setup your **zotero configuration**(left sidebar) first if you want to use this service!', icon='🚨')
