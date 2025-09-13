from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os, tempfile, uuid, shutil, json, datetime
from pathlib import Path
from typing import List, Dict, Any
import requests
from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-1")
USE_MOCK = os.getenv("USE_MOCK", "false").lower() in ("1","true","yes")

app = FastAPI(title="ResumeAI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Insight(BaseModel):
    type: str
    title: str
    description: str
    priority: str

class AnalysisResult(BaseModel):
    transcription: str
    summary: str
    insights: List[Insight]
    metadata: Dict[str, Any]

@app.get("/api/health")
async def health():
    return {"status":"ok","openai_configured": bool(OPENAI_API_KEY), "use_mock": USE_MOCK}

def _mock_process(file_path: str, filename: str):
    transcription = (
        "[00:00] João: Bom dia pessoal, vamos começar nossa reunião de planejamento estratégico.\n"
        "[00:15] Maria: Perfeito João. Primeiro item da pauta é a migração do CRM.\n"
        "[02:30] Carlos: Eu sugiro que façamos a migração até o final do trimestre.\n"
    )
    summary = (
        "**Reunião de Planejamento Estratégico**\n\n"
        "- Migração do CRM: prazo fim do trimestre; responsável: TI.\n"
        "- Orçamento de marketing aprovado: R$50.000.\n"
    )
    insights = [
        {"type":"action","title":"Implementar migração do CRM","description":"Equipe de TI iniciará o processo de migração.","priority":"high"},
        {"type":"decision","title":"Orçamento aprovado","description":"Budget de R$50.000 para marketing.","priority":"medium"}
    ]
    metadata = {
        "filename": filename,
        "duration": "00:15:30",
        "participants": "5",
        "processed_at": datetime.datetime.utcnow().isoformat() + "Z",
        "language": "pt-BR"
    }
    return {"transcription": transcription, "summary": summary, "insights": insights, "metadata": metadata}

def call_openai_transcription(file_path: str) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not configured")
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    with open(file_path, "rb") as f:
        files = {"file": (Path(file_path).name, f)}
        data = {"model": WHISPER_MODEL}
        resp = requests.post(url, headers=headers, data=data, files=files, timeout=180)
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        # surface error body if present
        detail = resp.text
        raise RuntimeError(f"OpenAI transcription error: {resp.status_code} {detail}")
    j = resp.json()
    text = j.get("text") or j.get("transcript") or j.get("data") or ""
    return text

def call_openai_summary_insights(transcription: str) -> Dict[str, Any]:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not configured")
    system = "Você é um assistente especialista em síntese de reuniões. Responda em português."
    user = f"""Analise a transcrição abaixo e retorne um JSON com 'summary' (string markdown) e 'insights' (lista de objetos com keys: type,title,description,priority).\nTRANSCRIÇÃO:\n""" + transcription
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role":"system","content": system},
            {"role":"user","content": user}
        ],
        "temperature": 0.2,
        "max_tokens": 1200
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        raise RuntimeError(f"OpenAI summarization error: {resp.status_code} {resp.text}")
    j = resp.json()
    choices = j.get("choices") or []
    if not choices:
        raise RuntimeError("No choices from OpenAI")
    text = choices[0].get("message", {}).get("content", "")
    # try parse JSON from response
    try:
        data = json.loads(text)
        return data
    except Exception:
        import re
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
    # fallback: return the text as summary
    return {"summary": text, "insights": []}

@app.post("/api/upload-audio", response_model=AnalysisResult)
async def upload_audio(file: UploadFile = File(...)):
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser um áudio válido")
    if not OPENAI_API_KEY and not USE_MOCK:
        raise HTTPException(status_code=503, detail="OpenAI API key not configured. Set OPENAI_API_KEY or enable USE_MOCK=true for development.")
    tmpdir = None
    try:
        tmpdir = tempfile.mkdtemp(prefix="resumeai_")
        filename = f"{uuid.uuid4().hex}_{file.filename}"
        tmp_path = os.path.join(tmpdir, filename)
        with open(tmp_path, "wb") as f:
            f.write(await file.read())

        if OPENAI_API_KEY:
            # transcription
            try:
                transcription = call_openai_transcription(tmp_path)
            except Exception as e:
                raise HTTPException(status_code=502, detail=str(e))

            # summary + insights
            try:
                out = call_openai_summary_insights(transcription)
                summary = out.get("summary", "")
                insights = out.get("insights", [])
                metadata = {"filename": file.filename, "duration": "estimado", "participants": "detectado automaticamente", "processed_at": datetime.datetime.utcnow().isoformat() + "Z"}
                return {"transcription": transcription, "summary": summary, "insights": insights, "metadata": metadata}
            except Exception as e:
                raise HTTPException(status_code=502, detail=str(e))

        # mock fallback
        return _mock_process(tmp_path, file.filename)
    finally:
        if tmpdir and os.path.exists(tmpdir):
            try:
                shutil.rmtree(tmpdir)
            except Exception:
                pass

# Serve static if build exists
frontend_dist = os.path.join(os.path.dirname(__file__), "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
