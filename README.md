# 🚀 AI ServiceNow Developer Agent

An AI-powered developer assistant that converts natural language into deployable ServiceNow scripts using RAG and multi-LLM routing.

---

## ✨ Features

- 🔹 Natural language → ServiceNow scripts
- 🔹 RAG (Retrieval Augmented Generation)
- 🔹 Multi-LLM support (OpenAI, Gemini, Claude)
- 🔹 API key rotation
- 🔹 Script validation
- 🔹 Automated deployment to ServiceNow

---

## 🏗 Architecture

User Input → RAG → LLM Router → Script Generation → Validation → Deployment

---

## 🧰 Tech Stack

- Python
- Streamlit
- Qdrant
- OpenAI / Gemini / Claude APIs
- ServiceNow REST API

---

## ⚙️ Setup

```bash
git clone <repo>
cd snow-dev-agent
pip install -r requirements.txt