from langchain_openai import ChatOpenAI
from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate, PromptTemplate
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper
from langchain_core.runnables import RunnableLambda
from skimage import io
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import os

load_dotenv()
open_api_key = os.getenv("OPENAI_API_KEY")

OPENAI_MODEL='gpt-4o-mini'

llm = ChatOpenAI(temperature=0.5, model=OPENAI_MODEL)


article = """
\
We believe AI's short—to mid-term future belongs to agents and that the long-term future of *AGI* may evolve from agentic systems. Our definition of agents covers any neuro-symbolic system in which we merge neural AI (such as an LLM) with semi-traditional software.

With agents, we allow LLMs to integrate with code — allowing AI to search the web, perform math, and essentially integrate into anything we can build with code. It should be clear the scope of use cases is phenomenal where AI can integrate with the broader world of software.

In this introduction to AI agents, we will cover the essential concepts that make them what they are and why that will make them the core of real-world AI in the years to come.

"""

# System Prompt: Instructions for how AI should act
system_prompt = SystemMessagePromptTemplate.from_template('You are an AI Assistant that helps generate article titles.')

# User prompt that takes article input variable (Will be article URL in future)
user_prompt = HumanMessagePromptTemplate.from_template(
    """You are tasked with creating a name for a article the article is here: {article}
    
    The name should be based on the context of the article. Be creative and make sure the names are clear, catchy, and relevatnt to the theme of the article.
    
    Only output the article name, no other explanation or text can be provided.""",
        input_variables=['article']
    )

image_prompt = PromptTemplate(
    input_variables=['article'],
    template=("""Generate a prompt with less than 1000 characters to generate an image based on the following user input: {article}.
              
    Make the prompt creative and interesting. Add artistic styles, mediums and color schemes centered around the input""")
)

# chat prompt template combines earlier messages and automatically reads input variables form each prompt
# Also prefixes each message input with their role (System for SystemPrompt, Human for HumanPrompt)
prompt = ChatPromptTemplate.from_messages([system_prompt, user_prompt]) 

def generate_and_display_image(image_prompt):
    image_url = DallEAPIWrapper(model='dall-e-3').run(image_prompt)
    return image_url
    """image_data = io.imread(image_url)

    plt.imshow(image_data)
    plt.axis('off')
    plt.show()"""

image_gen_runnable = RunnableLambda(generate_and_display_image)

chain = (
    {'article': lambda x: x['article']}
    | image_prompt
    | llm
    | (lambda x: x.content)
    | image_gen_runnable
)

result = chain.invoke({'article': article})

print(result)
print(type(result))