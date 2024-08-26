from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import os
from dotenv import find_dotenv, load_dotenv

def set_model(name:str):
    load_dotenv(find_dotenv())
    if name == 'llama3-8b-8192':
        os.environ['GROQ_API_KEY'] = os.getenv('GROQ_API_KEY')
        llm = ChatGroq(model=name)
    else:
        raise Exception(f"{name} is currently not supported.")
    return llm

def query_rewrite(model, query) -> str:
    sys_msg="You have a talent in rewriting a query that has a shorter length than the given query, while maintaining the semantic meaning of the given query. Please only return your output without giving any preambles or reasons."
    human_msg="query to rewrite: {query}"
    prompt = ChatPromptTemplate([
        ('system', sys_msg),
        ('human', human_msg)
    ])
    chain = prompt | model
    output = chain.invoke({'query': query})
    return output.content

def judge_paper(model, title, abstract, query):
    sys_msg= "You are a prominent AI researcher and you need to help students by telling them whether they should read the given paper or not. \
            You will be given the title, and abstract of the paper as an input. Based on the student's intention, tell them whether to read them or not. \
            Additionally, if they need to read the given paper, give some insights, and some focus point while reading the paper based on the given abstract. \
            You should strictly follow the JSON format of the output, which contains \"read\", \"insights\" as a key. Each of the key describes the following: \
                - \"read\": whether the student should read the given paper. (\'yes\' or \'no\')\n \
                - \"insights\": the insight or focus point while reading the given paper.\n \
                Now, begin!"
    human_msg="""title of the paper: {title}
    abstract of the paper: {abstract}

    student's intention for reading the paper: {query}
    output:
    """
    prompt = ChatPromptTemplate([
        ('system', sys_msg),
        ('human', human_msg)
    ])
    chain = prompt | model | JsonOutputParser()
    try:
        output = chain.invoke({'title': title, 'abstract': abstract, 'query': query})
    except Exception as e:
        output = {
            'read': "no",
            'insights': e
        }
    return output
    
    