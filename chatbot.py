import os

from langchain_openai import ChatOpenAI
from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationSummaryMemory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import ConfigurableFieldSpec
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()
open_api_key = os.getenv("OPENAI_API_KEY")
tavily_api_key = os.getenv("TAVILY_API_KEY")

OPENAI_MODEL='gpt-4o-mini'
TEMPERATURE=0.7

llm = ChatOpenAI(temperature=TEMPERATURE, model=OPENAI_MODEL)

system_prompt = SystemMessagePromptTemplate.from_template("You are a helpful AI Assistant that answers user queries accurately and concisely.")

user_prompt = HumanMessagePromptTemplate.from_template(
    """You are tasked with forming a creative yet accurate response
    to user queries which can be seen here: {query}""",
        input_variables=['query']
    )

prompt = ChatPromptTemplate.from_messages([
    system_prompt, 
    MessagesPlaceholder(variable_name='history'), 
    user_prompt
    ])

# basic chain that doesn't have conversational history (backup)
chain = (
    {'query': lambda x: x['query']}
    | prompt
    | llm
    | (lambda x: x.content)
)



async def get_openai_response(user_message: str) -> str:

    try:
        result = pipeline_with_history.invoke(
            {'query': user_message},
            config={'session_id': 'id_123', 'llm': llm}
        )
        print (result)
        print (result.content)
        print (chat_map['id_123'].messages)
        return result.content
    except Exception as e:
        return f"Error: {str(e)}"
    
class ConversationSummaryMessageHistory(BaseChatMessageHistory, BaseModel):
    messages: list[BaseMessage] = Field(default_factory=list)
    llm: ChatOpenAI = Field(default_factory=ChatOpenAI)

    def __init__(self, llm: ChatOpenAI):
        super().__init__(llm=llm)

    def add_messages(self, messages: list[BaseMessage]) -> None:
        """Add messages to history and remove any messages beyond last 'k' messages"""
        self.messages.extend(messages)
        summary_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                "Given the existing conversation summary and the new messages, generate a new summary of the conversation. Make sure to maintain as much relevant information as possible"
            ),
            HumanMessagePromptTemplate.from_template(
                "Existing Conversation summary: \n{existing_summary}\n New messages: {messages}"
            )
        ])
        new_summary = self.llm.invoke(
            summary_prompt.format_messages(
                existing_summary=self.messages,
                messages=[x.content for x in messages]
            )
        )

        self.messages = [SystemMessage(content=new_summary.content)]
    
    def clear(self) -> None:
        """Clear History"""
        self.messages = []

chat_map = {}
def get_chat_history(session_id: str, llm: ChatOpenAI) -> ConversationSummaryMessageHistory:
    if session_id not in chat_map:
        chat_map[session_id] = ConversationSummaryMessageHistory(llm=llm)
    return chat_map[session_id]

pipeline = prompt | llm

pipeline_with_history = RunnableWithMessageHistory(
    pipeline,
    get_session_history=get_chat_history,
    input_messages_key='query',
    history_messages_key='history',
    history_factory_config=[
        ConfigurableFieldSpec(
            id='session_id',
            annotation=str,
            name="Session ID",
            description="Session ID to use for chat history",
            default='id_default',
        ),
        ConfigurableFieldSpec(
            id='llm',
            annotation=ChatOpenAI,
            name='LLM',
            description='LLM to use for conversation summary',
            default=llm,
        )
    ]
)

