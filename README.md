## kb-frontend

Simple React + TypeScript frontend for the `knowledge-base` backend.

It provides two main pages:

- **Chat**
  - Paste a JWT token from `POST /api/v1/login`.
  - (Optional) Fill `KB UUID` to bind a knowledge base.
  - Send messages to the AI; the backend calls OpenAI and automatically stores Q&A and answer embeddings into Elasticsearch.

- **Semantic Search**
  - Paste the same JWT token and `KB UUID`.
  - Enter a natural-language query and `Top K`.
  - Calls `POST /api/v1/kb/{kb_uuid}/semantic-search` and shows the Top-K most similar historical answers (vector-based cosine similarity).

### Tech Stack

- React + TypeScript
- Vite
- Axios

### Run

```bash
cd kb-frontend
npm install
npm run dev
```

