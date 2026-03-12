import tokenize
import io
import re
import random
import urllib.request
from collections import defaultdict, Counter
from pathlib import Path
import html

class CodeCollector:
    def __init__(self):
        self.sources = [
            "https://docs.python.org/3/tutorial/controlflow.html",
            "https://docs.python.org/3/tutorial/datastructures.html",
            "https://www.w3schools.com/python/python_functions.asp",
            "https://www.programiz.com/python-programming/examples",
            "https://realpython.com/lessons/",
        ]
        self.code_dir = Path("memory/knowledge/raw/code")
        self.code_dir.mkdir(parents=True, exist_ok=True)

    def fetch_and_store(self, url):
        print(f"[CodeCollector] Fetching {url}")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Arint/6.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                html_content = resp.read().decode('utf-8', errors='ignore')
            blocks = self._extract_code_blocks(html_content)
            print(f"[CodeCollector] Found {len(blocks)} blocks")
            for i, code in enumerate(blocks):
                safe_name = url.replace('https://', '').replace('http://', '').replace('/', '_')[:50]
                fname = self.code_dir / f"{safe_name}_{i}.py"
                with open(fname, 'w', encoding='utf-8') as f:
                    f.write(code)
                print(f"[CodeCollector] Saved {fname}")
            return len(blocks)
        except Exception as e:
            print(f"[CodeCollector] Error: {e}")
            return 0

    def _extract_code_blocks(self, html_content):
        blocks = []
        # Pola 1: <pre><code>...</code></pre>
        pattern1 = r'<pre><code(?: class="[^"]*")?>(.*?)</code></pre>'
        blocks += re.findall(pattern1, html_content, re.DOTALL | re.IGNORECASE)
        # Pola 2: <code>...</code> (terkadang tanpa pre)
        pattern2 = r'<code[^>]*>(.*?)</code>'
        blocks += re.findall(pattern2, html_content, re.DOTALL | re.IGNORECASE)
        # Pola 3: Markdown ```python ... ```
        pattern3 = r'```python\n(.*?)\n```'
        blocks += re.findall(pattern3, html_content, re.DOTALL)
        # Pola 4: <div class="highlight">...<pre>...</pre>
        pattern4 = r'<div class="highlight".*?<pre>(.*?)</pre>'
        blocks += re.findall(pattern4, html_content, re.DOTALL | re.IGNORECASE)
        # Bersihkan entitas HTML dan hapus tag residual
        cleaned = []
        for b in blocks:
            b = html.unescape(b)
            b = re.sub(r'<[^>]+>', '', b)  # hapus tag HTML yang mungkin tersisa
            b = b.strip()
            if b and len(b) > 20:  # minimal panjang
                cleaned.append(b)
        return cleaned

    def seed_with_examples(self):
        examples = [
            "def hello():\n    print('Hello, world!')\n\nhello()",
            "def add(a, b):\n    return a + b",
            "for i in range(5):\n    print(i)",
            "class Person:\n    def __init__(self, name):\n        self.name = name\n    def greet(self):\n        print(f'Hello, {self.name}')",
            "import math\nprint(math.sqrt(16))",
            "def factorial(n):\n    if n == 0:\n        return 1\n    else:\n        return n * factorial(n-1)",
            "numbers = [1, 2, 3, 4, 5]\nsquared = [x**2 for x in numbers]",
        ]
        for i, code in enumerate(examples):
            fname = self.code_dir / f"seed_{i}.py"
            with open(fname, 'w', encoding='utf-8') as f:
                f.write(code)
        print(f"[CodeCollector] Seeded {len(examples)} contoh kode.")

class CodeTokenizer:
    def __init__(self):
        self.unigram = Counter()
        self.bigram = defaultdict(Counter)
        self.trigram = defaultdict(lambda: defaultdict(Counter))
        self.literals = defaultdict(list)

    def tokenize_code(self, code):
        tokens = []
        try:
            g = tokenize.generate_tokens(io.StringIO(code).readline)
            for toknum, tokval, _, _, _ in g:
                if toknum == tokenize.ENDMARKER:
                    break
                tokens.append((toknum, tokval))
        except tokenize.TokenError:
            pass
        return tokens

    def update(self, tokens):
        types = [t[0] for t in tokens]
        for tt in types:
            self.unigram[tt] += 1
        for i in range(len(types)-1):
            self.bigram[types[i]][types[i+1]] += 1
        for i in range(len(types)-2):
            self.trigram[types[i]][types[i+1]][types[i+2]] += 1
        for tt, tv in tokens:
            if tt in (tokenize.NAME, tokenize.NUMBER, tokenize.STRING):
                self.literals[tt].append(tv)

    def load_directory(self, path):
        for file in Path(path).glob("*.py"):
            with open(file, 'r', encoding='utf-8') as f:
                code = f.read()
            tokens = self.tokenize_code(code)
            self.update(tokens)