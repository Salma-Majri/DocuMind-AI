# 📚 DocuMind AI — Intelligent Document Assistant

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://documind-ia-majrisalma.streamlit.app/)

**Try the live application:** https://documind-ia-majrisalma.streamlit.app/

DocuMind AI is an AI-powered document assistant that allows users to upload documents and ask questions about their content. It uses Retrieval-Augmented Generation (RAG) to retrieve relevant information and generate context-based answers with source references.

## ✨ Features

- 📂 Upload PDF, DOCX, TXT, and Markdown files.
- 🧠 Extract text and split documents into manageable chunks.
- 🔎 Search documents using semantic similarity.
- 🤖 Generate contextual answers using the Groq API.
- 📚 Display source references to help users verify answers.
- 📊 Track processed documents and indexed text chunks.
- 🎨 Enjoy a clean interface with a pastel blue-and-pink design.

## 🌐 Live Demo

Try DocuMind AI online:

👉 **[Launch DocuMind AI](https://documind-ia-majrisalma.streamlit.app/)**

## 🖥️ Screenshots

### 1. Dashboard

![DocuMind AI Dashboard](images/1.jpg)

### 2. Document Upload

![Document Upload](images/2.jpg)

### 3. Ask Your Documents

![Question Interface](images/3.jpg)

### 4. AI Answer and Sources

![Generated Answer and Sources](images/4.jpg)

## 🛠️ Technologies Used

- **Python** — Application logic
- **Streamlit** — Interactive web interface
- **RAG (Retrieval-Augmented Generation)** — Context-based question answering
- **Sentence Transformers** — Text embeddings
- **FAISS** — Similarity search
- **Groq API** — AI answer generation
- **Hugging Face** — Pre-trained embedding model
- **pypdf** — PDF text extraction
- **python-docx** — DOCX text extraction
- **NumPy** — Numerical operations

## ⚙️ How It Works

1. **Document Upload:** Users upload supported documents.
2. **Text Extraction:** The application extracts the document text.
3. **Text Splitting:** Text is divided into smaller chunks.
4. **Embedding Generation:** Sentence Transformers converts text chunks into embeddings.
5. **Semantic Search:** FAISS retrieves chunks relevant to the user's question.
6. **Answer Generation:** The retrieved context is sent to the Groq API.
7. **Source References:** The application displays available document and page references.

## 📁 Project Structure

```text
DocuMind-AI/
│
├── app/
│   ├── main.py
│   ├── document_loader.py
│   ├── text_splitter.py
│   ├── vector_store.py
│   └── rag_pipeline.py
│
├── images/
│   ├── 1.jpg
│   ├── 2.jpg
│   ├── 3.jpg
│   └── 4.jpg
│
├── .env.example
├── .gitignore
└── requirements.txt
```

## 🔐 Security

API keys and other secrets should be stored in environment variables or the deployment platform's secrets manager.

## 🧠 Architecture

DocuMind AI combines local document processing and semantic retrieval with cloud-based language generation. Embeddings and FAISS search run within the application's environment, while the Groq API generates answers from the retrieved context.

## 👩‍💻 Author

**Salma Majri**

