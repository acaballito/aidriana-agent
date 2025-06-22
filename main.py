from fastapi import FastAPI
from pydantic import BaseModel
import anthropic
import fitz

app = FastAPI()
client = anthropic.Anthropic()

# Cargar instrucciones del agente
with open("AIDRIANA_agent_context.md", "r", encoding="utf-8") as f:
    agent_instructions = f.read()

# Cargar contenido del CV en PDF
with fitz.open("250609_CV_ENG_AdrianaCaballero.pdf") as doc:
    cv_text = "".join(page.get_text() for page in doc)

# Combinar contexto completo
base_context = agent_instructions + "\n\n---\n\n" + cv_text

class UserInput(BaseModel):
    question: str

@app.post("/ask")
def ask_question(user_input: UserInput):
    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1024,
        system=base_context,
        messages=[{"role": "user", "content": user_input.question}]
    )

    # Registrar en archivo de log
    with open("aidriana_logs.txt", "a", encoding="utf-8") as log:
        log.write(f"\n\n---\nPREGUNTA: {user_input.question}\nRESPUESTA: {response.content[0].text}\n")

    return {"response": response.content[0].text}
