from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import fitz  # pymupdf
import anthropic
import os
import json

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
def ask_agent(q: Question):
    try:
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

        # Guardar la pregunta en questions.json
        try:
            with open("questions.json", "r", encoding="utf-8") as f:
                history = json.load(f)
        except:
            history = []

        history.append({"question": q.question, "answer": answer})

        with open("questions.json", "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

        return {"answer": answer}

    except Exception as e:
        return {"error": f"❌ Error interno: {str(e)}"}


# Ruta para acceder al historial de preguntas
@app.get("/questions")
def get_questions():
    try:
        with open("questions.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"error": f"❌ No se pudieron cargar las preguntas: {str(e)}"}
