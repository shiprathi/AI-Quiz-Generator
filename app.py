from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import engine, SessionLocal
from . import models
from .models import ContentChunk, Question, StudentAnswer
from .pdf_ingestion import extract_text_from_pdf, chunk_text
from .quiz_generator import parse_questions
# create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Peblo Mini Quiz Engine",
    description="Backend system for ingesting PDFs and generating quizzes",
    version="1.0"
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.post("/ingest")
async def ingest_pdf(file: UploadFile = File(...)):
    file_path = f"temp_{file.filename}"

    with open(file_path, "wb") as f:
        f.write(await file.read())

    text = extract_text_from_pdf(file_path)
    chunks = chunk_text(text)

    db = SessionLocal()

    # optional: clear old chunks/questions for fresh run
    db.query(Question).delete()
    db.query(ContentChunk).delete()
    db.commit()

    for c in chunks:
        chunk = ContentChunk(
            source=file.filename,
            topic="general",
            text=c
        )
        db.add(chunk)

    db.commit()

    return {
        "message": "PDF processed successfully",
        "chunks_created": len(chunks)
    }


@app.post("/generate-quiz")
def generate_quiz():
    db = SessionLocal()
    chunks = db.query(ContentChunk).all()

    print("TOTAL CHUNKS FOUND:", len(chunks))

    db.query(StudentAnswer).delete()
    db.query(Question).delete()
    db.commit()

    created = 0

    for i, chunk in enumerate(chunks, start=1):
        print(f"\n--- CHUNK {i} START ---")
        print(chunk.text[:500])
        print("--- CHUNK END ---\n")

        parsed_questions = parse_questions(chunk.text)

        print("QUESTIONS GENERATED FROM THIS CHUNK:", len(parsed_questions))

        for q in parsed_questions:
            print("QUESTION:", q.get("question"))
            print("TYPE:", q.get("type"))
            print("ANSWER:", q.get("answer"))
            print("---")

            db.add(Question(
                question=q["question"],
                question_type=q["type"],
                options="|".join(q["options"]),
                answer=q["answer"],
                difficulty=q["difficulty"],
                chunk_id=chunk.id
            ))
            created += 1

    db.commit()

    print("TOTAL QUESTIONS SAVED:", created)

    return {
        "message": "Quiz generated successfully",
        "questions_created": created
    }


@app.get("/quiz")
def get_quiz():
    db = SessionLocal()
    questions = db.query(Question).all()

    result = []

    for q in questions:
        options_list = []
        if q.options and q.options.strip():
            options_list = [opt.strip() for opt in q.options.split("|") if opt.strip()]

        result.append({
            "id": q.id,
            "question": q.question,
            "type": q.question_type,
            "options": options_list,
            "answer": q.answer,
            "difficulty": q.difficulty
        })

    return result


@app.post("/submit-answer")
def submit_answer(question_id: int, selected: str):
    db = SessionLocal()

    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        return {"error": "Question not found"}

    correct = q.answer.strip().lower().replace(".", "") == selected.strip().lower().replace(".", "")


    db.add(StudentAnswer(
        question_id=question_id,
        user_answer=selected,
        correct=str(correct)
    ))
    db.commit()

    current_difficulty = q.difficulty.lower() if q.difficulty else "easy"

    if correct:
        if current_difficulty == "easy":
            next_difficulty = "medium"
        elif current_difficulty == "medium":
            next_difficulty = "hard"
        else:
            next_difficulty = "hard"
    else:
        if current_difficulty == "hard":
            next_difficulty = "medium"
        elif current_difficulty == "medium":
            next_difficulty = "easy"
        else:
            next_difficulty = "easy"

    return {
        "correct": correct,
        "correct_answer": q.answer,
        "current_difficulty": current_difficulty,
        "next_difficulty": next_difficulty
    }
