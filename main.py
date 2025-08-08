import time
import os
import sqlite3
import bcrypt

from fastapi import FastAPI, Form, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv

from chatbot import get_openai_response

app = FastAPI(title='OpenAI API Chatbot')
templates = Jinja2Templates(directory='templates')

app.mount('/static', StaticFiles(directory='static'), name='static')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL (which frontend origins can access API)
    allow_credentials=True,
    allow_methods=["*"], # access to all methods
    allow_headers=["*"],
)

load_dotenv()
open_api_key = os.getenv("OPENAI_API_KEY")

OPENAI_MODEL='gpt-4o-mini'
TEMPERATURE=0.7


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

    try:
        start_time = time.time()
        ai_response = await get_openai_response(user_message.message)

        processing_time = time.time() - start_time

        response = ChatResponse(
            response=ai_response,
            timestamp=get_current_timestamp(),
            process_time=round(processing_time, 3),
            model_used=OPENAI_MODEL
        )

        return response
    except Exception as e:
        return f"Error: {str(e)}"


    

