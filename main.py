from fastapi import FastAPI
from pydantic import BaseModel
import os
import json
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

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

# --- AI LOGIC ---
def build_prompt(q, mode):
    # 1. ⚡ SHORT MODE: Fast, direct, no fluff.
    if mode == "short":
        return f"""
        You are a helpful, brief AI assistant. 
        Answer this question in 2-3 sentences max. 
        Use \\( \\) for any technical terms or math.
        
        Question: {q}
        """
    
    # 2. 📚 EXAM MODE: The Professor (Math & LaTeX Heavy)
    elif mode == "math":
        return f"""
    You are an expert Math Professor.

    STRICT INSTRUCTIONS:
    1. Solve step-by-step clearly.
    2. Use proper LaTeX formatting:
       - Inline: \\( a^2 + b^2 = c^2 \\)
       - Block equations: \\[ c = \\sqrt{{a^2 + b^2}} \\]
    3. Put formulas on separate lines.
    4. Explain each step clearly.
    5. Show final answer clearly.

    Question: {q}
    """
    
    # 3. 😄 EXPLAIN MODE: The "Coffee" Friend (Normal Conversation)
    else:
        return f"""
        You are a friendly, smart classmate. 
        Explain this concept in simple, conversational terms like we're hanging out.
        Don't be overly formal. Use analogies.
        If there's math, keep it simple.
        
        Question: {q}
        """
    
    # --- ENDPOINTS ---
@app.get("/")
def home():
    return {"message": "FastStudy AI Persistence Layer Active 🚀"}

@app.post("/ask")
def ask_ai(query: Query):
    try:
        prompt = build_prompt(query.question, query.mode)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600
        )
        answer = response.choices[0].message.content
        return {"answer": answer if answer else "No response"}
    except Exception as e:
        return {"answer": f"Error: {str(e)}"}

@app.post("/save")
def save_history(history: SaveHistory):
    data = load_data()
    user = history.user
    
    if user not in data:
        data[user] = []
        
    data[user].insert(0, {"q": history.question, "ans": history.answer})
    save_data(data)
    return {"status": "saved"}

@app.get("/history/{user}")
def get_history(user: str):
    data = load_data()
    return data.get(user, [])