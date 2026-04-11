from fastapi import FastAPI
from pydantic import BaseModel
import os
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

def build_prompt(q, mode):
    if mode == "short":
        return f"Answer in 2-3 lines only: {q}"
    elif mode == "exam":
        return f"Give bullet points for exam: {q}"
    else:
        return f"Explain simply like a friend: {q}"

@app.get("/")
def home():
    return {"message": "FastStudy AI is running 🚀"}

@app.post("/ask")
def ask_ai(query: Query):
    try:
        prompt = build_prompt(query.question, query.mode)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120
        )

        answer = response.choices[0].message.content

        return {"answer": answer if answer else "No response"}

    except Exception as e:
        return {"answer": f"Error: {str(e)}"}