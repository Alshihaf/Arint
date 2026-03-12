#!/usr/bin/env python3
import re
import json
import yaml
import hashlib
import sqlite3
import logging
import unicodedata
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
from typing import Optional, Dict, Any, List, Tuple, Set, Union
from dataclasses import dataclass, asdict, field
from html import unescape
from functools import lru_cache
import math
import threading

# ----------------------------------------------------------------------
# Opsional dependencies dengan fallback internal
# ----------------------------------------------------------------------
try:
    from langdetect import detect as detect_lang
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    def detect_lang(text): return 'en'

try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    NLTK_AVAILABLE = True
    # Unduh data jika perlu
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)
    STOPWORDS = set(stopwords.words('english'))
except ImportError:
    NLTK_AVAILABLE = False
    # Fallback tokenizer sederhana dan stopwords minimal
    def sent_tokenize(text): return text.split('. ')
    def word_tokenize(text): return re.findall(r'\b\w+\b', text.lower())
    STOPWORDS = {'the', 'a', 'an', 'in', 'on', 'at', 'for', 'to', 'of', 'and', 'is', 'are', 'this', 'that'}

try:
    import spacy
    SPACY_AVAILABLE = True
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        # Download model kecil jika belum ada
        spacy.cli.download("en_core_web_sm")
        nlp = spacy.load("en_core_web_sm")
except ImportError:
    SPACY_AVAILABLE = False
    nlp = None

# ----------------------------------------------------------------------
# Data classes
# ----------------------------------------------------------------------
@dataclass
class ProcessedDocument:
    """Dokumen hasil proses."""
    id: str
    content: str
    summary: str
    key_points: List[str]
    keywords: List[str]
    source: str
    length: int
    quality: float
    type: str
    hash: str
    language: str
    original_language: str
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessedDocument':
        return cls(**data)

# ----------------------------------------------------------------------
# Konfigurasi
# ----------------------------------------------------------------------
class SeafilConfig:
    """Membaca konfigurasi dari file YAML/JSON dengan default cerdas."""
    DEFAULT = {
        'storage': {
            'db_path': 'memory/seafil.db',
            'raw_dir': 'memory/knowledge/raw',
            'clean_dir': 'memory/knowledge/clean',
        },
        'deduplication': {
            'enabled': True,
            'persistent': True,
        },
        'quality': {
            'min_words': 10,
            'min_unique_ratio': 0.4,
            'min_alpha_ratio': 0.6,
            'min_sentence_count': 2,
        },
        'language': {
            'target': 'en',
            'min_text_length_for_detection': 50,
        },
        'summarization': {
            'method': 'textrank',  # 'textrank', 'frequency', 'first_n'
            'max_sentences': 5,
            'ratio': 0.3,  # jika berdasarkan rasio
            'use_stopwords': True,
        },
        'keywords': {
            'method': 'tfidf',  # 'tfidf', 'rake', 'yake', 'frequency'
            'max_keywords': 15,
            'min_word_length': 3,
        },
        'classification': {
            'enabled': True,
        },
        'logging': {
            'level': 'INFO',
            'file': 'logs/seafil.log',
        }
    }

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        self.config = self.DEFAULT.copy()
        if config_path:
            self._load(config_path)
        self._setup_logging()

    def _load(self, path: Union[str, Path]):
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config {path} not found")
        with open(path, 'r') as f:
            if path.suffix in ('.yaml', '.yml'):
                user = yaml.safe_load(f)
            elif path.suffix == '.json':
                user = json.load(f)
            else:
                raise ValueError("Config must be YAML or JSON")
        self._deep_merge(self.config, user)

    def _deep_merge(self, base, update):
        for k, v in update.items():
            if isinstance(v, dict) and k in base and isinstance(base[k], dict):
                self._deep_merge(base[k], v)
            else:
                base[k] = v

    def _setup_logging(self):
        log_cfg = self.config['logging']
        level = getattr(logging, log_cfg['level'].upper(), logging.INFO)
        log_file = Path(log_cfg['file'])
        log_file.parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

    def get(self, *keys, default=None):
        val = self.config
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val

# ----------------------------------------------------------------------
# Storage Manager dengan SQLite
# ----------------------------------------------------------------------

class StorageManager:
    """Manajemen penyimpanan dokumen dan duplikasi."""
    def __init__(self, config: SeafilConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        db_path = Path(config.get('storage', 'db_path'))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.lock = threading.Lock()
        self._init_db()
        self.raw_dir = Path(config.get('storage', 'raw_dir'))
        self.clean_dir = Path(config.get('storage', 'clean_dir'))
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.clean_dir.mkdir(parents=True, exist_ok=True)

    def _init_db(self):
        with self.lock:
            cur = self.conn.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    hash TEXT UNIQUE,
                    source TEXT,
                    quality REAL,
                    type TEXT,
                    language TEXT,
                    timestamp TEXT,
                    file_path TEXT
                )
            ''')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_hash ON documents(hash)')
            self.conn.commit()

    def is_duplicate(self, text_hash: str) -> bool:
        if not self.config.get('deduplication', 'enabled', default=True):
            return False
        with self.lock:
            cur = self.conn.cursor()
            cur.execute('SELECT 1 FROM documents WHERE hash = ?', (text_hash,))
            return cur.fetchone() is not None

    def save_document(self, doc: ProcessedDocument, file_path: Path):
        with self.lock:
            cur = self.conn.cursor()
            cur.execute('''
                INSERT OR IGNORE INTO documents (id, hash, source, quality, type, language, timestamp, file_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (doc.id, doc.hash, doc.source, doc.quality, doc.type, doc.language, doc.timestamp, str(file_path)))
            self.conn.commit()

    def save_file(self, doc: ProcessedDocument) -> Path:
        if doc.quality >= 0.7 or doc.type in ('code', 'article'):
            folder = self.clean_dir
        else:
            folder = self.raw_dir
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        fname = f"{doc.type}_{doc.hash[:8]}_{timestamp}.json"
        path = folder / fname
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(doc.to_dict(), f, indent=2, ensure_ascii=False)
        self.save_document(doc, path)
        return path

    def close(self):
        with self.lock:
            self.conn.close()

# ----------------------------------------------------------------------
# Text Cleaner
# ----------------------------------------------------------------------
class TextCleaner:
    """Pembersihan teks dari noise dan normalisasi."""
    # Pola-pola noise
    PATTERNS = [
        (r'<[^>]+>', ' '),                          # HTML tags
        (r'\{[^\}]*\}', ' '),                        # JSON-like
        (r'function\s*\([^\)]*\)\s*\{', ' '),        # JS functions
        (r'var\s+\w+\s*=', ' '),                      # JS var
        (r'@media\s+[^\{]+\{', ' '),                  # CSS media
        (r'https?://\S+', ' '),                       # URLs
        (r'[\w\.-]+@[\w\.-]+', ' '),                  # emails
        (r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', ' '), # IPs
        (r'[0-9a-f]{32,}', ' '),                       # hashes
        (r'[A-Za-z0-9+/]{50,}', ' '),                  # base64
        (r'#\w+', ' '),                                # hashtags
        (r'@\w+', ' '),                                # mentions
        (r'[^\w\s\.\,\!\?\-\:\;\"\'\?]', ' '),        # karakter aneh
    ]

    @classmethod
    def clean(cls, text: str) -> str:
        """Bersihkan teks."""
        text = unescape(text)
        # Normalisasi Unicode (NFKC)
        text = unicodedata.normalize('NFKC', text)
        for pattern, repl in cls.PATTERNS:
            text = re.sub(pattern, repl, text, flags=re.DOTALL | re.IGNORECASE)
        # Hapus spasi berlebih
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

# ----------------------------------------------------------------------
# Language Detector (dengan fallback sederhana)
# ----------------------------------------------------------------------
class LanguageDetector:
    """Deteksi bahasa berdasarkan huruf atau langdetect."""
    @staticmethod
    def detect(text: str) -> str:
        if LANGDETECT_AVAILABLE and len(text) > 50:
            try:
                return detect_lang(text)
            except:
                pass
        # Fallback sederhana: deteksi berdasarkan skrip
        # Jika banyak karakter non-latin, anggap 'id' atau lainnya, tapi di sini kita kembalikan 'en'
        # Untuk keperluan demo, kita asumsikan Inggris
        return 'en'

# ----------------------------------------------------------------------
# Quality Scorer
# ----------------------------------------------------------------------
class QualityScorer:
    """Menghitung skor kualitas teks."""
    def __init__(self, config: SeafilConfig):
        self.min_words = config.get('quality', 'min_words', default=10)
        self.min_unique_ratio = config.get('quality', 'min_unique_ratio', default=0.4)
        self.min_alpha_ratio = config.get('quality', 'min_alpha_ratio', default=0.6)
        self.min_sentences = config.get('quality', 'min_sentence_count', default=2)

    def score(self, text: str) -> float:
        words = text.split()
        if len(words) < self.min_words:
            return 0.0

        unique_ratio = len(set(words)) / len(words)
        alpha_chars = sum(c.isalpha() for c in text)
        alpha_ratio = alpha_chars / max(len(text), 1)

        # Hitung jumlah kalimat (sederhana)
        sentences = sent_tokenize(text)
        sent_count = len(sentences)
        sent_bonus = 0.1 if sent_count >= self.min_sentences else 0.0

        # Penalti jika di bawah threshold
        score = (unique_ratio * 0.5) + (alpha_ratio * 0.4) + sent_bonus
        if unique_ratio < self.min_unique_ratio:
            score *= 0.7
        if alpha_ratio < self.min_alpha_ratio:
            score *= 0.7

        return min(score, 1.0)

# ----------------------------------------------------------------------
# Classifier (berbasis aturan yang diperkaya)
# ----------------------------------------------------------------------
class Classifier:
    """Klasifikasi tipe konten dengan aturan."""
    # Pola untuk berbagai tipe
    CODE_PATTERNS = [
        r'def\s+\w+\s*\(', r'class\s+\w+', r'import\s+\w+', r'from\s+\w+\s+import',
        r'if\s+__name__\s*==', r'for\s+\w+\s+in', r'while\s+', r'return\s+',
        r'public\s+class', r'private\s+', r'function\s+\w+\s*\(', r'var\s+\w+\s*=',
        r'let\s+\w+\s*=', r'const\s+\w+\s*=', r'#include', r'using namespace',
    ]
    CONFIG_PATTERNS = [
        r'=', r';', r'\[.*\]', r'\{.*\}', r'<.*>', r'#.*', r';\s*$'
    ]
    LOG_PATTERNS = [
        r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', r'\d{2}/\d{2}/\d{4}', r'ERROR|WARN|INFO|DEBUG',
        r'at\s+[\w\.]+\([\w\.]+\.java:\d+\)'
    ]
    MARKUP_PATTERNS = [
        r'<[^>]+>', r'&[a-z]+;', r'{{.*}}', r'{%.*%}'
    ]

    @classmethod
    def classify(cls, text: str) -> str:
        text_lower = text.lower()

        # Cek kode
        code_score = sum(1 for p in cls.CODE_PATTERNS if re.search(p, text_lower))
        if code_score >= 3:
            return 'code'

        # Cek log
        log_score = sum(1 for p in cls.LOG_PATTERNS if re.search(p, text))
        if log_score >= 2:
            return 'log'

        # Cek konfigurasi
        config_score = sum(1 for p in cls.CONFIG_PATTERNS if re.search(p, text))
        if config_score >= 5 and len(text) < 2000:
            return 'config'

        # Cek markup
        markup_score = sum(1 for p in cls.MARKUP_PATTERNS if re.search(p, text))
        if markup_score >= 3:
            return 'markup'

        # Cek artikel (banyak kalimat)
        sentences = sent_tokenize(text)
        if len(sentences) >= 5 and text.count('.') > 3:
            return 'article'

        # Percakapan?
        if re.search(r'^\s*[A-Z][a-z]+:', text, re.MULTILINE):
            return 'conversation'

        return 'unknown'

# ----------------------------------------------------------------------
# Keyword Extractor (beberapa metode)
# ----------------------------------------------------------------------
class KeywordExtractor:
    def __init__(self, config: SeafilConfig):
        self.method = config.get('keywords', 'method', default='tfidf')
        self.max_keywords = config.get('keywords', 'max_keywords', default=15)
        self.min_word_len = config.get('keywords', 'min_word_length', default=3)

    def extract(self, text: str) -> List[str]:
        if self.method == 'tfidf':
            return self._tfidf(text)
        elif self.method == 'rake':
            return self._rake(text)
        elif self.method == 'frequency':
            return self._frequency(text)
        else:
            return self._frequency(text)

    def _tokenize_words(self, text: str) -> List[str]:
        words = re.findall(r'\b\w+\b', text.lower())
        return [w for w in words if len(w) >= self.min_word_len and w not in STOPWORDS]

    def _frequency(self, text: str) -> List[str]:
        words = self._tokenize_words(text)
        freq = Counter(words)
        return [w for w, _ in freq.most_common(self.max_keywords)]

    def _tfidf(self, text: str) -> List[str]:
        # Untuk satu dokumen, TF-IDF tidak berarti, jadi kita gunakan frekuensi dengan penekanan pada kata yang jarang muncul di korpus umum.
        # Sederhananya kita pakai frekuensi biasa.
        return self._frequency(text)

    def _rake(self, text: str) -> List[str]:
        # Implementasi RAKE sederhana (Rapid Automatic Keyword Extraction)
        # 1. Split teks menjadi kalimat
        sentences = sent_tokenize(text)
        # 2. Tokenisasi kata per kalimat, dan tandai phrase (kombinasi kata non-stopword)
        phrase_candidates = []
        for sent in sentences:
            words = re.findall(r'\b\w+\b', sent.lower())
            # Buat phrase dengan menggabungkan kata selama bukan stopword
            phrase = []
            for w in words:
                if w not in STOPWORDS and len(w) >= self.min_word_len:
                    phrase.append(w)
                else:
                    if len(phrase) > 0:
                        phrase_candidates.append(' '.join(phrase))
                        phrase = []
            if phrase:
                phrase_candidates.append(' '.join(phrase))

        # 3. Hitung skor setiap kata: frekuensi kemunculan di seluruh teks, dan degree (jumlah kata yang berko-okurensi dalam phrase)
        word_freq = Counter()
        word_degree = Counter()
        for phrase in phrase_candidates:
            words = phrase.split()
            for w in words:
                word_freq[w] += 1
                word_degree[w] += len(words) - 1  # derajat adalah jumlah kata lain dalam phrase yang sama

        # 4. Skor kata = degree/freq
        word_score = {w: word_degree[w] / word_freq[w] if word_freq[w] > 0 else 0 for w in word_freq}

        # 5. Skor phrase = jumlah skor kata penyusun
        phrase_score = {}
        for phrase in set(phrase_candidates):
            words = phrase.split()
            score = sum(word_score.get(w, 0) for w in words)
            phrase_score[phrase] = score

        # 6. Ambil top phrase
        sorted_phrases = sorted(phrase_score.items(), key=lambda x: x[1], reverse=True)
        return [p for p, _ in sorted_phrases[:self.max_keywords]]

# ----------------------------------------------------------------------
# Summarizer (TextRank atau frekuensi)
# ----------------------------------------------------------------------
class Summarizer:
    def __init__(self, config: SeafilConfig):
        self.method = config.get('summarization', 'method', default='textrank')
        self.max_sentences = config.get('summarization', 'max_sentences', default=5)
        self.ratio = config.get('summarization', 'ratio', default=0.3)
        self.use_stopwords = config.get('summarization', 'use_stopwords', default=True)

    def summarize(self, text: str) -> Tuple[str, List[str]]:
        sentences = sent_tokenize(text)
        if len(sentences) <= self.max_sentences:
            return text, sentences

        if self.method == 'textrank':
            return self._textrank(text, sentences)
        elif self.method == 'frequency':
            return self._frequency(text, sentences)
        else:  # first_n
            return self._first_n(sentences)

    def _first_n(self, sentences: List[str]) -> Tuple[str, List[str]]:
        selected = sentences[:self.max_sentences]
        summary = ' '.join(selected)
        return summary, selected

    def _frequency(self, text: str, sentences: List[str]) -> Tuple[str, List[str]]:
        # Hitung frekuensi kata (abaikan stopwords)
        words = re.findall(r'\b\w+\b', text.lower())
        if self.use_stopwords:
            words = [w for w in words if w not in STOPWORDS]
        freq = Counter(words)

        # Skor kalimat berdasarkan frekuensi kata
        sent_scores = []
        for sent in sentences:
            sent_words = re.findall(r'\b\w+\b', sent.lower())
            if self.use_stopwords:
                sent_words = [w for w in sent_words if w not in STOPWORDS]
            score = sum(freq.get(w, 0) for w in sent_words)
            sent_scores.append((sent, score))

        # Ambil N kalimat dengan skor tertinggi, lalu urutkan sesuai posisi asli
        sent_scores.sort(key=lambda x: x[1], reverse=True)
        top = [s for s, _ in sent_scores[:self.max_sentences]]
        top.sort(key=lambda s: sentences.index(s))
        summary = ' '.join(top)
        return summary, top

    def _textrank(self, text: str, sentences: List[str]) -> Tuple[str, List[str]]:
        """Implementasi TextRank sederhana (graph-based)."""
        import numpy as np  # kita asumsikan numpy tersedia, jika tidak fallback ke frekuensi
        try:
            import numpy as np
        except ImportError:
            return self._frequency(text, sentences)

        n = len(sentences)
        if n == 0:
            return '', []

        # Buat matriks similarity berdasarkan overlap kata
        # Tokenisasi tiap kalimat
        sent_tokens = []
        for sent in sentences:
            words = re.findall(r'\b\w+\b', sent.lower())
            if self.use_stopwords:
                words = [w for w in words if w not in STOPWORDS]
            sent_tokens.append(set(words))

        # Matriks similarity
        sim = np.zeros((n, n))
        for i in range(n):
            for j in range(i+1, n):
                overlap = len(sent_tokens[i] & sent_tokens[j])
                if overlap > 0:
                    denom = math.log(len(sent_tokens[i]) + 1) + math.log(len(sent_tokens[j]) + 1)
                    sim[i][j] = sim[j][i] = overlap / denom if denom != 0 else 0

        # Normalisasi tiap baris (bobot keluar)
        for i in range(n):
            row_sum = sim[i].sum()
            if row_sum > 0:
                sim[i] /= row_sum

        # Power iteration untuk PageRank
        d = 0.85
        scores = np.ones(n) / n
        for _ in range(50):
            scores = (1 - d) / n + d * sim.T @ scores

        # Urutkan kalimat berdasarkan skor
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        selected_idx = [idx for idx, _ in ranked[:self.max_sentences]]
        selected_idx.sort()  # urut asli
        selected = [sentences[i] for i in selected_idx]
        summary = ' '.join(selected)
        return summary, selected

# ----------------------------------------------------------------------
# Pipeline Utama
# ----------------------------------------------------------------------
class SeafilPipeline:
    """Mengatur alur pemrosesan."""
    def __init__(self, config: SeafilConfig, storage: StorageManager):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.storage = storage
        self.cleaner = TextCleaner()
        self.lang_detector = LanguageDetector()
        self.quality_scorer = QualityScorer(config)
        self.classifier = Classifier()
        self.keyword_extractor = KeywordExtractor(config)
        self.summarizer = Summarizer(config)
        self.stats = Counter()

    def process(self, data: str, source: str = "unknown", auto_save: bool = True) -> Optional[ProcessedDocument]:
        """Proses dokumen secara sinkron."""
        self.stats['total'] += 1

        # Validasi dasar
        if not data or not isinstance(data, str) or len(data.strip()) < 20:
            self.stats['rejected_basic'] += 1
            self.logger.debug(f"Rejected basic validation")
            return None

        # Cek duplikat
        text_hash = self._compute_hash(data)
        if self.storage.is_duplicate(text_hash):
            self.stats['duplicate'] += 1
            self.logger.debug(f"Duplicate found, hash: {text_hash[:8]}")
            return None

        # Bersihkan teks
        cleaned = self.cleaner.clean(data)
        if len(cleaned) < 20:
            self.stats['rejected_clean'] += 1
            return None

        # Deteksi bahasa
        orig_lang = self.lang_detector.detect(cleaned)
        # Kita hanya proses bahasa Inggris untuk kesederhanaan
        if orig_lang != 'en':
            self.logger.info(f"Non-English text detected ({orig_lang}), but we continue in English mode.")
            # Tidak ada terjemahan, kita tetap proses tapi mungkin kualitas rendah

        # Kualitas
        quality = self.quality_scorer.score(cleaned)
        if quality < 0.3:
            self.stats['rejected_quality'] += 1
            self.logger.debug(f"Low quality: {quality:.2f}")
            return None

        # Klasifikasi
        content_type = self.classifier.classify(cleaned)

        # Ekstraksi kata kunci
        keywords = self.keyword_extractor.extract(cleaned)

        # Peringkasan
        summary, key_points = self.summarizer.summarize(cleaned)

        # Bangun objek dokumen
        doc = ProcessedDocument(
            id=text_hash[:16],
            content=cleaned,
            summary=summary,
            key_points=key_points,
            keywords=keywords,
            source=source,
            length=len(cleaned),
            quality=quality,
            type=content_type,
            hash=text_hash,
            language='en',  # setelah deteksi kita asumsikan en
            original_language=orig_lang,
            timestamp=datetime.now().isoformat(),
            metadata={}
        )

        if auto_save:
            self.storage.save_file(doc)
            self.stats['saved'] += 1

        self.stats['accepted'] += 1
        return doc

    def _compute_hash(self, text: str) -> str:
        normalized = re.sub(r'\s+', ' ', text).strip().lower()
        return hashlib.sha256(normalized.encode()).hexdigest()

    def get_stats(self) -> Dict[str, int]:
        return dict(self.stats)

# ----------------------------------------------------------------------
# Kelas Utama Seafil (facade)
# ----------------------------------------------------------------------
class Seafil:
    """
    Seafil v4.0 Offline – Semantic Filter tanpa LLM eksternal.
    """
    def __init__(self, config_path: Optional[Union[str, Path]] = None, strict: bool = False, **kwargs):
        self.config = SeafilConfig(config_path)
        if strict:
            self.config.config['quality']['min_words'] = 20
            self.config.config['quality']['min_unique_ratio'] = 0.5

        # Override kwargs
        for key, value in kwargs.items():
            self._set_nested(self.config.config, key.split('.'), value)

        self.logger = logging.getLogger(self.__class__.__name__)
        self.storage = StorageManager(self.config, self.logger)
        self.pipeline = SeafilPipeline(self.config, self.storage)

    def _set_nested(self, d, keys, value):
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = value

    def process(self, data: str, source: str = "unknown", auto_save: bool = True) -> Optional[ProcessedDocument]:
        """Proses dokumen."""
        return self.pipeline.process(data, source, auto_save)

    def get_stats(self) -> Dict[str, int]:
        return self.pipeline.get_stats()

    def close(self):
        self.storage.close()