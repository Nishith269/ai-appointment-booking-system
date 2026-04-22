# 🤖 AI Appointment Booking Assistant

An intelligent full-stack appointment booking system that enables users to book, cancel, and manage appointments using natural language or structured UI.

Built using LLM-powered workflows with LangGraph, FastAPI backend, and a Streamlit frontend, with persistent storage via SQLite.


## 🚀 Features

* 💬 Natural language booking via chat interface
* ⚙️ Structured UI for quick actions (book/cancel/list)
* 🧠 Context-aware conversations (remembers user inputs across turns)
* 📅 Smart scheduling (30-minute slots, no past bookings)
* ❌ Conflict detection (prevents double booking)
* 🔄 Cancellation with confirmation flow
* 📊 Persistent database using SQLite + SQLAlchemy
* 🔍 Next available slot detection (only unbooked slots)


## 🏗️ Architecture

Frontend (Streamlit)
        ↓
FastAPI Backend (REST APIs)
        ↓
LangGraph Agent (LLM reasoning + tool routing)
        ↓
Tools Layer (Book / Cancel / List / Next Slot)
        ↓
SQLite Database (SQLAlchemy ORM)



## 🔄 How It Works

1. User interacts via Chat or Actions UI
2. Request is sent to FastAPI backend
3. LangGraph agent processes the request using LLM reasoning
4. Relevant tool is triggered:

   * Book appointment
   * Cancel appointment
   * List appointments
   * Get next available slot
5. Data is stored/retrieved from SQLite database
6. Response is returned to frontend


## ⚙️ Tech Stack

* **Frontend:** Streamlit
* **Backend:** FastAPI
* **LLM Orchestration:** LangGraph
* **LLM Provider:** Azure OpenAI (GPT-4o)
* **Database:** SQLite (SQLAlchemy ORM)
* **Language:** Python

## 📧 Email Notifications (Optional)

The system supports automatic email notifications for:

- ✅ Appointment confirmation (on booking)
- ❌ Appointment cancellation

Emails are sent using SMTP (Gmail App Password-based authentication).

### 🔒 Privacy Note

For security and privacy reasons, email functionality is **disabled by default**.

To enable it, configure the following environment variables:

EMAIL_USER=your_email@gmail.com  
EMAIL_PASS=your_app_password  

If these are not provided, the system will skip sending emails without affecting core functionality.


## ⚙️ Setup Instructions

### 1. Clone Repository


git clone https://github.com/YOUR_USERNAME/ai-appointment-booking-system.git
cd ai-appointment-booking-system


### 2. Install Dependencies


pip install -r requirements.txt


### 3. Setup Environment Variables

Create a .env file:

AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment
AZURE_OPENAI_API_VERSION=your_version


### 4. Run Backend

cd backend
uvicorn main:app --reload


### 5. Run Frontend

cd frontend
streamlit run app.py


## 🔮 Future Enhancements

* User authentication 
* Google Calendar integration
* Email/SMS reminders
* Cloud deployment 


## 📌 Key Highlights

* Combines LLM reasoning with structured APIs
* Demonstrates real-world AI system design
* Clean separation between UI, backend, and agent logic
* Implements stateful conversations using thread-based memory
