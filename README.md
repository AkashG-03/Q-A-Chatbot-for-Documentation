# Medical RAG Chatbot

An AI-powered **Medical Question-Answering chatbot** built using **Retrieval-Augmented Generation (RAG)** to provide context-aware responses from uploaded medical documents.

The application combines document processing, semantic search, LLM-based generation, and secure role-based authentication into a full-stack healthcare-focused RAG system.

> **Note:** This project is an educational/prototype application and is not intended to provide medical diagnosis, treatment recommendations, or replace professional medical advice.

##  Features

###  Role-Based Authentication

- **General Users**
  - Register and securely log in
  - Ask questions through the chatbot
  - Maintain conversation sessions

- **Medical Professionals**
  - Professional role-based access
  - License verification
  - OTP-based authentication
  - Upload medical documents for knowledge-base creation

###  Intelligent Document Processing

- Upload medical PDF documents
- Extract text and tables from PDFs
- Split documents into meaningful chunks
- Generate semantic embeddings
- Store embeddings using **FAISS**
- Retrieve relevant document sections based on user queries

###  Retrieval-Augmented Generation

The chatbot follows a RAG pipeline:

```text
Medical PDF
    ↓
Text & Table Extraction
    ↓
Document Chunking
    ↓
Sentence Embeddings
    ↓
FAISS Vector Index
    ↓
User Question
    ↓
Semantic Retrieval
    ↓
Relevant Context
    ↓
LLM
    ↓
Context-Aware Answer
```

This approach allows the chatbot to generate responses based on the information retrieved from the uploaded documentation rather than relying only on the model's pretrained knowledge.

###  Advanced Chat System

- Session-based conversations
- Conversation history
- Context-aware question answering
- Multiple LLM provider support
- Source/citation tracking
- Role-specific interface and functionality

###  Security

- JWT-based authentication
- Password hashing
- OTP verification
- Role-based access control
- Secure authentication flow
- Environment-based configuration for API credentials

##  Tech Stack

### Backend
- Python
- FastAPI
- Uvicorn
- SQLAlchemy
- PostgreSQL

### RAG / AI
- Retrieval-Augmented Generation (RAG)
- Sentence Transformers
- `all-MiniLM-L6-v2`
- FAISS
- LLM APIs
- Semantic search

### Document Processing
- PDFPlumber
- PDF text extraction
- Table extraction
- Document chunking

### Authentication
- JWT
- Password hashing
- OTP verification
- Twilio

### Frontend
- HTML
- CSS
- JavaScript
- Jinja2 Templates

##  Project Structure

```text
Medical-RAG-Chatbot/
│
├── backend/
│   ├── main.py
│   ├── auth.py
│   ├── models.py
│   │
│   └── rag/
│       ├── embeddings.py
│       ├── ingest.py
│       ├── llm.py
│       ├── qa.py
│       ├── retrieve.py
│       ├── rerank.py
│       ├── store.py
│       └── utils.py
│
├── templates/
├── static/
│
├── tests/
│
├── requirements.txt
├── .gitignore
└── README.md
```

> The exact structure may vary depending on the current version of the project.

##  Prerequisites

Before running the application, make sure you have:

- Python 3.8+
- PostgreSQL
- A configured database
- Twilio account for OTP functionality
- API credentials for the selected LLM provider

##  Installation

### 1. Clone the repository

```bash
git clone https://github.com/AkashG-03/Q-A-Chatbot-for-Documentation.git
cd Q-A-Chatbot-for-Documentation
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root and add the required configuration:

```env
DATABASE_URL=your_postgresql_connection_string

JWT_SECRET_KEY=your_secret_key

TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

LLM_API_KEY=your_llm_api_key
```

> Never commit `.env` files or API keys to GitHub.

### 5. Start the application

Run the FastAPI application using:

```bash
uvicorn backend.main:app --reload
```

The application will be available locally at:

```text
http://127.0.0.1:8000
```

##  How the RAG Pipeline Works

1. A medical professional uploads a PDF document.
2. The system extracts text and relevant tables.
3. The extracted content is divided into smaller chunks.
4. Each chunk is converted into a numerical embedding using Sentence Transformers.
5. The embeddings are stored in a FAISS vector index.
6. A user submits a question.
7. The question is converted into an embedding.
8. FAISS retrieves the most relevant document chunks.
9. The retrieved context is passed to the configured LLM.
10. The LLM generates a response based on the retrieved information.

##  Security Considerations

The application implements several security mechanisms:

- JWT authentication for protected API endpoints
- Password hashing instead of storing plain-text passwords
- Role-based authorization
- OTP verification for professional users
- Environment variables for sensitive configuration
- Restricted document-upload functionality

For a production healthcare application, additional security, privacy, compliance, auditing, encryption, and clinical validation would be required.

##  Testing

The project includes testing for document processing and RAG-related functionality.

Example:

```bash
pytest
```

##  Future Enhancements

- Improve retrieval accuracy with advanced reranking
- Add document-level access controls
- Support additional document formats
- Improve citation and source highlighting
- Add conversation export functionality
- Implement stronger evaluation metrics for RAG responses
- Add automated RAG evaluation
- Deploy using Docker and cloud infrastructure
- Introduce monitoring and logging for production environments

##  Project Highlights

This project demonstrates practical experience with:

- Retrieval-Augmented Generation
- Large Language Model integration
- Vector databases and semantic search
- PDF and table processing
- FastAPI backend development
- PostgreSQL database integration
- JWT authentication
- Role-based authorization
- OTP-based verification
- Full-stack application development

##  Disclaimer

This application was developed as an educational/project prototype. The generated responses may contain inaccuracies and **must not be used as a substitute for professional medical diagnosis, treatment, or advice**.

## 📄 License

This project is intended for educational and portfolio purposes.
