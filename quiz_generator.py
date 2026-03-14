import re
import random
import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

STOPWORDS = {
    "the", "is", "am", "are", "was", "were", "a", "an", "and", "or", "of", "to",
    "in", "on", "at", "for", "with", "by", "from", "as", "it", "this", "that",
    "these", "those", "be", "been", "being", "has", "have", "had", "do", "does",
    "did", "can", "could", "shall", "should", "will", "would", "may", "might",
    "must", "we", "you", "they", "he", "she", "i", "them", "his", "her", "their",
    "our", "your", "its", "into", "than", "then", "so", "because", "if", "but",
    "also", "very", "more", "most", "such", "many", "much", "any", "all", "some"
}


def clean_text(text: str) -> str:
    text = text.replace("\r", "\n")
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def split_sentences(text: str):
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def is_good_sentence(sentence: str):
    if len(sentence.split()) < 6:
        return False

    lower = sentence.lower()

    bad_patterns = [
        "answer:",
        "(mcq)",
        "true/false",
        "fill in the blank",
        "a.",
        "b.",
        "c.",
        "d."
    ]

    for p in bad_patterns:
        if p in lower:
            return False

    return True


def pick_keyword(sentence: str):
    words = re.findall(r"[A-Za-z][A-Za-z\-']+", sentence)

    candidates = []
    for w in words:
        wl = w.lower()
        if wl in STOPWORDS:
            continue
        if len(w) < 5:
            continue
        if w[0].islower():
            continue
        candidates.append(w)

    if not candidates:
        for w in words:
            wl = w.lower()
            if wl not in STOPWORDS and len(w) >= 5:
                candidates.append(w)

    if not candidates:
        return None

    return random.choice(candidates)


def extract_json_from_response(text: str):
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"^```\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except:
        pass

    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        possible_json = text[start:end + 1]
        try:
            return json.loads(possible_json)
        except:
            pass

    return []


def generate_questions_llm(text):
    prompt = f"""
You are an educational quiz generator.

From the following study material, generate exactly 3 high-quality quiz questions.

Rules:
- Focus only on meaningful learning concepts.
- Avoid headings like Chapter, Summary, Topic, Grade, Section titles.
- Do not create silly blanks from decorative text.
- Generate exactly:
  1 easy MCQ
  1 medium True-False
  1 hard Fill in the blank
- Keep the language simple and student-friendly.
- For MCQ, provide 4 meaningful options.
- For Fill in the blank, options must be an empty list.
- Return ONLY valid JSON.
- Do not add explanation before or after JSON.

Return format:
[
  {{
    "question": "...",
    "type": "MCQ",
    "options": ["...", "...", "...", "..."],
    "answer": "...",
    "difficulty": "easy"
  }},
  {{
    "question": "...",
    "type": "True-False",
    "options": ["True", "False"],
    "answer": "...",
    "difficulty": "medium"
  }},
  {{
    "question": "...",
    "type": "Fill in the blank",
    "options": [],
    "answer": "...",
    "difficulty": "hard"
  }}
]

STUDY MATERIAL:
{text[:2500]}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        print("RAW GEMINI RESPONSE:")
        print(response.text)

        questions = extract_json_from_response(response.text)

        valid_questions = []

        for q in questions:
            if not isinstance(q, dict):
                continue

            question = q.get("question", "").strip()
            qtype = q.get("type", "").strip()
            options = q.get("options", [])
            answer = q.get("answer", "").strip()
            difficulty = q.get("difficulty", "easy").strip().lower()

            if not question or not qtype or not answer:
                continue

            if qtype == "Fill in the blank":
                options = []

            if difficulty not in ["easy", "medium", "hard"]:
                difficulty = "easy"

            if qtype in ["MCQ", "True-False", "Fill in the blank"]:
                valid_questions.append({
                    "question": question,
                    "type": qtype,
                    "options": options,
                    "answer": answer,
                    "difficulty": difficulty
                })

        print("VALID LLM QUESTIONS:", len(valid_questions))
        return valid_questions

    except Exception as e:
        print("GEMINI ERROR:", e)
        return []


def generate_fill_blank_from_text(text: str, limit=5):
    questions = []
    seen = set()

    for sent in split_sentences(text):
        if not is_good_sentence(sent):
            continue

        keyword = pick_keyword(sent)
        if not keyword:
            continue

        pattern = r"\b" + re.escape(keyword) + r"\b"
        blanked = re.sub(pattern, "____", sent, count=1)

        if blanked == sent:
            continue
        if blanked in seen:
            continue

        seen.add(blanked)

        questions.append({
            "question": blanked,
            "type": "Fill in the blank",
            "options": [],
            "answer": keyword,
            "difficulty": "hard"
        })

        if len(questions) >= limit:
            break

    return questions


def generate_true_false_from_text(text: str, limit=3):
    questions = []
    seen = set()

    for sent in split_sentences(text):
        if not is_good_sentence(sent):
            continue

        if sent in seen:
            continue
        seen.add(sent)

        questions.append({
            "question": sent,
            "type": "True-False",
            "options": ["True", "False"],
            "answer": "True",
            "difficulty": "medium"
        })

        if len(questions) >= limit:
            break

    return questions


def parse_structured_questions(text: str):
    questions = []

    flat_text = text.replace("\n", " ")
    flat_text = re.sub(r"\s+", " ", flat_text).strip()

    blocks = re.split(r"\s(?=\d+\.\s)", flat_text)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        block = re.sub(r"^\d+\.\s*", "", block)

        mcq_pattern = re.compile(
            r"\(MCQ\)\s*(.*?)\s*A\.\s*(.*?)\s*B\.\s*(.*?)\s*C\.\s*(.*?)\s*D\.\s*(.*?)\s*Answer:\s*(.*?)(?=\s*\d+\.\s|$)",
            re.IGNORECASE
        )
        mcq_match = mcq_pattern.search(block)
        if mcq_match:
            questions.append({
                "question": mcq_match.group(1).strip(),
                "type": "MCQ",
                "options": [
                    mcq_match.group(2).strip(),
                    mcq_match.group(3).strip(),
                    mcq_match.group(4).strip(),
                    mcq_match.group(5).strip()
                ],
                "answer": mcq_match.group(6).strip(),
                "difficulty": "easy"
            })
            continue

        tf_pattern = re.compile(
            r"(?:\(True/False\)|True/False)\s*(.*?)\s*Answer:\s*(.*?)(?=\s*\d+\.\s|$)",
            re.IGNORECASE
        )
        tf_match = tf_pattern.search(block)
        if tf_match:
            questions.append({
                "question": tf_match.group(1).strip(),
                "type": "True-False",
                "options": ["True", "False"],
                "answer": tf_match.group(2).strip(),
                "difficulty": "medium"
            })
            continue

        fill_pattern = re.compile(
            r"(?:\(Fill\)\s*)?Fill in the blank:\s*(.*?)\s*Answer:\s*(.*?)(?=\s*\d+\.\s|$)",
            re.IGNORECASE
        )
        fill_match = fill_pattern.search(block)
        if fill_match:
            questions.append({
                "question": fill_match.group(1).strip(),
                "type": "Fill in the blank",
                "options": [],
                "answer": fill_match.group(2).strip(),
                "difficulty": "hard"
            })
            continue

    return questions


def parse_questions(text: str):
    text = clean_text(text)

    structured_questions = parse_structured_questions(text)
    if structured_questions:
        return structured_questions

    llm_questions = generate_questions_llm(text)
    if llm_questions:
        return llm_questions

    generated_questions = []

    fill_blank_questions = generate_fill_blank_from_text(text, limit=5)
    true_false_questions = generate_true_false_from_text(text, limit=3)

    generated_questions.extend(fill_blank_questions)
    generated_questions.extend(true_false_questions)

    return generated_questions