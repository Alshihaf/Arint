# tools/summarizer.py
import os
import json
import re
import hashlib
import nltk
import time
from pathlib import Path
from typing import Optional, Dict, List, Any
import random

try:
    from langdetect import detect
except ImportError:
    def detect(text):
        return 'en'
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)
from nltk.tokenize import sent_tokenize

class Summarizer:

    def __init__(self, use_llm: bool = True, llm_tool=None):
        self.use_llm = use_llm
        self.llm = llm_tool
        self.summary_dir = Path("memory/summaries")
        self.summary_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.summary_dir / "index.json"
        self.index = self._load_index()

    def _load_index(self) -> Dict:
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_index(self):
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)

    def clean_text(self, text: str) -> str:
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'[^\x20-\x7E\n\r\t]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def detect_language(self, text: str) -> str:
        try:
            return detect(text)
        except:
            return 'en'

    def translate_to_english(self, text: str, source_lang: str) -> str:
        if not self.llm or source_lang == 'en':
            return text
        prompt = f"Translate the following text from {source_lang} to English:\n\n{text[:2000]}"
        try:
            translation = self.llm.ask(prompt)
            return translation
        except:
            return text

    def extractive_summary(self, text: str, max_sentences: int = 5) -> Dict:
        sentences = sent_tokenize(text)
        if len(sentences) <= max_sentences:
            return {
                "summary": text,
                "key_points": sentences,
                "keywords": []
            }

        words = re.findall(r'\b\w+\b', text.lower())
        stopwords = set(['the', 'a', 'an', 'in', 'on', 'at', 'for', 'to', 'of', 'and', 'is', 'are'])
        word_freq = {}
        for w in words:
            if w not in stopwords and len(w) > 2:
                word_freq[w] = word_freq.get(w, 0) + 1

        sentence_scores = []
        for sent in sentences:
            score = 0
            for w in re.findall(r'\b\w+\b', sent.lower()):
                score += word_freq.get(w, 0)
            sentence_scores.append((sent, score))

        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        top_sentences = [s for s, _ in sentence_scores[:max_sentences]]
        top_sentences.sort(key=lambda s: sentences.index(s))

        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        keywords = [k for k, _ in keywords]

        return {
            "summary": " ".join(top_sentences),
            "key_points": top_sentences,
            "keywords": keywords
        }

    def abstractive_summary(self, text: str, max_length: int = 200) -> Dict:
        if not self.llm:
            return self.extractive_summary(text)

        prompt = f"""Summarize the following text in English. Provide:
1. A brief summary (max {max_length} words)
2. 3-5 key points
3. 5-10 keywords/tags

Format the output as JSON with keys: summary, key_points (list), keywords (list).

Text:
{text[:3000]}"""

        try:
            response = self.llm.ask(prompt)
            import json
            data = json.loads(response)
            if not isinstance(data.get('key_points'), list):
                data['key_points'] = [data.get('summary', '')]
            if not isinstance(data.get('keywords'), list):
                data['keywords'] = []
            return data
        except:
            return self.extractive_summary(text)

    def summarize(self, text: str, source: str, title: str = ""):
        cleaned = self.clean_text(text)
        if not cleaned:
            return {}

        lang = self.detect_language(cleaned)
        if lang != 'en':
            cleaned = self.translate_to_english(cleaned, lang)

        if self.use_llm:
            summary_data = self.abstractive_summary(cleaned)
        else:
            summary_data = self.extractive_summary(cleaned)

        summary_data['source'] = source
        summary_data['title'] = title or source
        summary_data['timestamp'] = time.time()
        summary_data['language'] = 'en'
        summary_data['word_count'] = len(cleaned.split())
        summary_data['id'] = hashlib.md5(f"{source}{time.time()}".encode()).hexdigest()[:16]

        filename = f"summary_{int(time.time())}_{summary_data['id']}.json"
        filepath = self.summary_dir / filename
        with open(filepath, 'w') as f:
            json.dump(summary_data, f, indent=2)

        self.index[summary_data['id']] = {
            "id": summary_data['id'],
            "title": summary_data['title'],
            "source": source,
            "timestamp": summary_data['timestamp'],
            "keywords": summary_data.get('keywords', [])
        }
        self._save_index()

        return summary_data

    def search(self, keyword: str) -> List[Dict]:
        results = []
        for sid, meta in self.index.items():
            if keyword.lower() in ' '.join(meta.get('keywords', [])).lower():
                results.append(meta)
        return results

    def get_summary(self, summary_id: str) -> Optional[Dict]:
        filepath = self.summary_dir / f"*{summary_id}.json"
        for f in self.summary_dir.glob("*.json"):
            if summary_id in f.name:
                with open(f, 'r') as fp:
                    return json.load(fp)
        return None