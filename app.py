"""
app.py — UPSC Gap Radar ka web app (Flask).

Phone/laptop browser pe chalega. ngrok se public bhi kar sakte ho.
Port: 5000, host: 0.0.0.0 (taaki phone/ngrok access kar sake).

Chalao:
    python app.py
Phir browser me:  http://localhost:5000   (ya phone se ngrok URL)
"""

import json
import re

from flask import Flask, render_template, request, jsonify

import engine
import llm
import news_fetch


def _parse_json(text):
    """LLM ke output me se JSON object nikaalo (code fences/extra text hatake)."""
    if not text:
        return None
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(text[start:end + 1])
    except Exception:
        return None

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/news")
def news():
    """Aaj ki headlines (PIB + The Hindu + Indian Express)."""
    force = request.args.get("refresh") == "1"
    items = news_fetch.fetch_news(force=force)
    return jsonify({"items": items, "count": len(items)})


@app.route("/article", methods=["POST"])
def article():
    """Ek news ka poora text (jahan se nikal sake)."""
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    text = news_fetch.fetch_article(url)
    return jsonify({"text": text, "ok": text is not None})


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}
    news = (data.get("news") or "").strip()
    if not news:
        return jsonify({"error": "News khali hai — kuch text daalo."}), 400

    topic, topic_score = engine.match_topic(news)
    pyqs = engine.match_pyqs(news, top_k=3)

    prompt = engine.build_prompt(news, topic)
    raw, provider = llm.generate(prompt)
    ai = _parse_json(raw)

    error = None
    if raw is None:
        error = ("Koi LLM key set nahi hai. .env me GROQ_API_KEY ya GEMINI_API_KEY "
                 "daalo. Topic + PYQ matching phir bhi chal raha hai.")
    elif ai is None:
        error = "AI ne theek JSON nahi diya. Niche raw output dikha raha hun."

    return jsonify({
        "topic": topic,
        "topic_score": topic_score,
        "pyqs": pyqs,
        "ai": ai,            # structured study card (ya null)
        "raw": raw,          # fallback ke liye
        "provider": provider,
        "error": error,
    })


if __name__ == "__main__":
    # host 0.0.0.0 -> phone/ngrok bhi access kar sakte hain
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
