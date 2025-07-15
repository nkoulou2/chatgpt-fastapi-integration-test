from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import time
import os
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(title="AI Chatbot API", version="1.0.0")

# Configure CORS to allow frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=openai_api_key)

# Data models
class ChatMessage(BaseModel):
    message: str
    timestamp: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    processing_time: float
    model_used: str

class ConversationHistory(BaseModel):
    messages: List[dict]

# In-memory storage for conversation history (use database in production)
conversation_store = {}

# OpenAI Configuration
OPENAI_MODEL = "gpt-4o-mini" 
MAX_TOKENS = 500
TEMPERATURE = 0.7

# System prompt for the AI assistant
SYSTEM_PROMPT = """You are a helpful, friendly, and knowledgeable AI assistant. You provide accurate, helpful responses while maintaining a conversational and approachable tone. Keep your responses concise but informative. If you're unsure about something, admit it rather than guessing."""

# Utility functions
def get_current_timestamp():
    return datetime.now().isoformat()

# Get response from OpenAI ChatGPT API
async def get_openai_response(user_message: str, conversation_history: List[dict] = None) -> str: # conversation_history optional for now and can be implemented later, function expected to return string
    try:
        # Prepare messages for the API
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # Add conversation history if provided (optional feature)
        if conversation_history:
            for msg in conversation_history[-10:]:  # Keep last 10 messages for context
                messages.append(msg)
        
        # Add the current user message
        messages.append({"role": "user", "content": user_message})
        
        # Make API call to OpenAI
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            timeout=30  # 30 second timeout
        )
        
        # Extract the response
        ai_response = response.choices[0].message.content
        return ai_response
        
    except Exception as e:
        # Log error
        print(f"OpenAI API Error: {str(e)}")
        
        return "I'm sorry, but I'm having trouble processing your request right now. Please try again in a moment."

# API Routes
@app.get("/") # when accessing webpage
async def root(): # run this function 
    return {
        "message": "AI Chatbot API is running!", 
        "version": "1.0.0",
        "ai_model": OPENAI_MODEL
    }

@app.get("/health")
async def health_check():

    openai_status = "configured" if openai_api_key else "missing"

    return {
        "status": "healthy", # add if statement where status will only be health id db is up and running
        "timestamp": get_current_timestamp(), # confirming real time responses
        "openai": openai_status
    }

# Main chat endpoint that processes user messages and returns AI responses
@app.post("/chat", response_model=ChatResponse) # when new data is created at /chat endpoint
# when /chat endpoint returns data, it must match ChatResponse Pydantic model. FastAPI will validate and serialize the response so any wrong, extra, or ommitted data types and variables will not run 

async def chat(user_message: ChatMessage): # run function
    
    start_time = time.time() # calls time module and access time function within module to get current time and start of function
    
    try:
        # Validate input
        if not user_message.message or not user_message.message.strip(): # checks that message string in message variable from ChatMessage class is not empty or full of whitespace
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Get response from OpenAI (await assumes get_openai_response is also async)
        ai_response = await get_openai_response(user_message.message) # send message from message variable to get_openai_response function
        
        # Calculate processing time (good for observability and possible debugging)
        processing_time = time.time() - start_time
        
        # Create response (constructs Pydantic model response using variables in function)
        response = ChatResponse(
            response=ai_response,
            timestamp=get_current_timestamp(),
            processing_time=round(processing_time, 3),
            model_used=OPENAI_MODEL
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        # Log the error
        print(f"Chat endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your request")

# Chat endpoint that maintains conversation history for context
@app.post("/chat-with-history", response_model=ChatResponse)
async def chat_with_history(message: ChatMessage, session_id: str = "default"):

    start_time = time.time()
    
    try:
        # Validate input
        if not message.message or not message.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Get conversation history
        conversation_history = conversation_store.get(session_id, [])
        
        # Get response from OpenAI with context
        ai_response = await get_openai_response(message.message, conversation_history)
        
        # Update conversation history
        conversation_history.append({"role": "user", "content": message.message})
        conversation_history.append({"role": "assistant", "content": ai_response})
        conversation_store[session_id] = conversation_history
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Create response
        response = ChatResponse(
            response=ai_response,
            timestamp=get_current_timestamp(),
            processing_time=round(processing_time, 3),
            model_used=OPENAI_MODEL
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Chat with history endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your request")

# Get conversation history for a specific session
@app.get("/conversation/{session_id}")
async def get_conversation(session_id: str):
    if session_id not in conversation_store:
        return {"session_id": session_id, "messages": []}
    
    return {
        "session_id": session_id,
        "messages": conversation_store[session_id]
    }

# Save conversation history for a specific session
@app.post("/conversation/{session_id}")
async def save_conversation(session_id: str, conversation: ConversationHistory):
    conversation_store[session_id] = conversation.messages
    return {"status": "saved", "session_id": session_id, "message_count": len(conversation.messages)}

# Clear conversation history for a specific session
@app.delete("/conversation/{session_id}")
async def clear_conversation(session_id: str):
    if session_id in conversation_store:
        del conversation_store[session_id]
        return {"status": "cleared", "session_id": session_id}
    else:
        return {"status": "not_found", "session_id": session_id}


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Endpoint not found", "message": "The requested endpoint does not exist"}

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {"error": "Internal server error", "message": "An unexpected error occurred"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)