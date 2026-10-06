"""
engine.py — UPSC Gap Radar ka "dimaag" (retrieval part).

Yahan data load hota hai aur news ko syllabus topic + sabse paas wale PYQs se
match karne ka logic hai. Ye OFFLINE chalta hai (TF-IDF, koi API/internet nahi).
Isko app.py (web) aur poc.py (terminal) dono use karte hain.
"""

import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")

PYQ_FILE = os.path.join(DATA_DIR, "pyqs.csv")
SYLLABUS_FILE = os.path.join(DATA_DIR, "syllabus.txt")


# --- data ek baar load karo (import hote hi) -------------------------------
def _load_syllabus():
    topics = []
    with open(SYLLABUS_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                topics.append(line)
    return topics


PYQ_DF = pd.read_csv(PYQ_FILE)
TOPICS = _load_syllabus()


# --- retrieval helpers -----------------------------------------------------
def _top_matches(news_text, candidate_texts, top_k):
    """candidate_texts me se news ke sabse paas wale top_k (index, score) do."""
    corpus = candidate_texts + [news_text]
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(corpus)
    scores = cosine_similarity(matrix[-1], matrix[:-1])[0]
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    return [(i, float(scores[i])) for i in ranked[:top_k]]


def match_topic(news_text):
    idx, score = _top_matches(news_text, TOPICS, top_k=1)[0]
    return TOPICS[idx], round(score, 3)


def match_pyqs(news_text, top_k=3):
    rows = []
    for idx, score in _top_matches(news_text, PYQ_DF["question"].tolist(), top_k):
        row = PYQ_DF.iloc[idx].to_dict()
        row["similarity"] = round(score, 3)
        rows.append(row)
    return rows


# --- prompt builder (LLM ke liye) ------------------------------------------
def build_prompt(news_text, topic):
    """LLM se ek STUDY CARD JSON mangte hain (summary, orgs, MCQ, Mains, etc.).
    Note: PYQ "proof" (kis saal aaya) hum retrieval se khud dikhate hain, isliye
    LLM ko saal banane ko nahi kehte (hallucination se bachne ke liye)."""
    return f"""You are a UPSC Civil Services exam mentor helping a beginner aspirant.

Read this current-affairs NEWS and the likely syllabus topic, then return a STUDY
CARD as a single valid JSON object and NOTHING ELSE (no markdown, no code fences).

NEWS:
{news_text}

LIKELY SYLLABUS TOPIC (from our system): {topic}

Return JSON with exactly these keys:
{{
  "summary": "3-4 line simple, exam-oriented summary of the news in clear English",
  "key_points": ["3 to 5 short crisp points an aspirant must remember"],
  "organisations": [
    {{"name": "name of any body/organisation/scheme/ministry/place mentioned",
      "info": "one-line: what it is and its role"}}
  ],
  "static_background": "1-2 lines on the static/background concepts this news connects to (what to revise)",
  "prelims_mcq": {{
    "question": "one UPSC-style Prelims MCQ based on this news",
    "options": ["(a) ...", "(b) ...", "(c) ...", "(d) ..."],
    "answer": "(x)",
    "explanation": "1-2 line explanation"
  }},
  "mains_question": "one 10-15 mark analytical UPSC Mains question on this theme"
}}

Rules: If no organisation is mentioned, use an empty array for "organisations".
Do NOT mention specific past exam years (our system handles that separately).
Keep everything concise and beginner-friendly. Output ONLY the JSON object."""
