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

class Query(BaseModel):
    question: str
    mode: str

class SaveHistory(BaseModel):
    user: str
    question: str
    answer: str

DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE): return {}
    try:
        with open(DATA_FILE, "r") as f: return json.load(f)
    except: return {}

def save_data(data):
    try:
        with open(DATA_FILE, "w") as f: json.dump(data, f)
    except: pass

def build_prompt(q, mode):
    if mode == "short":
        return f"Briefly answer in 2 sentences. Use \\( \\) for math: {q}"
    elif mode == "math":
        return f"Math Professor. Solve step-by-step. Use LaTeX: \\( inline \\) and \\[ block \\]. Q: {q}"
    elif mode == "engineering":
        return f"Engineering Lead. Break down technical logic and architecture using bullet points and \\( \\). Q: {q}"
    else:
        return f"Smart classmate. Use simple analogies and conversational tone. Q: {q}"

@app.get("/")
def home():
    return {"message": "FastStudy Pro Backend Live 🚀"}

@app.post("/ask")
def ask_ai(query: Query):
    try:
        prompt = build_prompt(query.question, query.mode)
        tokens = 300 if query.mode == "short" else 900 if query.mode in ["math", "engineering"] else 600
        
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
            n=1
        )
        url = response.data[0].url
        return {"answer": f"🎨 <b>AI Image Complete:</b><br><img src='{url}' style='width:100%; border-radius:15px; margin-top:10px; border:1px solid #444;'>"}
    except Exception as e:
        return {"answer": f"❌ Generation Failed: {str(e)}"}

@app.post("/save")
def save_history(history: SaveHistory):
    data = load_data()
    user_name = history.user.strip()
    if user_name not in data: data[user_name] = []
    data[user_name].insert(0, {"q": history.question, "ans": history.answer})
    data[user_name] = data[user_name][:20]
    save_data(data)
    return {"status": "saved"}

@app.get("/history/{user}")
def get_history(user: str):
    data = load_data()
    return data.get(user.strip(), [])