import random
import ast
from pathlib import Path
from tools.code_learner import CodeCollector, CodeTokenizer
from tools.code_genetic import CodeGenetic

class Coder:
    def __init__(self):
        self.collector = CodeCollector()
        self.tokenizer = CodeTokenizer()
        self.genetic = None
        self._initialize()

    def _initialize(self):
        code_dir = Path("memory/knowledge/raw/code")
        # Jika belum ada file atau kurang dari 3, coba fetch dari internet
        if not code_dir.exists() or len(list(code_dir.glob("*.py"))) < 3:
            print("[Coder] Mengumpulkan kode dari internet...")
            for url in self.collector.sources[:3]:
                self.collector.fetch_and_store(url)
        # Jika masih kosong, gunakan seed contoh
        if len(list(code_dir.glob("*.py"))) == 0:
            print("[Coder] Tidak ada kode dari internet, menggunakan contoh bawaan.")
            self.collector.seed_with_examples()
        # Muat tokenizer
        self.tokenizer.load_directory(code_dir)
        # Muat populasi untuk genetika
        codes = []
        for file in code_dir.glob("*.py"):
            with open(file, 'r', encoding='utf-8') as f:
                codes.append(f.read())
        if codes:
            self.genetic = CodeGenetic(codes)
            print(f"[Coder] Populasi awal: {len(codes)} kode.")
        else:
            print("[Coder] Tidak ada kode sama sekali, fallback ke generator sederhana.")
            self.genetic = None

    def can_write(self):
        return self.genetic is not None and len(self.genetic.population) >= 3

    def write_function(self, name=None):
        if not self.can_write():
            return None
        if name is None:
            name = f"auto_gen_{random.randint(1000,9999)}"
        # Evolusi selama beberapa generasi
        best_code = self.genetic.evolve(generations=3, population_size=10)
        # Pastikan berbentuk fungsi
        if not best_code.strip().startswith('def'):
            lines = best_code.split('\n')
            indented = '\n    '.join(lines) if lines else '    pass'
            best_code = f"def {name}():\n    {indented}"
        # Validasi akhir
        try:
            ast.parse(best_code)
        except SyntaxError:
            best_code = f"def {name}():\n    pass"
        return best_code