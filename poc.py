"""
poc.py — UPSC Gap Radar, terminal version (web app ke alawa).

Web app ke liye:  python app.py   (browser/phone pe)
Terminal test ke liye:  python poc.py   ya   python poc.py --news data/news_sample.txt

Ye engine.py (retrieval) aur llm.py (Groq/Gemini) ko hi use karta hai.
"""

import os
import sys
import argparse

import engine
import llm

DEFAULT_NEWS = os.path.join(engine.DATA_DIR, "news_sample.txt")


def hr(c="="):
    print(c * 70)


def main():
    ap = argparse.ArgumentParser(description="UPSC Gap Radar POC (terminal)")
    ap.add_argument("--news", default=DEFAULT_NEWS, help="news text file ka path")
    args = ap.parse_args()

    if not os.path.exists(args.news):
        print(f"News file nahi mili: {args.news}")
        sys.exit(1)

    with open(args.news, encoding="utf-8") as f:
        news = f.read().strip()

    topic, tscore = engine.match_topic(news)
    pyqs = engine.match_pyqs(news, top_k=3)

    hr(); print("NEWS:"); hr("-"); print(news); print()
    hr(); print(f"MAPPED TOPIC (score {tscore}):"); hr("-"); print(" ", topic); print()
    hr(); print("SIMILAR PYQs (proof):"); hr("-")
    for r in pyqs:
        print(f"  [{r['year']}] ({r['topic']}, score {r['similarity']})")
        print(f"     {r['question']}\n")

    hr(); print("AI STUDY CARD (raw JSON):"); hr("-")
    prompt = engine.build_prompt(news, topic)
    text, provider = llm.generate(prompt)
    if text is None:
        text = ("(Koi LLM key nahi mili. .env me GROQ_API_KEY ya GEMINI_API_KEY "
                "daalo. Retrieval part upar phir bhi sahi chala hai.)")
    print(f"[provider: {provider}]\n")
    print(text)
    print(); hr()


if __name__ == "__main__":
    main()
