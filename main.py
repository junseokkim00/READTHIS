from utils.db_utils import (
    load_db
)
from utils.LLM_utils import (
    set_model,
    query_rewrite,
    judge_paper
)
import os
from dotenv import find_dotenv, load_dotenv
from langchain_openai import OpenAIEmbeddings


if __name__ == '__main__':
    event=input("Enter event name: ")
    year=input("Enter year: ")
    paper_type = input("Enter paper_type: ")
    db_name = f"{year}{event}-{paper_type}"
    print(f"You are currently using {db_name} db")

    load_dotenv(find_dotenv())
    os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
    embeddings = OpenAIEmbeddings()

    # load db
    db = load_db(name=db_name,
                 embeddings=embeddings)
    retriever = db.as_retriever(search_kwargs={'k': 10})
    print(f"{db_name} LOADED")
    query = input("Enter query: ")
    llm = set_model("llama3-8b-8192")
    rewritten_query = query_rewrite(model=llm, query=query)
    print(f"Your original query: {query}")
    print(f"After query rewriting: {rewritten_query}")
    select = input("Do you want to you the rewritten query for retrieving papers? (y/n)")
    if select != 'y':
        print("You are using the original query")
        rewritten_query = query
    else:
        print("You are using the rewritten query.")

    result = retriever.invoke(rewritten_query)
    print("This is the following result for your query:")
    for idx, doc in enumerate(result):
        abstract, title = doc.page_content, doc.metadata['title']
        output = judge_paper(model=llm, title=title, abstract=abstract, query=query)
        if output['read'] == 'yes':
            print(f"{idx}. title: {title}")
            print(f"abstract: {abstract}")
            print(f"insights: {output['insights']}")
            print('\n')
