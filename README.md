 <div align="center">

## 💻 LaptopAI: Step-Aware Procedural QA using RAG

An intelligent Retrieval-Augmented Generation (RAG) system that provides accurate, source-grounded, and step-by-step troubleshooting assistance for laptop hardware and software issues. The system combines semantic retrieval, multi-query expansion, and cross-encoder reranking to minimize hallucinations and deliver reliable technical guidance.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Qdrant](https://img.shields.io/badge/Qdrant-DC244C?style=for-the-badge)
![HuggingFace](https://img.shields.io/badge/HuggingFace-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

</div>

---

## 📖 Overview

LaptopAI is a domain-specific Question Answering system designed to assist users in diagnosing and resolving laptop-related problems. Instead of relying solely on a Large Language Model, the system retrieves relevant repair guides from a structured knowledge base before generating responses. This retrieval-first approach improves factual accuracy and ensures every recommendation is grounded in trusted documentation. The project is built using FastAPI, Qdrant Vector Database, Hugging Face embedding models, and Docker, with a React-based frontend for interactive conversations. The overall architecture follows a modular design consisting of **Ingestion**, **Retrieval**, **Generation**, and **Memory** components. :contentReference[oaicite:0]{index=0}

---

## ✨ Key Features

- 🔍 Retrieval-Augmented Generation (RAG) for grounded responses
- 🧠 Multi-query expansion to improve semantic search recall
- 🎯 Cross-encoder reranking for higher retrieval precision
- 💬 Context-aware multi-turn conversations with session memory
- 📚 Source-cited, step-by-step troubleshooting guidance
- ⚡ FastAPI REST backend with React frontend
- 🗄️ Qdrant Vector Database for semantic document retrieval
- 🐳 Dockerized deployment for reproducibility

---

## 🏗️ Architecture

```text
User Query
    │
    ▼
FastAPI Backend
    │
Conversation Memory
    │
Multi-Query Generation
    │
BGE Embeddings
    │
Qdrant Vector Search
    │
Merge & Deduplicate
    │
Cross-Encoder Reranking
    │
Prompt Builder
    │
Llama 3.1
    │
Generated Answer
```

---

## 🛠️ Tech Stack

| Category | Technologies |
|-----------|--------------|
| Backend | Python, FastAPI |
| Frontend | React, Vite |
| Vector Database | Qdrant |
| Embeddings | BAAI BGE |
| LLM | Llama 3.1 |
| AI Pipeline | RAG, Multi-Query Retrieval, Cross-Encoder Reranking |
| Deployment | Docker, Docker Compose |

---

## 🚀 Highlights

- Built a modular **Retrieval-Augmented Generation** pipeline for laptop troubleshooting.
- Indexed structured repair guides using semantic vector embeddings.
- Implemented **multi-query retrieval** and **cross-encoder reranking** to improve search quality.
- Added conversation memory for context-aware follow-up responses.
- Dockerized the complete application for reproducible deployment.

---

## 📂 Project Structure

```text
LaptopAI/
├── backend/
│   ├── ingestion/
│   ├── retrieval/
│   ├── generation/
│   ├── memory/
│   └── api/
├── frontend/
├── data/
├── scripts/
├── docker/
└── README.md
```

---

## 📌 Future Improvements

- Step-level document chunking
- Redis-based persistent conversation memory
- Brand-aware retrieval using metadata filtering
- Multilingual retrieval with BGE-M3
- Automated evaluation using RAGAS
- Voice-enabled troubleshooting interface

---

## 👥 Contributors

- Aman Kakadiya
- Kashyap Dhameliya
- Mayank Satapara

---

## 📄 License

This project was developed as part of the **Natural Language Processing with Deep Learning** course at **IIIT Bangalore** for academic and research purposes.
