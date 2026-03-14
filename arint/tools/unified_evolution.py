import sqlite3
import time
import random
from pathlib import Path
from .code_learner import CodeCollector
from .validator import run_sandboxed_test

class GenePool:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._create_tables()

    def _create_tables(self):
        with self.conn:
            self.conn.execute("""
            CREATE TABLE IF NOT EXISTS gene_pool (
                id INTEGER PRIMARY KEY,
                code TEXT NOT NULL,
                fitness REAL NOT NULL,
                source TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

    def add_gene(self, code, fitness, source):
        with self.conn:
            self.conn.execute(
                "INSERT INTO gene_pool (code, fitness, source) VALUES (?, ?, ?)",
                (code, fitness, source)
            )
    
    def get_best(self, limit=10):
        cursor = self.conn.execute(
            "SELECT code, fitness FROM gene_pool ORDER BY fitness DESC LIMIT ?", (limit,)
        )
        return cursor.fetchall()

class GeneGauntlet:
    def __init__(self, validator_func):
        self.validator = validator_func

    def evaluate(self, code, test_cases):
        '''Mengevaluasi satu gen dan mengembalikan skor kebugaran.'''
        # Tahap 1: Validasi Sintaks
        try:
            ast.parse(code)
        except SyntaxError:
            return 0.0 # Kebugaran nol jika sintaks tidak valid

        # Tahap 2: Pengujian Sandbox
        result = self.validator(code, test_cases)
        
        if result["status"] == "success":
            return 100.0
        elif result["status"] == "failure":
            return 50.0 * (result['passed'] / result['total'])
        else:
            return 1.0 # Kebugaran minimal untuk kode yang bisa berjalan tapi error

class UnifiedEvolutionEngine:
    def __init__(self, knowledge_db):
        self.gene_pool = GenePool(knowledge_db)
        self.harvester = CodeCollector() # Pengumpul gen
        self.gauntlet = GeneGauntlet(run_sandboxed_test) # Validator gen
        self.mutator = CodeGenetic([]) # Untuk operasi mutasi & crossover

    def run_autonomous_cycle(self, generations=5):
        print("[UEE] Menjalankan siklus evolusi otonom...")
        # 1. Dapatkan gen terbaik dari pool sebagai populasi awal
        initial_pop_tuples = self.gene_pool.get_best(limit=20)
        if len(initial_pop_tuples) < 4: # Butuh minimal 4 untuk crossover
            print("[UEE] Populasi tidak cukup untuk evolusi, perlu panen.")
            self.harvest_new_genes()
            return
        
        initial_pop = [code for code, fit in initial_pop_tuples]
        self.mutator.population = initial_pop
        
        # 2. Lakukan evolusi
        evolved_code = self.mutator.evolve(generations=generations, population_size=len(initial_pop))
        
        # 3. Validasi ulang hasil terbaik
        #    (menggunakan test case dummy untuk evaluasi umum)
        test_cases = [((1, 2), 3), ((0, 0), 0)] 
        new_fitness = self.gauntlet.evaluate(evolved_code, test_cases)
        
        print(f"[UEE] Evolusi selesai. Kebugaran baru: {new_fitness:.2f}")
        
        # 4. Jika cukup baik, tambahkan kembali ke gene pool
        if new_fitness > 50:
            self.gene_pool.add_gene(evolved_code, new_fitness, "evolution_cycle")
            print("[UEE] Gen baru yang berevolusi ditambahkan ke pool.")

    def harvest_new_genes(self, max_sources=1):
        print("[UEE] Memanen gen baru dari internet...")
        urls_to_try = random.sample(self.harvester.sources, k=min(max_sources, len(self.harvester.sources)))
        for url in urls_to_try:
            self.harvester.fetch_and_store(url)

    def process_goal(self, goal_manager, goal_index):
        # Logika canggih untuk memproses subgoal yang membutuhkan kode
        # Ini akan mengekstrak persyaratan dari deskripsi tujuan,
        # membuat test case, dan menjalankan evolusi yang ditargetkan.
        print(f"[UEE] Memproses tujuan evolusi: {goal_index}")
        # (Implementasi detail akan ditambahkan di sini)
        pass

def create_unified_engine(config):
    db_path = config.get("knowledge_db_path", "memory/evolution/knowledge.db")
    return UnifiedEvolutionEngine(knowledge_db=db_path)
