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
    if mode == "short":
        return f"Give a concise 2-sentence summary: {q}"
    
    # THE MATH/ENGINEERING PROMPT
    elif mode == "exam":
        return f"""
        You are an expert Engineering Professor. 
        If the question involves Math or Logic:
        1. List the given values.
        2. State the formula to be used.
        3. Show step-by-step substitution.
        4. Bold the final answer.
        
        If the question is theoretical:
        - Use structured bullet points.
        - Use professional language.
        
        Question: {q}
        """
    else:
        return f"Explain this like we are grabbing a coffee together, very simple: {q}"

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