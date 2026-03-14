# AI Quiz Generator

This project is an AI-powered system that generates quiz questions from educational PDF files.

Users can upload a PDF containing study material, and the system extracts the text, generates questions using AI, and allows students to take a quiz with adaptive difficulty.

This project was built as part of the **Peblo AI Backend Engineer Challenge**.

---

# Features

- Upload educational PDFs
- Extract and process text from the uploaded document
- Automatically generate quiz questions using AI
- Supports multiple question formats:
  - MCQ (Multiple Choice Questions)
  - True/False
  - Fill in the blanks
- Store generated questions in a database
- Adaptive difficulty based on student performance
- Simple and interactive web interface for taking quizzes

---

# Technologies Used

## Backend
- Python
- FastAPI
- SQLAlchemy
- SQLite

## AI Integration
- Google Gemini API

## Frontend
- HTML
- CSS
- JavaScript

---

# Project Structure

peblo_quiz_engine/

app/
- app.py  
- database.py  
- models.py  
- pdf_ingestion.py  
- quiz_generator.py  

static/
- index.html  

requirements.txt  
README.md  
.env.example  

---

# Setup Instructions

## 1. Clone the Repository

git clone <[your-repo-link](https://github.com/shiprathi/AI-Quiz-Generator.git)>  
cd peblo_quiz_engine

---

## 2. Create Virtual Environment

python3 -m venv venv

Activate the environment:

Mac/Linux

source venv/bin/activate

Windows

venv\Scripts\activate

---

## 3. Install Dependencies

pip install -r requirements.txt

---

## 4. Add Environment Variables

Create a `.env` file in the root directory and add:

GEMINI_API_KEY=your_api_key_here  
DATABASE_URL=sqlite:///./quiz.db

---

## 5. Run the Server

python3 -m uvicorn app.app:app --reload

Open in browser:

http://127.0.0.1:8000

---

# API Endpoints

## Upload PDF

POST `/ingest`

Uploads a PDF file and extracts the text content for processing.

---

## Generate Quiz

POST `/generate-quiz`

Generates quiz questions from the extracted content using AI.

---

## Get Quiz

GET `/quiz`

Returns the generated quiz questions.

---

## Submit Answer

POST `/submit-answer`

Checks the student's answer and adjusts quiz difficulty.

---

# Adaptive Difficulty

The quiz adapts its difficulty based on the student's performance.

Correct answer → harder question  
Incorrect answer → easier question  

Difficulty levels:

easy → medium → hard

---

# Author

Shipra Rathi
