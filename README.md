# 🏥 Medical RAG Chatbot

A sophisticated healthcare chatbot powered by Retrieval-Augmented Generation (RAG) technology, designed for medical professionals and patients. Features role-based authentication, OTP verification, and secure document management.

## ✨ Features

### 🔐 **Dual Authentication System**
- **General Users**: Simple registration for asking medical questions
- **Medical Professionals**: License verification + OTP authentication for document upload

### 📚 **Intelligent Document Processing**
- PDF upload and processing for medical documents
- Advanced text chunking and embedding generation
- FAISS-based vector search for accurate retrieval

### 💬 **Advanced Chat System**
- Session-based conversations with memory
- Context-aware responses using multiple LLM providers
- Citation tracking for source transparency

### 🔒 **Security Features**
- JWT-based authentication
- OTP verification via SMS (Twilio)
- Role-based access control
- Secure password hashing

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL
- Twilio account (for OTP)
- API keys for LLM providers (Groq/OpenAI/Gemini)

