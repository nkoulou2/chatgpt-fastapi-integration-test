from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from langchain.chat_models import init_chat_model
from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain_community.document_loaders import WebBaseLoader
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Annotated
import os

load_dotenv()
open_api_key = os.getenv("OPENAI_API_KEY")
tavily_api_key = os.getenv("TAVILY_API_KEY")

model = init_chat_model('gpt-4o-mini', model_provider='openai')


memory = MemorySaver()
@tool
def web_search(user_query: str) -> str:
    """Use to search user queries and return a list of URLs depicting an article relevant to the user query.
    Only use articles from websites that don't require subscriptions (NBC News, CBS News, Google News) """
    search = TavilySearch(max_results=5)
    response = search.invoke({'query': user_query, 'time_range': 'week'})
    urls = [url['url'] for url in response['results']]
    return urls
    

@tool
def website_parser(
    url_list: Annotated[List[str], "List of URLs from Web Search Tool"], 
    article_choice: Annotated[int, "Index of which URL will be chosen from url_list"]
    ) -> str:
    """Choose one of the articles passed in url_list and parse the page content of the website"""

    article_url = url_list[article_choice]

    loader = WebBaseLoader(article_url)
    doc = loader.load()

    return doc[0].page_content.strip()


@tool
def final_answer(article: str) -> str:
    """Create a final answer which will be a concise and informative summary of the article passed to this function.
    This should be the answer that is returned back to the user after all the right tools have been used"""

    system_prompt = SystemMessagePromptTemplate.from_template("You are a helpful AI Assistant that takes in an article and returns a summary of the article")
    human_prompt = HumanMessagePromptTemplate.from_template("""You are tasked with creating a summary of an article which can be found here: {article}
                                                            The summary should be concise yet informative and retain all relevant facts and information needed to understand the article""")
    prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])

    chain = (
    {'article': lambda x: x['article']}
    | prompt
    | model
    | (lambda x: x.content)
    )

    return chain.invoke({'article': article})


tools = [web_search, website_parser, final_answer]

agent_executor = create_react_agent(model, tools, checkpointer=memory)
config = {"configurable": {"thread_id": "id123"}}

while True:
    query = input("Message: " )
    input_message = {'role': 'user', 'content': query}

    if query == 'q':
        break

    for step in agent_executor.stream(
        {"messages": [input_message]}, config=config, stream_mode="values"
    ):
        step["messages"][-1].pretty_print()