
<div align="center">

## 💻 LaptopAI: Step-Aware Procedural QA using RAG

An intelligent **Retrieval-Augmented Generation (RAG)** system for laptop diagnosis and repair. LaptopAI combines semantic search, multi-query retrieval, cross-encoder reranking, and LLM reasoning to generate accurate, source-grounded troubleshooting guidance.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Qdrant](https://img.shields.io/badge/Qdrant-DC244C?style=for-the-badge)
![HuggingFace](https://img.shields.io/badge/HuggingFace-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

</div>

---

## 📖 Overview

LaptopAI is a domain-specific AI assistant designed to help users diagnose and resolve laptop hardware and software issues through Retrieval-Augmented Generation (RAG). Unlike conventional LLM-based chatbots that rely only on pre-trained knowledge, LaptopAI first retrieves relevant repair documentation from a structured knowledge base before generating every response. This retrieval-first approach significantly reduces hallucinations while producing reliable, source-grounded, and step-by-step troubleshooting guidance.

The project is built around a modular architecture consisting of four major components: **Ingestion, Retrieval, Generation, and Conversation Memory**. Structured repair guides are transformed into semantic embeddings and stored inside **Qdrant**, enabling efficient vector search. User queries are expanded into multiple semantic variations, retrieved in parallel, reranked using a cross-encoder model, and finally passed to the language model to generate accurate answers. Session-aware memory allows the system to maintain conversational context across multiple troubleshooting steps.

Designed with scalability in mind, LaptopAI exposes REST APIs through **FastAPI**, provides an intuitive **React** frontend, and supports reproducible deployment using **Docker**. The modular architecture makes it easy to extend the system with additional datasets, multilingual support, persistent memory, and advanced retrieval techniques.

---

## ✨ Features

- 🔍 Retrieval-Augmented Generation (RAG)
- 🧠 Multi-query semantic retrieval
- 🎯 Cross-encoder reranking
- 💬 Context-aware multi-turn conversations
- 📚 Source-grounded troubleshooting responses
- ⚡ FastAPI REST APIs
- 🗄️ Qdrant Vector Database
- 🐳 Dockerized deployment
- 📈 Modular and scalable architecture
- 🔄 Easy knowledge-base updates

---

## 🏗️ System Architecture

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
              Llama 3.1 LLM
                     │
                     ▼
          Grounded Final Answer
```

---

## 🛠️ Tech Stack

| Category | Technologies |
|-----------|--------------|
| Backend | Python, FastAPI |
| Frontend | React, Vite |
| AI/LLM | Hugging Face, Llama 3.1 |
| Vector Database | Qdrant |
| Retrieval | BGE Embeddings, Cross-Encoder Reranker |
| Deployment | Docker, Docker Compose |

---

## 🚀 Engineering Highlights

- Implemented a **multi-stage retrieval pipeline** combining semantic embeddings, multi-query expansion, vector search, and cross-encoder reranking.
- Built a **context-aware conversational QA system** capable of maintaining previous troubleshooting history.
- Optimized indexing using **batched embedding generation**, deterministic UUID-based updates, and concurrent retrieval.
- Containerized the complete application for reproducible deployment and simplified development workflows.
- Followed a modular architecture separating ingestion, retrieval, generation, and memory components for maintainability.

---

## 📂 Project Structure

```text
LaptopAI/
│
├── backend/
│   ├── ingestion/
│   ├── retrieval/
│   ├── generation/
│   ├── memory/
│   └── api/
│
├── frontend/
│
├── data/
│
├── scripts/
│
├── docker/
│
└── README.md
```

---

## ⚙️ Getting Started

```bash
git clone <repository-url>
cd LaptopAI
docker compose up --build
```

Backend

```bash
cd backend
uvicorn app:app --reload
```

Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 🔮 Future Improvements

- Step-level document chunking
- Redis-based persistent conversation memory
- Brand-aware retrieval using metadata filtering
- Multilingual retrieval with BGE-M3
- Automated evaluation using RAGAS
- Voice-enabled troubleshooting

---

## 👥 Contributors

- Aman Kakadiya
- Kashyap Dhameliya
- Mayank Satapara

---

## 📄 License

Developed as part of the **Natural Language Processing with Deep Learning** course at **IIIT Bangalore** for academic and research purposes.
