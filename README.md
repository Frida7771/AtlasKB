## Knowledge Base – LLM-powered KB & Chat (FastAPI + OpenAI + Elasticsearch)

This project is an LLM-powered knowledge base and chat backend built with **Python (FastAPI)**, **OpenAI**, and **Elasticsearch**.

It supports:

- Authenticated users chatting with an AI assistant for **interview preparation**.
- Persisting each Q&A into topic-specific knowledge bases.
- Vectorizing all **answers** and storing them into Elasticsearch for semantic reuse.
- A separate **semantic search** API that retrieves similar historical answers via cosine similarity on embeddings (without feeding them back to the model).



## Tech Stack

- **Backend**
  - Python / FastAPI
  - Elasticsearch 8.x
  - OpenAI Python SDK (chat & embeddings)
  - JWT auth, bcrypt password hashing
- **Infra**
  - Docker Compose for Elasticsearch + Kibana
  - `.env`-based configuration

---

## Getting Started

### 1. Prerequisites

- Python 3.10+  
- Docker Desktop  
- An OpenAI API key

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
JWT_SECRET=kb-secret-change-this
OPENAI_API_KEY=sk-xxx
ELASTICSEARCH_URL=http://127.0.0.1:9200
```

### 4. Start Elasticsearch (and Kibana)

```bash
cd deploy
docker-compose up -d
cd ..
```

### 5. Run the FastAPI backend

```bash
python main.py
```

API docs:

- Swagger UI: `http://localhost:8000/swagger-ui`
- ReDoc: `http://localhost:8000/redoc`

---

## Core Features

### 1. Auth & Users

- **Login** – `POST /api/v1/login`
  - Request: `{"username": "...", "password": "..."}`  
  - Response: `{"code": 200, "data": { "token": "<JWT>" }}`
- **Password change** – `POST /api/v1/password/modify` (JWT required)

Passwords are stored using **bcrypt**. Old plaintext passwords are still supported and migrated on change/reset.

All protected APIs require:

```http
Authorization: Bearer <token>
```

### 2. Knowledge Bases

- **Create KB** – `POST /api/v1/kb`
- **List KBs** – `GET /api/v1/kb/list`
- **Update / Delete KB** – `PUT /api/v1/kb/{kb_uuid}`, `DELETE /api/v1/kb/{kb_uuid}`

Data is stored in:

- `kb_index` – knowledge base metadata
- `kb_doc_index` – Q&A text
- `kb_doc_embed_index` – answer embeddings (`dense_vector`)

### 3. Q&A (Chat with AI + Persist + Embeddings)

- **Ask a question in a KB** – `POST /api/v1/kb/{kb_uuid}/qa`
  - Behavior:
    - Sends only the question to OpenAI.
    - Saves `"Q: ...\n\nA: ..."` to `kb_doc_index`.
    - Generates an embedding for the **answer** and writes it to `kb_doc_embed_index`.
  - Returns:
    ```json
    { "answer": "...", "context": [] }
    ```
    (`context` is intentionally empty; retrieved content is not fed back to the model.)

### 4. Chat (Per-user conversations)

- **Create chat** – `POST /api/v1/chat`
- **Send message** – `POST /api/v1/chat/{chat_uuid}/message`
- **List chats** – `GET /api/v1/chat/list`
- **List messages** – `GET /api/v1/chat/{chat_uuid}/messages`

If a chat is bound to a `kb_uuid`, every Q&A round is also saved via `save_qa_to_kb`:

- Q&A text → `kb_doc_index`
- Answer embedding → `kb_doc_embed_index`

### 5. Semantic Search (Vector-based)

- **Endpoint** – `POST /api/v1/kb/{kb_uuid}/semantic-search`
  - Request:
    ```json
    { "query": "Java concurrent hashmap interview question", "top_k": 5 }
    ```
  - Implementation:
    - Encodes `query` with OpenAI embeddings.
    - Retrieves all vectors for that `kb_uuid` from `kb_doc_embed_index`.
    - Computes cosine similarity in Python.
    - Returns Top-K chunks and scores:
      ```json
      {
        "code": 200,
        "data": [
          {
            "kb_uuid": "...",
            "doc_uuid": "...",
            "chunk": "answer text ...",
            "score": 0.80
          }
        ]
      }
      ```
  - This endpoint **does not call OpenAI**; it only reuses stored embeddings.

---



## Notes

- This project focuses on **storing and reusing** LLM answers, not full RAG prompting.
- Vector dimension currently matches OpenAI `text-embedding-ada-002` (1536 dims).
- Keep `.env` and your OpenAI key private; `.env` is Git-ignored by default.
