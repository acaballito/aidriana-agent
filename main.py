
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

# Ruta para preguntas
@app.post("/ask")
def ask_agent(q: Question):
    try:
        # Guardar la pregunta en un archivo json por línea
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "question": q.question
        }
        with open("questions.json", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

        full_prompt = f"""{anthropic.HUMAN_PROMPT} Responde la siguiente pregunta utilizando SOLO esta información profesional:

### CONTEXTO .MD
{context_md}

### CONTEXTO CV PDF
{context_pdf}

Pregunta: {q.question}

{anthropic.AI_PROMPT}
"""
        response = client.completions.create(
            model="claude-3-sonnet-20240229",
            prompt=full_prompt,
            max_tokens_to_sample=500
        )
        return {"answer": response.completion.strip()}

    except Exception as e:
        return {"error": f"❌ Error interno: {str(e)}"}

# Ruta para consultar preguntas (protegida con clave)
@app.get("/questions")
def get_logged_questions(request: Request):
    key = request.query_params.get("key")
    if key != os.getenv("ADMIN_KEY"):
        return {"error": "🔒 Acceso denegado"}

    try:
        with open("questions.json", "r", encoding="utf-8") as f:
            lines = f.readlines()
            questions = [json.loads(line) for line in lines]
        return {"questions": questions}
    except Exception as e:
        return {"error": f"❌ No se pudieron cargar las preguntas: {str(e)}"}
