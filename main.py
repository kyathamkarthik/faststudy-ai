from fastapi import FastAPI
from pydantic import BaseModel
import os
import json
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 🚀 CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- DATA MODELS ---
class Query(BaseModel):
    question: str
    mode: str

class SaveHistory(BaseModel):
    user: str
    question: str
    answer: str

# --- DB HELPERS ---
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
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error saving data: {e}")

# --- PROMPT LOGIC ---
def build_prompt(q, mode):
    if mode == "short":
        return f"Helpful, brief AI. 2-3 sentences max. Use \\( \\) for technical terms. Q: {q}"
    elif mode == "math":
        return f"Expert Math Professor. Solve step-by-step. Use LaTeX: \\( inline \\) and \\[ block \\]. Q: {q}"
    elif mode == "engineering":
        return f"Senior Engineering Lead. Technical architecture and logic. Use bullet points and \\( \\). Q: {q}"
    else:
        return f"Friendly, smart classmate. Simple, conversational terms and analogies. Q: {q}"

# --- ENDPOINTS ---

@app.get("/")
def home():
    return {"message": "FastStudy AI Pro Backend is Live 🚀"}

@app.post("/ask")
def ask_ai(query: Query):
    try:
        prompt = build_prompt(query.question, query.mode)
        
        # Adaptive Token Control
        if query.mode == "short":
            tokens = 300
        elif query.mode in ["math", "engineering"]:
            tokens = 900 
        else:
            tokens = 600

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=tokens
        )
        return {"answer": response.choices[0].message.content}
    except Exception as e:
        return {"answer": f"Error: {str(e)}"}

@app.post("/generate-image")
def generate_image(query: Query):
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=query.question,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        return {"answer": f"🎨 <b>Premium Generation:</b><br><img src='{image_url}' style='width:100%; border-radius:15px; margin-top:10px; border: 1px solid #444;'>"}
    except Exception as e:
        return {"answer": f"❌ Image Generation Failed: {str(e)}"}

@app.post("/save")
def save_history(history: SaveHistory):
    data = load_data()
    user_key = history.user.strip() # Clean the name
    
    if user_key not in data:
        data[user_key] = []
        
    data[user_key].insert(0, {"q": history.question, "ans": history.answer})
    
    # Keep only last 20 chats per user to save space
    data[user_key] = data[user_key][:20]
    
    save_data(data)
    return {"status": "saved"}

@app.get("/history/{user}")
def get_history(user: str):
    data = load_data()
    # Use .get() to avoid errors if user doesn't exist
    return data.get(user.strip(), [])