// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');
const loadingIndicator = document.getElementById('loadingIndicator');

// Initialize the chatbot
async function initializeChatbot() {
    // Check backend health on startup
    const backendHealthy = await checkBackendHealth();
    
    if (!backendHealthy) {
        // Add a system message about backend status
        addMessage("⚠️ Backend server is not responding. Please make sure the FastAPI server is running on localhost:8000", 'bot');
    }
    
    // Auto-resize textarea
    userInput.addEventListener('input', autoResizeTextarea);
    
    // Send message on Enter (but allow Shift+Enter for new lines)
    userInput.addEventListener('keydown', handleKeyDown);
    
    // Send message on button click
    sendButton.addEventListener('click', sendMessage);
    
    // Focus on input when page loads
    userInput.focus();
}

// Auto-resize textarea based on content
function autoResizeTextarea() {
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 120) + 'px';
}

// Handle keyboard events
function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// Send user message
function sendMessage() {
    const message = userInput.value.trim();
    
    if (message === '') return; // Function ends early if nothing in text box (prevents from sending)
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Clear input
    userInput.value = '';
    autoResizeTextarea();
    
    // Show loading indicator
    showLoading();
    

    setTimeout(async () => {
        await generateAIResponse(message);
        hideLoading();
    }, 500 + Math.random() * 1000); // Random delay between 0.5-1.5 seconds 
}

// Add message to chat
function addMessage(message, sender) {
    const messageElement = document.createElement('div');
    messageElement.className = `message ${sender}-message`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = sender === 'user' ? '👤' : '🤖';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const paragraph = document.createElement('p');
    paragraph.textContent = message;
    content.appendChild(paragraph);
    
    messageElement.appendChild(avatar);
    messageElement.appendChild(content);
    
    chatMessages.appendChild(messageElement);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}


// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// Generate AI response by calling the FastAPI backend
async function generateAIResponse(userMessage) {
    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json', // Sets content type to JSON
            },
            body: JSON.stringify({ // Converts JS object to JSON with userMessage variable and timestamp
                message: userMessage,
                timestamp: new Date().toISOString()
            })
        });

        if (!response.ok) { // true for 200-299 HTTP Statuses (success)
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json(); // parses JSON in JS object
        addMessage(data.response, 'bot'); // get response part of ChatResponse Pydantic class 
        
        // Optional: Log processing time for debugging
        console.log(`Response generated in ${data.processing_time}s`);
        
    } catch (error) {
        console.error('Error calling AI API:', error);
        
        // Fallback to local response if API is unavailable
        const fallbackResponse = "I'm sorry, but I'm having trouble connecting to my brain right now. Please try again in a moment, or check if the backend server is running.";
        addMessage(fallbackResponse, 'bot');
    }
}

// Health check function to verify backend connection
async function checkBackendHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
            console.log('✅ Backend connection established');
            return true;
        }
    } catch (error) {
        console.warn('⚠️ Backend not available:', error.message);
        return false;
    }
    return false;
}


// Show loading indicator
function showLoading() {
    loadingIndicator.classList.add('active');
    sendButton.disabled = true;
}

// Hide loading indicator
function hideLoading() {
    loadingIndicator.classList.remove('active');
    sendButton.disabled = false;
}

// Add some visual feedback for button interactions
sendButton.addEventListener('mouseenter', () => {
    if (!sendButton.disabled) {
        sendButton.style.transform = 'scale(1.1)';
    }
});

sendButton.addEventListener('mouseleave', () => {
    if (!sendButton.disabled) {
        sendButton.style.transform = 'scale(1)';
    }
});

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeChatbot); // run first function when DOM loads that initializes Chatbot
