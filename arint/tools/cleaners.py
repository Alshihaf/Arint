# tools/cleaners.py
import re
import urllib.request

def abstract_knowledge(text):
    """Abstraksi & Generalisasi: Mengambil inti sari teks."""
    sentences = re.split(r'[.!?]', text)
    sentences = [s.strip() for s in sentences if len(s) > 25]
    keywords = ["ai", "system", "control", "knowledge", "logic", "autonomous"]
    scored = [(s, sum(s.lower().count(k) for k in keywords)) for s in sentences]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [s[0] for s in scored[:5]]

def find_patterns(contents):
    """Pattern Recognition: Deteksi ide yang berulang."""
    word_count = {}
    for content in contents:
        words = re.findall(r'\w+', content.lower())
        for w in words:
            if len(w) > 4:
                word_count[w] = word_count.get(w, 0) + 1
    return sorted(word_count.items(), key=lambda x: x[1], reverse=True)[:15]

def prioritize_content(snippets, keywords):
    """Strategic Knowledge: Memilih data dengan dampak tertinggi."""
    scored = []
    for s in snippets:
        score = sum(s.lower().count(k) for k in keywords)
        scored.append((s, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [s for s, _ in scored[:3]]

def fetch_url(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'CyberGod/6.0'})
        with urllib.request.urlopen(req, timeout=10) as res:
            return res.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return f"Error: {e}"