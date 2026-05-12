# Codebase Q&A

Ever opened a big codebase and had no idea where anything is? This project fixes that.
You paste a GitHub repo link, it reads all the code, and then you can ask it questions like:

- "Where is authentication handled?"
- "What does the login function do?"
- "How is the database connected?"

And it replies with the actual answer + tells you exactly which file and which line the code is in.

Built this as a practice project to learn LangChain and how RAG (Retrieval Augmented Generation) works.

---

## How it actually works

So there are two main phases:

**Phase 1 — Indexing (when you paste a repo url)**

1. It clones the GitHub repo to your machine
2. Goes through every code file (Python, JS, Java, Go etc.)
3. For Python files it uses AST to split code at function and class boundaries — so each chunk is actually a complete function, not some random lines
4. For other files it uses LangChain's text splitter to break them into chunks
5. Each chunk gets converted into a vector (basically a list of numbers that represents the meaning of that code) using a model called `all-MiniLM-L6-v2`
6. All those vectors get stored in FAISS (an in-memory vector database)

**Phase 2 — Asking a question**

1. You type a question
2. Your question also gets converted into a vector
3. FAISS finds the code chunks whose vectors are closest to your question vector (this is the retrieval part)
4. Those chunks + your question get sent to Groq's free LLM (llama 3.1)
5. The LLM reads the code and writes an answer, mentioning exact file names and line numbers
6. Answer shows up in the chat with source references like `auth/middleware.py:42-67`

This whole approach is called RAG — instead of asking the LLM to memorize the whole codebase, we just fetch the relevant parts and show it only those. Way more accurate.

---

## What I used

- **FastAPI** — backend server, handles /index and /ask requests
- **Streamlit** — frontend chat UI
- **LangChain** — connects everything together (chunking, embeddings, prompt templates)
- **FAISS** — stores and searches code vectors, runs fully in memory, no setup needed
- **Groq** — free LLM API, using llama-3.1-8b model, super fast
- **sentence-transformers** — converts code into vectors using all-MiniLM-L6-v2
- **Docker** — containerizes everything so it runs on any machine
- **Github Actions** — deployed successfully
---

## Option 1 — Run with Docker (easiest, recommended)

No need to install Python or any dependencies. Just need Docker Desktop installed.

**Step 1 — Pull the images from Docker Hub**
```bash
docker pull ishaan0010/codebaseqa-backend:v2
docker pull ishaan0010/codebaseqa-frontend:v2
```

**Step 2 — Create a `.env` file** in whatever folder you are in and add your Groq key:
```
GROQ_API_KEY=your_key_here
```
Get a free key at https://console.groq.com (free).
**Step 3 — Download the docker-compose.yml** from this repo and run:
```bash
docker-compose up
```

That's it. Open `http://localhost:8501` in your browser.

---

## Option 2 — Run locally (for development)

**Step 1 — Clone the repo**
```bash
git clone https://github.com/Ishaangoyal0010/Codebase-Q-A
cd Codebase-Q-A
```

**Step 2 — Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate.bat     # windows
source venv/bin/activate      # mac/linux
```

**Step 3 — Install dependencies**
```bash
pip install -r requirements.txt
```

**Step 4 — Add your Groq API key**

Create a `.env` file in the root folder:
```
GROQ_API_KEY=your_key_here
```

**Step 5 — Run the backend** 
```bash
cd backend
uvicorn main:app --port 8000
```

**Step 6 — Run the frontend** (open a new terminal)
```bash
cd frontend
streamlit run app.py
```

Open `http://localhost:8501` and start using it.

---

## Project structure

```
codebase-qa/
├── backend/
│   ├── indexer.py      clones repo, chunks code, embeds and stores in FAISS
│   ├── retriever.py    takes a question, searches FAISS, returns relevant chunks
│   ├── llm.py          builds prompt using LangChain, calls Groq, returns answer
│   └── main.py         FastAPI app with /index and /ask endpoints
├── frontend/
│   └── app.py          Streamlit chat UI
├── docker-compose.yml
├── requirements.txt
├── .env                add your GROQ_API_KEY here
└── .dockerignore
```

---

## REMEMBER

FAISS runs in memory so if you restart the backend the index gets cleared and you'll need to re-index the repo. Good enough for a project though.