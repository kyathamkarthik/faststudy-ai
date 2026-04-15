from fastapi import FastAPI
from pydantic import BaseModel
import os
import json
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 🚀 CORS Setup - Crucial for connecting to your Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI Client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- DATA MODELS ---
class Query(BaseModel):
    question: str
    mode: str

class SaveHistory(BaseModel):
    user: str
    question: str
    answer: str

# --- DB HELPERS (JSON FILE) ---
DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# --- DYNAMIC PROMPT LOGIC ---
def build_prompt(q, mode):
    # 1. ⚡ SHORT MODE: The Speedster
    if mode == "short":
        return f"""
        You are a helpful, brief AI assistant. 
        Answer this question in 2-3 sentences max. 
        Be direct and avoid fluff. 
        Use \\( \\) for any technical terms.
        
        Question: {q}
        """
    
    # 2. 📐 MATH MODE: The LaTeX Professor
    elif mode == "math":
        return f"""
        You are an expert Math Professor.
        STRICT INSTRUCTIONS:
        1. Solve step-by-step clearly.
        2. Use LaTeX for ALL math: \\( inline \\) and \\[ block \\].
        3. Explain each step.
        4. Show the final answer clearly in a block.

        Question: {q}
        """
    
    # 3. 🛠️ ENGINEERING MODE: The Lead Architect
    elif mode == "engineering":
        return f"""
        You are a Senior Engineering Lead. 
        Break down the technical architecture, logic, or process of this topic.
        Use bullet points, technical terminology, and explain the "how" and "why".
        Use \\( \\) for variables or formulas.

        Question: {q}
        """
    
    # 4. 📚 NORMAL/EXPLAIN MODE: The Classmate (Default)
    else:
        return f"""
        You are a friendly, smart classmate. 
        Explain this concept in simple, conversational terms.
        Use analogies and don't be overly formal.
        
        Question: {q}
        """

# --- ENDPOINTS ---

@app.get("/")
def home():
    return {"message": "FastStudy AI Pro Backend is Live 🚀"}

# 🎯 TEXT GENERATION ENDPOINT
@app.post("/ask")
def ask_ai(query: Query):
    try:
        prompt = build_prompt(query.question, query.mode)
        
        # 🎯 ADAPTIVE TOKEN CONTROL
        if query.mode == "short":
            max_tokens = 300
        elif query.mode in ["math", "engineering"]:
            max_tokens = 900 
        else:
            max_tokens = 600

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens
        )

        answer = response.choices[0].message.content
        return {"answer": answer if answer else "No response"}

    except Exception as e:
        return {"answer": f"Error: {str(e)}"}

# 🎨 PREMIUM IMAGE GENERATION ENDPOINT (DALL-E 3)
@app.post("/generate-image")
def generate_image(query: Query):
    try:
        # Calling DALL-E 3 for high-quality images
        response = client.images.generate(
            model="dall-e-3",
            prompt=query.question,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        
        # Returning HTML string for the frontend to render directly
        return {
            "answer": f"🎨 <b>Premium AI Generation complete:</b><br><img src='{image_url}' style='width:100%; border-radius:15px; margin-top:10px; border: 1px solid #444;' alt='AI Generated Image'>"
        }
    except Exception as e:
        return {"answer": f"❌ Image Generation Failed: {str(e)}"}

# 📜 HISTORY ENDPOINTS
@app.post("/save")
def save_history(history: SaveHistory):
    data = load_data()
    user = history.user
    
    if user not in data:
        data[user] = []
        
    # Insert at the beginning so newest is on top
    data[user].insert(0, {"q": history.question, "ans": history.answer})
    save_data(data)
    return {"status": "saved"}

@app.get("/history/{user}")
def get_history(user: str):
    data = load_data()
    return data.get(user, [])