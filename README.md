# ResumeAI 🎙️🤖

ResumeAI é uma aplicação **fullstack** que utiliza **Inteligência Artificial** para apoiar equipes em reuniões.  
A aplicação recebe arquivos de áudio, faz a **transcrição automática** (via **OpenAI Whisper**), gera **resumos estruturados** e entrega **insights acionáveis** a partir da conversa.  

Backend em **Python (FastAPI)** + Frontend em **React/Vite**.  
Suporte a **Docker** e deploy em **Render**, **Railway** ou **AWS**.  

---

## 📂 Estrutura do Projeto

```
resumeai_fullstack_app_env_ready/
│── docker-compose.yml   # Orquestração dos containers
│── Dockerfile           # Build da aplicação
│── backend/             # API de transcrição e insights (FastAPI)
│   │── main.py
│   │── requirements.txt
│   │── .env.example
│   └── ...
│── frontend/            # Interface web para upload de áudios e visualização dos resumos
│   │── package.json
│   └── ...
```

---

## ⚙️ Pré-requisitos

Antes de rodar o projeto localmente, instale:

- [Python 3.10+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/)
- [Docker](https://docs.docker.com/get-docker/) (opcional, para containerização)
- Conta e chave da [OpenAI API](https://platform.openai.com/)

---

## 🚀 Rodando Localmente

### 1. Clonar o repositório

```bash
git clone https://github.com/seu-usuario/resumeai.git
cd resumeai_fullstack_app_env_ready
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

A API ficará disponível em: [http://localhost:8000](http://localhost:8000)

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

O frontend ficará disponível em: [http://localhost:5173](http://localhost:5173)

---

## 🐳 Rodando com Docker

```bash
docker-compose up --build
```

Isso inicia tanto o **backend** quanto o **frontend** automaticamente.

---

## 🔑 Variáveis de Ambiente

Crie um arquivo `backend/.env` com:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
USE_MOCK=false
```

⚠️ **Não versionar este arquivo**. Use apenas localmente ou configure no provedor de deploy.

---

## 🌐 Deploy no Render

1. Crie um serviço **Web Service** para o **backend**.  
   - Build command:
     ```bash
     pip install -r backend/requirements.txt
     ```
   - Start command:
     ```bash
     uvicorn main:app --host 0.0.0.0 --port 8000
     ```

2. Crie um serviço **Static Site** para o **frontend**.  
   - Build command:
     ```bash
     cd frontend && npm install && npm run build
     ```
   - Public directory: `frontend/dist`

Adicione as variáveis de ambiente no painel do Render.

---

## 📜 Licença

Este projeto está sob a licença **MIT**.  
Sinta-se livre para usar, modificar e distribuir.
