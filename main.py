
from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import fitz  # pymupdf
import anthropic
import os
import json
from datetime import datetime

app = FastAPI()

# Middleware para permitir llamadas desde cualquier origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo de entrada
class Question(BaseModel):
    question: str

# Cargar el contexto desde el PDF y el .md
try:
    with open("AIDRIANA_agent_context.md", "r", encoding="utf-8") as f:
        context_md = f.read()
except Exception as e:
    context_md = "⚠️ Error cargando el archivo .md: " + str(e)

try:
    doc = fitz.open("250609_CV_ENG_AdrianaCaballero.pdf")
    context_pdf = ""
    for page in doc:
        context_pdf += page.get_text()
    doc.close()
except Exception as e:
    context_pdf = "⚠️ Error cargando el CV PDF: " + str(e)

# Cliente de Claude
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

@app.post("/ask")
async def ask_agent(q: Question, request: Request):
    try:
        user_ip = request.client.host

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": f"""Responde la siguiente pregunta utilizando SOLO esta información profesional:

### CONTEXTO .MD
{context_md}

### CONTEXTO CV PDF
{context_pdf}

Pregunta: {q.question}
"""
                }
            ]
        )

        answer = response.content[0].text.strip()

        # Guardar pregunta en questions.json
        try:
            with open("questions.json", "r", encoding="utf-8") as f:
                previous = json.load(f)
        except Exception:
            previous = []

        previous.append({
            "timestamp": datetime.utcnow().isoformat(),
            "ip": user_ip,
            "question": q.question,
            "answer": answer,
            "category": "no_clasificada"
        })

        with open("questions.json", "w", encoding="utf-8") as f:
            json.dump(previous, f, indent=2, ensure_ascii=False)

        return {"answer": answer}
    except Exception as e:
        return {"error": f"❌ Error interno: {str(e)}"}

@app.get("/questions")
def get_questions(key: str):
    if key != "adriana2025!":
        return {"error": "⛔ Clave incorrecta"}

    try:
        with open("questions.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        return {"error": f"❌ No se pudieron cargar las preguntas: {str(e)}"}
