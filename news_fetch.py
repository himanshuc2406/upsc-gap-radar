"""
news_fetch.py — aaj ki news khud laata hai (PIB + The Hindu + Indian Express).

RSS feeds se headlines + chhota summary nikaalta hai. 15 min cache (baar-baar
fetch na ho). Koi feed fail ho to baaki chalte rehte hain (graceful).
"""

import re
import time
import html

import feedparser
import trafilatura

# Har source ke kai sections — taaki coverage zyada ho aur news miss na ho.
# (RSS sirf "aaj/abhi" ki window deta hai; asli app me roz fetch + store karke
#  poora capture hoga — abhi POC me jitna mil sake utna laate hain.)
FEEDS = [
    # PIB ka apna RSS sirf Hindi me hai, isliye English Google News se laate hain.
    ("PIB", "https://news.google.com/rss/search?q=site:pib.gov.in&hl=en-IN&gl=IN&ceid=IN:en"),

    ("The Hindu", "https://www.thehindu.com/news/national/feeder/default.rss"),
    ("The Hindu", "https://www.thehindu.com/business/Economy/feeder/default.rss"),
    ("The Hindu", "https://www.thehindu.com/sci-tech/feeder/default.rss"),
    ("The Hindu", "https://www.thehindu.com/news/international/feeder/default.rss"),

    ("Indian Express", "https://indianexpress.com/section/india/feed/"),
    ("Indian Express", "https://indianexpress.com/section/business/economy/feed/"),
    ("Indian Express", "https://indianexpress.com/section/explained/feed/"),
]

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36")

CACHE_TTL = 900  # 15 min
_cache = {"ts": 0.0, "items": []}


def _clean(text):
    """HTML tags hatao + entities decode karo."""
    text = re.sub(r"<[^>]+>", "", text or "")
    return html.unescape(text).strip()


def _parse_feed(source, url, limit=10):
    items = []
    try:
        d = feedparser.parse(url, agent=_UA)
        for e in d.entries[:limit]:
            title = _clean(e.get("title", ""))
            summary = _clean(e.get("summary", e.get("description", "")))
            if not title:
                continue
            items.append({
                "source": source,
                "title": title,
                "summary": summary[:600],
                "link": e.get("link", ""),
                "published": e.get("published", e.get("updated", "")),
            })
    except Exception:
        pass  # ek feed fail = chhodo, baaki chalein
    return items


def fetch_news(force=False, per_feed=10):
    now = time.time()
    if not force and _cache["items"] and (now - _cache["ts"] < CACHE_TTL):
        return _cache["items"]

    all_items = []
    for source, url in FEEDS:
        all_items.extend(_parse_feed(source, url, limit=per_feed))

    # title se dedupe
    seen, uniq = set(), []
    for it in all_items:
        key = it["title"].lower()
        if key and key not in seen:
            seen.add(key)
            uniq.append(it)

    _cache.update(ts=now, items=uniq)
    return uniq


_article_cache = {}  # url -> text


def fetch_article(url):
    """Article URL se poora text nikaalo (trafilatura). Na nikle to None.
    PIB ke Google News encoded links pe ye fail hoga -> None (frontend snippet
    pe fall back kar lega)."""
    if not url:
        return None
    if url in _article_cache:
        return _article_cache[url]
    text = None
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded, include_comments=False,
                                       include_tables=False)
    except Exception:
        text = None
    if text and len(text.strip()) < 200:  # itna chhota = theek se nahi nikla
        text = None
    _article_cache[url] = text
    return text
