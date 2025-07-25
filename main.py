from fastapi import FastAPI, HTTPException, Form, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
import time
import os
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import uvicorn
import sqlite3
import bcrypt

app = FastAPI(title='OpenAI API Chatbot')
templates = Jinja2Templates(directory='templates')

app.mount('/static', StaticFiles(directory='static'), name='static')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL (which frontend origins can access API)
    allow_credentials=True,
    allow_methods=["*"], # access get, post, delete, put
    allow_headers=["*"],
)

load_dotenv()
open_api_key=os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=open_api_key)

OPENAI_MODEL='gpt-4o-mini'
MAX_TOKENS=500
TEMPERATURE=0.7
SYSTEM_PROMPT="""You are a helpful, friendly, and knowledgeable AI assistant. You provide accurate, helpful responses while maintaining a conversational and approachable tone. Keep your responses concise but informative. If you're unsure about something, admit it rather than guessing."""

class ChatMessage(BaseModel):
    message: str
    timestamp: Optional[str]

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    process_time: float
    model_used: str

def get_current_timestamp():
    return datetime.now().isoformat()

async def get_openai_response(user_message: str) -> str:

    try:
        messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
        messages.append({'role': 'user', 'content': user_message})

        response = client.responses.create(
            model=OPENAI_MODEL,
            input=messages,
            temperature=TEMPERATURE,
            max_output_tokens=MAX_TOKENS,
            timeout=30
        )

        ai_response = response.output_text

        return ai_response
    except Exception as e:
        print(f"OpenAI API Error: {str(e)}")
        return "I'm sorry, but I'm having trouble processing your request right now. Please try again in a moment."
    
@app.get('/', response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("login.html", {'request': request})


@app.get('/home', response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {'request': request})


@app.get('/signup', response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("signup.html", {'request': request})

@app.get('/login', response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("login.html", {'request': request})


@app.post('/login')
async def login(email: str = Form(), password: str = Form()):
    connection = sqlite3.connect('LoginData.db')
    cursor = connection.cursor()

    user = cursor.execute('SELECT password FROM USERS WHERE email=?', (email,)).fetchall()
    connection.close()

    if not user:
        return RedirectResponse(url='signup', status_code=status.HTTP_302_FOUND)

    hashed_password = user[0][0]
    print (hashed_password)

    if not bcrypt.checkpw(password.encode('utf-8'), hashed_password):
        return RedirectResponse(url='login', status_code=status.HTTP_302_FOUND)
    else:
        return RedirectResponse(url='/home', status_code=status.HTTP_302_FOUND) # standard HTTP redirect status (default is 307 which uses same method as current function which wont be allowed)


@app.post('/signup')
async def signup(first_name: str = Form(), last_name: str = Form(), email: str = Form(), password: str = Form()):
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    connection = sqlite3.connect('LoginData.db')
    cursor = connection.cursor()

    user = cursor.execute('SELECT * FROM USERS WHERE email=?', (email,)).fetchall() # comma must be added after email to indicate tuple not string

    if len(user) > 0:
        connection.close()
        return RedirectResponse(url='/login', status_code=status.HTTP_302_FOUND)
    else:
        cursor.execute('INSERT INTO USERS (first_name, last_name, email, password) values(?, ?, ?, ?)', (first_name, last_name, email, hashed_password))
        connection.commit()
        connection.close()
        return RedirectResponse(url='/home', status_code=status.HTTP_302_FOUND)



@app.get('/health')
async def check_health():
    
    api_status = 'configured' if open_api_key else 'missing'
    
    return {
        'status': 'Healthy',
        'timestamp': get_current_timestamp(),
        'openai': api_status
    }


@app.post('/chat', response_model = ChatResponse)
async def chat(user_message: ChatMessage):

    start_time=time.time()
    
    try:
        if not user_message.message or not user_message.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        ai_response = await get_openai_response(user_message.message)

        processing_time = time.time() - start_time

        response = ChatResponse(
            response=ai_response,
            timestamp=get_current_timestamp(),
            process_time=round(processing_time, 3),
            model_used=OPENAI_MODEL
        )

        return response
    
    except HTTPException:
        raise
    except Exception as e:
        # Log the error
        print(f"Chat endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your request")

