# Codebase Q&A

ever opened a big codebase and had no idea where anything is? this project fixes that.
you paste a github repo link, it reads all the code, and then you can ask it questions like:

- "where is authentication handled?"
- "what does the login function do?"
- "how is the database connected?"

and it replies with the actual answer + tells you exactly which file and which line the code is in.

built this as a practice project to learn LangChain and how RAG (Retrieval Augmented Generation) works.

---

## how it actually works

so there are two main phases:

**phase 1 — indexing (when you paste a repo url)**

1. it clones the github repo to your machine
2. goes through every code file (python, js, java, go etc.)
3. for python files it uses AST to split code at function and class boundaries — so each chunk is actually a complete function, not some random lines
4. for other files it uses LangChain's text splitter to break them into chunks
5. each chunk gets converted into a vector (basically a list of numbers that represents the meaning of that code) using a model called `all-MiniLM-L6-v2`
6. all those vectors get stored in FAISS (an in-memory vector database)

**phase 2 — asking a question**

1. you type a question
2. your question also gets converted into a vector
3. FAISS finds the code chunks whose vectors are closest to your question vector (this is the retrieval part)
4. those chunks + your question get sent to Groq's free LLM (llama 3.1)
5. the LLM reads the code and writes an answer, mentioning exact file names and line numbers
6. answer shows up in the chat with source references like `auth/middleware.py:42-67`

this whole approach is called RAG — instead of asking the LLM to memorize the whole codebase, we just fetch the relevant parts and show it only those. way more accurate.

---

## what i used

- **FastAPI** — backend server, handles /index and /ask requests
- **Streamlit** — frontend chat UI
- **LangChain** — connects everything together (chunking, embeddings, prompt templates)
- **FAISS** — stores and searches code vectors, runs fully in memory, no setup needed
- **Groq** — free LLM API, using llama-3.1-8b model, super fast
- **sentence-transformers** — converts code into vectors using all-MiniLM-L6-v2
- **Docker** — containerizes everything so it runs on any machine

---

## how to run locally

**step 1 — clone the repo**
```bash
git clone https://github.com/your-username/codebase-qa
cd codebase-qa
```

**step 2 — create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate.bat     # windows
source venv/bin/activate      # mac/linux
```

**step 3 — install dependencies**
```bash
pip install -r requirements.txt
```
this will take a few minutes, lot of packages.

**step 4 — add your groq api key**

create a `.env` file in the root folder and paste this:
```
GROQ_API_KEY=your_key_here
```
get a free key at https://console.groq.com — takes 2 minutes, no credit card.

**step 5 — run the backend**
```bash
cd backend
uvicorn main:app --reload --port 8000
```
you can test it at `http://localhost:8000/docs` — FastAPI gives a free UI to try the endpoints.

**step 6 — run the frontend** (open a new terminal)
```bash
cd frontend
streamlit run app.py
```
open `http://localhost:8501` and start using it.

---

## how to run with docker

make sure Docker Desktop is running, then:
```bash
docker-compose up --build
```
frontend → `http://localhost:8501`
backend → `http://localhost:8000`

to push images to docker hub (replace with your username in docker-compose.yml first):
```bash
docker-compose build
docker-compose push
```

to run on any other computer after pushing:
```bash
docker-compose pull
docker-compose up
```

---

## project structure

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

## one thing to keep in mind

FAISS runs in memory so if you restart the backend the index gets cleared and you'll need to re-index the repo. good enough for a project though.