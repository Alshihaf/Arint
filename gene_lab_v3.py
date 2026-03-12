#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║       SelfExpandingEvolutionEngine  v3.0  —  gene_lab.py                   ║
║                                                                              ║
║  Template hanya "contoh", bukan batasan. Engine tumbuh sendiri.             ║
║                                                                              ║
║  Fitur Baru vs v2:                                                           ║
║  ─────────────────────────────────────────────────────────────────────────  ║
║  [+] Gene Gauntlet       — Pipeline 6 stage: Complexity→Syntax→TypeDiv→     ║
║                            EdgeCase→Uniqueness→Performance. Yang lemah      ║
║                            tersingkir, yang kuat masuk pool.                ║
║  [+] Gene Synthesizer    — Distilasi kode evolusi sukses → gen baru         ║
║  [+] Code Harvester      — Scan file teks apapun di filesystem → gen baru   ║
║  [+] Template Mutator    — Mutasi AST-level pada gen yang ada → varian baru ║
║  [+] Self-Reflective Scanner — Engine membaca source code-nya sendiri       ║
║  [+] Gene Pruner (Moderate) — Buang gen lemah + jarang dipakai              ║
║  [+] Dynamic Gene Pool   — Pool tumbuh & menyusut secara organik            ║
║                                                                              ║
║  Warisan dari v2:                                                            ║
║  ─────────────────────────────────────────────────────────────────────────  ║
║  [=] Experience Memory, Island Model, Pattern Mining, Novelty Search        ║
║  [=] 6 Tipe Mutasi, Intelligent XO, Adaptive HP, Warm Start                ║
║  [=] Diversity Guard, Persistent Memory, Fitness Cache, Diagnostics         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import ast
import json
import logging
import random
import threading
import time
import traceback
import hashlib
import shutil
import inspect
import re
import statistics
import itertools
import math
import os
import sys
import textwrap
import operator
import copy

from collections import defaultdict, Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Callable, Set

# ─────────────────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────────────────

logger = logging.getLogger("ExperienceDrivenEvolution")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# ─────────────────────────────────────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class EvolutionConfig:
    # Populasi & Generasi
    population_size: int = 40
    generations: int = 60
    mutation_rate: float = 0.3
    crossover_rate: float = 0.8
    elitism_count: int = 3
    tournament_size: int = 5
    timeout_seconds: float = 2.0

    # Island Model
    num_islands: int = 3
    migration_interval: int = 10   # tiap berapa generasi migrasi terjadi
    migration_size: int = 2        # berapa individu yang bermigrasi per island

    # Bobot Multi-Objective
    weight_correctness: float = 10.0
    weight_speed: float = 1.0
    weight_memory: float = 0.5
    weight_simplicity: float = 0.2
    weight_novelty: float = 0.5    # [BARU] reward untuk keunikan perilaku

    # Experience & Memory
    learning_rate: float = 0.15       # seberapa cepat belajar dari pengalaman
    forgetting_rate: float = 0.002    # bobot lama perlahan meluruh tiap generasi
    experience_min_weight: float = 0.05  # batas bawah bobot gen
    experience_max_weight: float = 5.0   # batas atas bobot gen

    # Pattern Mining
    pattern_min_length: int = 2
    pattern_max_length: int = 4
    pattern_top_k: int = 20    # berapa pola teratas yang disimpan
    pattern_use_prob: float = 0.3  # probabilitas pakai pola saat init genome

    # Adaptive Hyperparameters (Simulated Annealing)
    stagnation_threshold: int = 7
    annealing_heat_factor: float = 1.6   # faktor naikkan mutasi saat stagnan
    annealing_cool_factor: float = 0.88  # faktor turunkan mutasi saat progres
    mutation_rate_min: float = 0.05
    mutation_rate_max: float = 0.90
    crossover_rate_min: float = 0.3
    crossover_rate_max: float = 0.95

    # Novelty Archive
    novelty_archive_size: int = 50
    novelty_k_nearest: int = 5

    # Diversity
    diversity_threshold: float = 0.15  # kalau < ini, inject fresh blood
    diversity_inject_count: int = 5

    # Self-Improvement
    auto_internal_optimization: bool = True
    internal_optimization_interval: int = 100

    # Knowledge Base
    use_knowledge_base: bool = True
    max_knowledge_age: float = 7 * 24 * 3600

    # Meta-Evolution
    meta_evolution_rate: float = 0.01

    # ── v3: Self-Expanding Pool ──────────────────────────────────────────────
    # Gene Gauntlet
    gauntlet_min_score: float = 0.30       # skor minimum untuk masuk pool
    gauntlet_probationary_threshold: float = 0.60  # < ini → masuk sebagai probationary
    gauntlet_elite_threshold: float = 0.80  # > ini → masuk sebagai elite
    gauntlet_probationary_weight: float = 0.3
    gauntlet_standard_weight: float = 1.0
    gauntlet_elite_weight: float = 2.5
    gauntlet_timeout: float = 0.5          # max detik per stage execution

    # Gene Pruner (Moderate)
    pruner_weight_threshold: float = 0.20  # buang kalau weight di bawah ini
    pruner_min_usage: int = 3              # minimal pernah dipakai N kali
    pruner_min_pool_size: int = 20         # pool tidak boleh lebih kecil dari ini
    pruner_interval: int = 15             # tiap berapa generasi pruner jalan

    # Code Harvester
    harvester_max_files: int = 50          # max file per sesi scan
    harvester_max_genes_per_file: int = 8  # max kandidat gen per file
    harvester_scan_extensions: Tuple = (".py", ".txt", ".md", ".sh", ".js", ".ts",
                                         ".java", ".c", ".cpp", ".rs", ".go")
    harvester_interval: int = 20          # tiap berapa generasi harvester jalan

    # Gene Synthesizer
    synthesizer_interval: int = 5         # tiap berapa generasi synthesizer jalan
    synthesizer_max_per_run: int = 5      # max gen baru per run

    # Template Mutator
    mutator_interval: int = 8
    mutator_max_per_run: int = 4

    # Self-Reflective Scanner
    self_scan_interval: int = 30

    # Dynamic Pool limits
    pool_max_size: int = 200
    pool_soft_max: int = 120              # di atas ini pruner lebih agresif

    version: float = 3.0


@dataclass
class CodeGene:
    id: str
    template: str
    arity: int
    complexity: float
    description: str = ""
    # Genealogy (v2)
    success_count: int = 0
    failure_count: int = 0
    # v3: Self-Expanding metadata
    origin: str = "default"          # "default" | "synthesized" | "harvested" | "mutated" | "self_scan"
    gauntlet_score: float = 1.0      # skor dari Gene Gauntlet (0.0 - 1.0)
    is_probationary: bool = False    # gen baru yang belum terbukti
    usage_count: int = 0             # total dipakai di genome manapun
    added_at: float = field(default_factory=time.time)
    source_hint: str = ""            # dari file mana / metode mana asalnya


@dataclass
class Genome:
    genes: List[CodeGene]
    fitness: float = 0.0
    compiled_code: str = ""
    generation: int = 0
    parent_ids: Tuple[str, str] = ("", "")
    execution_time: float = 0.0
    memory_estimate: float = 0.0
    code_length: int = 0
    # [BARU] behavioral fingerprint untuk novelty search
    behavior_fingerprint: str = ""
    novelty_score: float = 0.0
    # [BARU] island ID
    island_id: int = 0


@dataclass
class Solution:
    task_id: str
    code: str
    fitness: float
    execution_time: float
    memory_estimate: float
    created_at: float
    last_used: float
    use_count: int
    version: int


@dataclass
class GenePattern:
    """Pola urutan gen yang terbukti sukses."""
    gene_ids: List[str]
    avg_fitness: float
    occurrence_count: int
    last_seen: float


# ─────────────────────────────────────────────────────────────────────────────
# GENE POOL
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_GENE_POOL = [
    # --- MATEMATIKA DASAR ---
    CodeGene("assign_add",    "    result = arg1 + arg2\n",                                         2, 1.0, "penjumlahan"),
    CodeGene("assign_sub",    "    result = arg1 - arg2\n",                                         2, 1.0, "pengurangan"),
    CodeGene("assign_mul",    "    result = arg1 * arg2\n",                                         2, 1.0, "perkalian"),
    CodeGene("assign_div",    "    result = (arg1 / arg2) if arg2 != 0 else 0\n",                   2, 1.2, "pembagian aman"),
    CodeGene("assign_mod",    "    result = arg1 % arg2 if arg2 != 0 else 0\n",                     2, 1.2, "modulo aman"),
    CodeGene("assign_floordiv","   result = arg1 // arg2 if arg2 != 0 else 0\n",                    2, 1.2, "pembagian bulat"),
    CodeGene("math_pow",      "    result = arg1 ** arg2 if abs(arg1) < 1e6 and abs(arg2) < 20 else 0\n", 2, 2.0, "pangkat"),
    CodeGene("math_sqrt",     "    result = arg1 ** 0.5 if arg1 >= 0 else 0\n",                     1, 1.5, "akar kuadrat"),
    CodeGene("math_log",      "    result = math.log(abs(arg1) + 1)\n",                             1, 2.0, "log natural"),
    CodeGene("math_abs",      "    result = abs(arg1)\n",                                           1, 1.0, "nilai mutlak"),
    CodeGene("math_ceil",     "    result = math.ceil(arg1) if isinstance(arg1, float) else arg1\n",1, 1.2, "ceiling"),
    CodeGene("math_floor",    "    result = math.floor(arg1) if isinstance(arg1, float) else arg1\n",1,1.2,"floor"),
    CodeGene("math_clamp",    "    result = max(arg2, min(arg3, arg1))\n",                          3, 2.0, "clamp nilai"),

    # --- STATISTIK ---
    CodeGene("stat_mean",     "    result = sum(arg1)/len(arg1) if arg1 else 0\n",                  1, 2.0, "rata-rata"),
    CodeGene("stat_median",   "    result = sorted(arg1)[len(arg1)//2] if arg1 else 0\n",           1, 2.5, "median"),
    CodeGene("stat_variance", "    _m=sum(arg1)/len(arg1) if arg1 else 0; result=sum((x-_m)**2 for x in arg1)/len(arg1) if arg1 else 0\n", 1, 3.0, "varians"),
    CodeGene("stat_stdev",    "    _m=sum(arg1)/len(arg1) if arg1 else 0; _v=sum((x-_m)**2 for x in arg1)/max(len(arg1)-1,1); result=_v**0.5\n", 1, 3.0, "standar deviasi"),
    CodeGene("list_max_min",  "    result = (max(arg1), min(arg1)) if arg1 else (0, 0)\n",          1, 1.8, "nilai ekstrim"),
    CodeGene("stat_range",    "    result = max(arg1) - min(arg1) if arg1 else 0\n",                1, 1.8, "rentang nilai"),
    CodeGene("stat_normalize","    _mx=max(arg1) if arg1 else 1; _mn=min(arg1) if arg1 else 0; result=[((x-_mn)/(_mx-_mn) if _mx!=_mn else 0) for x in arg1]\n", 1, 3.5, "normalisasi 0-1"),

    # --- STRING ---
    CodeGene("string_concat", "    result = str(arg1) + str(arg2)\n",                               2, 1.0, "gabung string"),
    CodeGene("string_split",  "    result = str(arg1).split(str(arg2)) if str(arg2) else str(arg1).split()\n", 2, 2.0, "split string"),
    CodeGene("regex_find",    "    result = re.findall(str(arg2), str(arg1))\n",                     2, 3.5, "regex findall"),
    CodeGene("string_clean",  "    result = ''.join(e for e in str(arg1) if e.isalnum())\n",         1, 2.2, "clean alphanumeric"),
    CodeGene("string_upper",  "    result = str(arg1).upper()\n",                                   1, 1.0, "uppercase"),
    CodeGene("string_lower",  "    result = str(arg1).lower()\n",                                   1, 1.0, "lowercase"),
    CodeGene("string_strip",  "    result = str(arg1).strip()\n",                                   1, 1.0, "strip whitespace"),
    CodeGene("string_replace","    result = str(arg1).replace(str(arg2), str(arg3))\n",             3, 2.0, "replace substring"),
    CodeGene("string_len",    "    result = len(str(arg1))\n",                                      1, 1.0, "panjang string"),
    CodeGene("string_count",  "    result = str(arg1).count(str(arg2))\n",                          2, 1.5, "hitung kemunculan"),
    CodeGene("string_join",   "    result = str(arg2).join(str(x) for x in arg1) if isinstance(arg1, list) else str(arg1)\n", 2, 2.0, "join list ke string"),

    # --- LIST ---
    CodeGene("list_sort",     "    result = sorted(arg1)\n",                                        1, 2.0, "pengurutan asc"),
    CodeGene("list_sort_desc","    result = sorted(arg1, reverse=True)\n",                          1, 2.0, "pengurutan desc"),
    CodeGene("list_reverse",  "    result = arg1[::-1]\n",                                          1, 1.2, "balik list"),
    CodeGene("list_unique",   "    result = list(dict.fromkeys(arg1))\n",                           1, 2.0, "elemen unik (urutan preserved)"),
    CodeGene("list_filter_pos","   result = [x for x in arg1 if isinstance(x, (int, float)) and x > 0]\n", 1, 2.5, "filter positif"),
    CodeGene("list_map_scale","    result = [x * arg2 for x in arg1] if isinstance(arg1, list) else arg1\n", 2, 2.5, "skalasi list"),
    CodeGene("list_flatten",  "    result = [item for sub in arg1 for item in (sub if isinstance(sub, list) else [sub])]\n", 1, 3.5, "flatten nested"),
    CodeGene("list_reduce_sum","   result = sum(arg1) if isinstance(arg1, list) else 0\n",          1, 1.2, "total list"),
    CodeGene("list_any_all",  "    result = any(arg1) if arg2 == 'any' else all(arg1)\n",           2, 2.0, "any/all"),
    CodeGene("list_chunk",    "    result = [arg1[i:i+arg2] for i in range(0, len(arg1), max(arg2,1))] if isinstance(arg1,list) and arg2>0 else arg1\n", 2, 3.5, "chunking"),
    CodeGene("list_zip",      "    result = list(zip(arg1, arg2)) if isinstance(arg1, list) and isinstance(arg2, list) else []\n", 2, 2.0, "zip dua list"),
    CodeGene("list_enumerate","    result = list(enumerate(arg1)) if isinstance(arg1, list) else []\n", 1, 1.5, "indeksasi"),
    CodeGene("list_slice",    "    result = arg1[arg2:arg3] if isinstance(arg1, list) else arg1\n", 3, 1.5, "slicing list"),
    CodeGene("list_head",     "    result = arg1[:arg2] if isinstance(arg1, list) and arg2>0 else arg1\n", 2, 1.2, "ambil N elemen pertama"),
    CodeGene("list_tail",     "    result = arg1[-arg2:] if isinstance(arg1, list) and arg2>0 else arg1\n", 2, 1.2, "ambil N elemen terakhir"),
    CodeGene("list_concat",   "    result = list(arg1) + list(arg2) if isinstance(arg1,(list,tuple)) and isinstance(arg2,(list,tuple)) else arg1\n", 2, 1.5, "gabung dua list"),
    CodeGene("list_count_by", "    result = sum(1 for x in arg1 if x == arg2)\n",                   2, 2.0, "hitung kemunculan elemen"),
    CodeGene("list_remove",   "    result = [x for x in arg1 if x != arg2]\n",                      2, 2.0, "hapus elemen tertentu"),
    CodeGene("list_map_str",  "    result = [str(x) for x in arg1]\n",                              1, 1.5, "konversi list ke string"),
    CodeGene("list_map_int",  "    result = [int(x) for x in arg1 if str(x).lstrip('-').isdigit()]\n", 1, 2.0, "konversi list ke int"),

    # --- DICT ---
    CodeGene("dict_get",      "    result = arg1.get(arg2, None) if isinstance(arg1, dict) else {}\n", 2, 1.5, "ambil nilai dict"),
    CodeGene("dict_merge",    "    result = {**arg1, **arg2} if isinstance(arg1, dict) and isinstance(arg2, dict) else arg1\n", 2, 2.5, "merge dict"),
    CodeGene("dict_count",    "    result = {x: arg1.count(x) for x in set(arg1)} if isinstance(arg1, list) else {}\n", 1, 3.0, "frekuensi elemen"),
    CodeGene("dict_keys",     "    result = list(arg1.keys()) if isinstance(arg1, dict) else []\n", 1, 1.2, "ambil keys"),
    CodeGene("dict_values",   "    result = list(arg1.values()) if isinstance(arg1, dict) else []\n",1, 1.2, "ambil values"),
    CodeGene("dict_invert",   "    result = {v: k for k, v in arg1.items()} if isinstance(arg1, dict) else {}\n", 1, 2.5, "invert dict"),
    CodeGene("dict_filter",   "    result = {k: v for k, v in arg1.items() if v} if isinstance(arg1, dict) else {}\n", 1, 2.5, "filter truthy values"),

    # --- LOGIKA ---
    CodeGene("logic_if_else", "    result = arg1 if bool(arg1) else arg2\n",                        2, 1.5, "ternary"),
    CodeGene("logic_and",     "    result = arg1 and arg2\n",                                       2, 1.0, "AND"),
    CodeGene("logic_or",      "    result = arg1 or arg2\n",                                        2, 1.0, "OR"),
    CodeGene("logic_not",     "    result = not arg1\n",                                            1, 1.0, "NOT"),
    CodeGene("logic_compare", "    result = (arg1==arg2) if arg3=='==' else (arg1>arg2) if arg3=='>' else (arg1<arg2) if arg3=='<' else (arg1!=arg2)\n", 3, 2.5, "perbandingan dinamis"),
    CodeGene("logic_in_range","    result = arg2 <= arg1 <= arg3\n",                                3, 2.0, "cek rentang"),
    CodeGene("logic_is_instance","  result = isinstance(arg1, arg2)\n",                             2, 1.5, "cek tipe"),
    CodeGene("logic_coalesce","    result = next((x for x in [arg1, arg2] if x is not None), None)\n", 2, 2.0, "null coalescing"),

    # --- TYPE CONVERSION & VALIDATION ---
    CodeGene("try_parse_int", "    try: result = int(arg1)\n    except: result = 0\n",              1, 2.0, "safe int parse"),
    CodeGene("try_parse_float","   try: result = float(arg1)\n    except: result = 0.0\n",          1, 2.0, "safe float parse"),
    CodeGene("val_is_not_none","   result = arg1 is not None\n",                                    1, 1.0, "non-null check"),
    CodeGene("val_to_bool",   "    result = bool(arg1)\n",                                          1, 1.0, "ke bool"),
    CodeGene("val_type_name", "    result = type(arg1).__name__\n",                                 1, 1.2, "nama tipe"),

    # --- TERMINAL ---
    CodeGene("return_res",    "    return result\n",                                                0, 0.5, "return hasil"),
]


# ─────────────────────────────────────────────────────────────────────────────
# SANDBOX
# ─────────────────────────────────────────────────────────────────────────────

class AdvancedSandbox:
    SAFE_BUILTINS = {
        "range": range, "len": len, "str": str, "int": int, "float": float,
        "bool": bool, "list": list, "dict": dict, "set": set, "tuple": tuple,
        "sum": sum, "max": max, "min": min, "abs": abs, "round": round,
        "enumerate": enumerate, "zip": zip, "sorted": sorted,
        "reversed": reversed, "any": any, "all": all, "type": type,
        "isinstance": isinstance, "next": next, "iter": iter,
        "print": lambda *x: None, "math": math, "re": re,
        "statistics": statistics, "itertools": itertools,
    }

    def __init__(self, timeout: float = 2.0):
        self.timeout = timeout

    def execute(
        self, code: str, func_name: str, args: tuple
    ) -> Tuple[bool, Any, float, float, str]:
        result = {"output": None, "error": None, "success": False, "exec_time": 0.0}

        def target():
            start = time.perf_counter()
            safe_globals = {"__builtins__": self.SAFE_BUILTINS}
            local_env = {}
            try:
                exec(code, safe_globals, local_env)
                if func_name in local_env:
                    res = local_env[func_name](*args)
                    result["output"] = res
                    result["success"] = True
                else:
                    result["error"] = f"Function '{func_name}' not found."
            except Exception as e:
                result["error"] = f"{type(e).__name__}: {str(e)}"
            finally:
                result["exec_time"] = time.perf_counter() - start

        t = threading.Thread(target=target)
        t.start()
        t.join(self.timeout)

        if t.is_alive():
            return False, None, self.timeout, 0.0, "TimeoutError"

        mem = 0.0
        if result["output"] is not None:
            try:
                mem = len(repr(result["output"])) * 8
            except:
                pass

        return (
            result["success"], result["output"],
            result["exec_time"], mem, result["error"],
        )


# ─────────────────────────────────────────────────────────────────────────────
# KNOWLEDGE BASE  (extended dengan tabel experience)
# ─────────────────────────────────────────────────────────────────────────────

class KnowledgeBase:
    def __init__(self, db_path: str = "memory/evolution/knowledge.db"):
        import sqlite3
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self.lock:
            c = self.conn.cursor()
            c.executescript("""
                CREATE TABLE IF NOT EXISTS solutions (
                    task_id TEXT PRIMARY KEY,
                    code TEXT, fitness REAL, exec_time REAL,
                    mem_estimate REAL, created_at REAL, last_used REAL,
                    use_count INTEGER, version INTEGER
                );
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id TEXT PRIMARY KEY, population TEXT,
                    generation INTEGER, task_id TEXT, timestamp REAL
                );
                CREATE TABLE IF NOT EXISTS gene_experience (
                    gene_id TEXT PRIMARY KEY,
                    weight REAL NOT NULL DEFAULT 1.0,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    last_updated REAL
                );
                CREATE TABLE IF NOT EXISTS gene_transitions (
                    from_gene TEXT NOT NULL,
                    to_gene TEXT NOT NULL,
                    weight REAL NOT NULL DEFAULT 1.0,
                    last_updated REAL,
                    PRIMARY KEY (from_gene, to_gene)
                );
                CREATE TABLE IF NOT EXISTS gene_patterns (
                    pattern_key TEXT PRIMARY KEY,
                    gene_ids TEXT NOT NULL,
                    avg_fitness REAL,
                    occurrence_count INTEGER DEFAULT 1,
                    last_seen REAL
                );
            """)
            self.conn.commit()

    # ── Solutions ──────────────────────────────────────────────────────────
    def get_solution(self, task_id: str) -> Optional[Solution]:
        with self.lock:
            c = self.conn.cursor()
            c.execute("SELECT * FROM solutions WHERE task_id = ?", (task_id,))
            row = c.fetchone()
            return Solution(*row) if row else None

    def save_solution(self, sol: Solution):
        with self.lock:
            c = self.conn.cursor()
            c.execute(
                "INSERT OR REPLACE INTO solutions VALUES (?,?,?,?,?,?,?,?,?)",
                (sol.task_id, sol.code, sol.fitness, sol.execution_time,
                 sol.memory_estimate, sol.created_at, sol.last_used,
                 sol.use_count, sol.version)
            )
            self.conn.commit()

    def update_usage(self, task_id: str):
        with self.lock:
            c = self.conn.cursor()
            c.execute(
                "UPDATE solutions SET last_used=?, use_count=use_count+1 WHERE task_id=?",
                (time.time(), task_id)
            )
            self.conn.commit()

    def get_all_solutions(self) -> List[Solution]:
        with self.lock:
            c = self.conn.cursor()
            c.execute("SELECT * FROM solutions ORDER BY fitness DESC")
            return [Solution(*row) for row in c.fetchall()]

    # ── Checkpoints ────────────────────────────────────────────────────────
    def save_checkpoint(self, ckpt_id: str, population: List[Genome], generation: int, task_id: str):
        data = [
            {"genes": [g.id for g in gm.genes], "fitness": gm.fitness,
             "generation": gm.generation, "parent_ids": list(gm.parent_ids),
             "exec_time": gm.execution_time, "mem": gm.memory_estimate,
             "island_id": gm.island_id}
            for gm in population
        ]
        with self.lock:
            c = self.conn.cursor()
            c.execute(
                "INSERT OR REPLACE INTO checkpoints VALUES (?,?,?,?,?)",
                (ckpt_id, json.dumps(data), generation, task_id, time.time())
            )
            self.conn.commit()

    def load_checkpoint(
        self, ckpt_id: str, gene_pool: Dict[str, "CodeGene"]
    ) -> Tuple[List[Genome], int, str]:
        with self.lock:
            c = self.conn.cursor()
            c.execute("SELECT population, generation, task_id FROM checkpoints WHERE id=?", (ckpt_id,))
            row = c.fetchone()
            if not row:
                raise ValueError("Checkpoint not found")
            data, generation, task_id = json.loads(row[0]), row[1], row[2]
            population = []
            for d in data:
                genes = [gene_pool[gid] for gid in d["genes"] if gid in gene_pool]
                gm = Genome(
                    genes=genes, fitness=d.get("fitness", 0.0),
                    generation=d.get("generation", 0),
                    parent_ids=tuple(d.get("parent_ids", ("", ""))),
                    execution_time=d.get("exec_time", 0.0),
                    memory_estimate=d.get("mem", 0.0),
                    island_id=d.get("island_id", 0),
                )
                population.append(gm)
            return population, generation, task_id

    # ── Gene Experience ────────────────────────────────────────────────────
    def save_gene_weights(self, weights: Dict[str, float], success: Dict[str, int], failure: Dict[str, int]):
        now = time.time()
        with self.lock:
            c = self.conn.cursor()
            for gid, w in weights.items():
                c.execute("""
                    INSERT OR REPLACE INTO gene_experience
                    VALUES (?, ?, ?, ?, ?)
                """, (gid, w, success.get(gid, 0), failure.get(gid, 0), now))
            self.conn.commit()

    def load_gene_weights(self) -> Dict[str, Tuple[float, int, int]]:
        """Returns {gene_id: (weight, success_count, failure_count)}"""
        with self.lock:
            c = self.conn.cursor()
            c.execute("SELECT gene_id, weight, success_count, failure_count FROM gene_experience")
            return {row[0]: (row[1], row[2], row[3]) for row in c.fetchall()}

    def save_gene_transitions(self, transitions: Dict[str, Dict[str, float]]):
        now = time.time()
        with self.lock:
            c = self.conn.cursor()
            for from_g, to_dict in transitions.items():
                for to_g, w in to_dict.items():
                    c.execute("""
                        INSERT OR REPLACE INTO gene_transitions VALUES (?,?,?,?)
                    """, (from_g, to_g, w, now))
            self.conn.commit()

    def load_gene_transitions(self) -> Dict[str, Dict[str, float]]:
        with self.lock:
            c = self.conn.cursor()
            c.execute("SELECT from_gene, to_gene, weight FROM gene_transitions")
            result: Dict[str, Dict[str, float]] = defaultdict(dict)
            for row in c.fetchall():
                result[row[0]][row[1]] = row[2]
            return dict(result)

    def save_patterns(self, patterns: List[GenePattern]):
        now = time.time()
        with self.lock:
            c = self.conn.cursor()
            for p in patterns:
                key = "|".join(p.gene_ids)
                c.execute("""
                    INSERT OR REPLACE INTO gene_patterns VALUES (?,?,?,?,?)
                """, (key, json.dumps(p.gene_ids), p.avg_fitness, p.occurrence_count, now))
            self.conn.commit()

    def load_patterns(self) -> List[GenePattern]:
        with self.lock:
            c = self.conn.cursor()
            c.execute("SELECT gene_ids, avg_fitness, occurrence_count, last_seen FROM gene_patterns ORDER BY avg_fitness DESC")
            result = []
            for row in c.fetchall():
                result.append(GenePattern(
                    gene_ids=json.loads(row[0]),
                    avg_fitness=row[1],
                    occurrence_count=row[2],
                    last_seen=row[3],
                ))
            return result

    def close(self):
        self.conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# ██████╗ GENE GAUNTLET  — Pipeline validasi 6 stage
# ─────────────────────────────────────────────────────────────────────────────

class GeneGauntlet:
    """
    Sistem seleksi alam untuk gen kandidat.
    Gen yang lemah tidak akan pernah mencemari pool.

    Stage 0: Complexity Scorer   — beri skor awal, tidak eliminasi
    Stage 1: Syntax Gauntlet     — syntax valid + tidak berbahaya
    Stage 2: Type Diversity Test — bertahan dengan berbagai tipe input
    Stage 3: Edge Case Stress    — tahan terhadap input ekstrem
    Stage 4: Uniqueness Gauntlet — perilaku unik vs pool yang ada
    Stage 5: Performance Bench   — tidak terlalu lambat
    """

    # Input sintetis untuk pengujian (beragam tipe)
    _TYPE_INPUTS = [
        (5, 3),
        (3.14, 2.0),
        ("hello", "world"),
        ([1, 2, 3], [4, 5, 6]),
        ({"a": 1}, {"b": 2}),
        (0, 1),
        (True, False),
        (100, 0),
    ]

    _EDGE_INPUTS = [
        (None, None),
        (0, 0),
        ("", ""),
        ([], []),
        ({}, {}),
        (-1, -999),
        (float("inf"), 1),
        ([None, None], 0),
        ("héllo wörld", "ö"),
        ([1, [2, [3]]], 0),
        (10**15, 10**15),
        (0.0000001, 0.0000001),
    ]

    # Op/builtins berbahaya yang dilarang ada dalam template
    _FORBIDDEN_NODES = {
        "Import", "ImportFrom", "Global", "Nonlocal",
        "AsyncFunctionDef", "AsyncFor", "AsyncWith",
    }
    _FORBIDDEN_NAMES = {
        "exec", "eval", "compile", "__import__", "open",
        "input", "breakpoint", "exit", "quit", "globals", "locals",
        "vars", "setattr", "delattr", "getattr", "__builtins__",
    }

    def __init__(self, config: "EvolutionConfig", existing_pool: Dict[str, "CodeGene"]):
        self.config = config
        self.existing_pool = existing_pool
        self.sandbox_globals = {
            "__builtins__": {
                "range": range, "len": len, "str": str, "int": int, "float": float,
                "bool": bool, "list": list, "dict": dict, "set": set, "tuple": tuple,
                "sum": sum, "max": max, "min": min, "abs": abs, "round": round,
                "enumerate": enumerate, "zip": zip, "sorted": sorted,
                "reversed": reversed, "any": any, "all": all, "type": type,
                "isinstance": isinstance, "next": next, "iter": iter,
                "print": lambda *x: None, "math": math, "re": re,
                "statistics": statistics, "itertools": itertools,
                "hasattr": hasattr,
            }
        }

    def run(self, gene_id: str, template: str, arity: int) -> Tuple[bool, float, str]:
        """
        Jalankan semua stage gauntlet.
        Returns: (lolos: bool, skor_akhir: float, alasan_gagal: str)
        """
        scores: Dict[str, float] = {}
        stage_weights = {
            "complexity": 0.10,
            "syntax":     0.25,
            "type_div":   0.20,
            "edge_case":  0.20,
            "uniqueness": 0.15,
            "performance":0.10,
        }

        # ── Stage 0: Complexity Scorer ─────────────────────────────────────
        scores["complexity"] = self._stage0_complexity(template)

        # ── Stage 1: Syntax Gauntlet ───────────────────────────────────────
        syntax_ok, syntax_score, reason = self._stage1_syntax(template)
        scores["syntax"] = syntax_score
        if not syntax_ok:
            return False, 0.0, f"[Stage1-Syntax] {reason}"

        # ── Stage 2: Type Diversity ────────────────────────────────────────
        scores["type_div"] = self._stage2_type_diversity(gene_id, template, arity)

        # ── Stage 3: Edge Case Stress ──────────────────────────────────────
        scores["edge_case"] = self._stage3_edge_cases(gene_id, template, arity)

        # ── Stage 4: Uniqueness ────────────────────────────────────────────
        scores["uniqueness"] = self._stage4_uniqueness(gene_id, template, arity)

        # ── Stage 5: Performance ───────────────────────────────────────────
        perf_ok, perf_score, reason = self._stage5_performance(gene_id, template, arity)
        scores["performance"] = perf_score
        if not perf_ok:
            return False, 0.0, f"[Stage5-Performance] {reason}"

        # ── Final Score ────────────────────────────────────────────────────
        final = sum(scores[k] * stage_weights[k] for k in stage_weights)

        if final < self.config.gauntlet_min_score:
            return False, final, f"Score too low ({final:.3f} < {self.config.gauntlet_min_score})"

        return True, final, "passed"

    # ── Stage 0 ────────────────────────────────────────────────────────────
    def _stage0_complexity(self, template: str) -> float:
        """
        Analisis struktur kode:
        - Terlalu sederhana (hanya assignment literal) → skor rendah
        - Punya kondisional/comprehension/operasi → skor tinggi
        - Terlalu panjang/berlapis → skor turun (over-complex)
        """
        try:
            wrapped = f"def _probe():\n{template}\n    return result"
            tree = ast.parse(wrapped)
            nodes = list(ast.walk(tree))

            n_nodes = len(nodes)
            has_conditional = any(isinstance(n, (ast.IfExp, ast.If)) for n in nodes)
            has_comprehension = any(isinstance(n, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)) for n in nodes)
            has_try = any(isinstance(n, ast.Try) for n in nodes)
            has_call = any(isinstance(n, ast.Call) for n in nodes)
            has_binop = any(isinstance(n, ast.BinOp) for n in nodes)
            has_compare = any(isinstance(n, ast.Compare) for n in nodes)
            n_lines = len([l for l in template.strip().split("\n") if l.strip()])

            score = 0.3  # baseline
            if has_binop:     score += 0.10
            if has_call:      score += 0.15
            if has_conditional: score += 0.15
            if has_comprehension: score += 0.15
            if has_try:       score += 0.10
            if has_compare:   score += 0.05

            # Penalize extremes
            if n_nodes > 80:  score -= 0.2   # terlalu kompleks
            if n_lines > 6:   score -= 0.1   # terlalu panjang
            if n_nodes < 5:   score -= 0.15  # terlalu trivial

            return max(0.0, min(1.0, score))
        except Exception:
            return 0.2

    # ── Stage 1 ────────────────────────────────────────────────────────────
    def _stage1_syntax(self, template: str) -> Tuple[bool, float, str]:
        """Syntax check + keamanan (tidak boleh ada node berbahaya)."""
        try:
            wrapped = f"def _probe(arg1=None, arg2=None, arg3=None):\n    result = None\n{template}\n    return result"
            tree = ast.parse(wrapped)
        except SyntaxError as e:
            return False, 0.0, f"SyntaxError: {e}"

        for node in ast.walk(tree):
            ntype = type(node).__name__
            if ntype in self._FORBIDDEN_NODES:
                return False, 0.0, f"Forbidden node: {ntype}"
            if isinstance(node, ast.Name) and node.id in self._FORBIDDEN_NAMES:
                return False, 0.0, f"Forbidden name: {node.id}"
            if isinstance(node, ast.Attribute) and node.attr in self._FORBIDDEN_NAMES:
                return False, 0.0, f"Forbidden attr: {node.attr}"
            # Cek infinite loop risk
            if isinstance(node, ast.While):
                return False, 0.0, "While loop not allowed in gene template"

        return True, 1.0, "ok"

    # ── Stage 2 ────────────────────────────────────────────────────────────
    def _stage2_type_diversity(self, gene_id: str, template: str, arity: int) -> float:
        """Test bertahan dengan berbagai tipe input."""
        survived = 0
        total = 0

        for inp_tuple in self._TYPE_INPUTS:
            args = inp_tuple[:max(arity, 1)]
            if len(args) < arity:
                args = args + (None,) * (arity - len(args))

            ok, _ = self._exec_template(template, args, gene_id)
            total += 1
            if ok:
                survived += 1

        return survived / max(total, 1)

    # ── Stage 3 ────────────────────────────────────────────────────────────
    def _stage3_edge_cases(self, gene_id: str, template: str, arity: int) -> float:
        """Test ketahanan terhadap input ekstrem."""
        survived = 0
        total = 0

        for inp_tuple in self._EDGE_INPUTS:
            args = inp_tuple[:max(arity, 1)]
            if len(args) < arity:
                args = args + (None,) * (arity - len(args))

            ok, _ = self._exec_template(template, args, gene_id)
            total += 1
            if ok:
                survived += 1

        # Edge case lebih sulit → punya credit lebih
        base = survived / max(total, 1)
        # bonus kalau selamat di None dan overflow
        return base

    # ── Stage 4 ────────────────────────────────────────────────────────────
    def _stage4_uniqueness(self, gene_id: str, template: str, arity: int) -> float:
        """
        Ukur seberapa berbeda perilaku gen ini vs gen yang sudah ada.
        Gen yang outputnya identik dengan gen lain = rendah nilainya.
        """
        # Kumpulkan output gen kandidat
        candidate_outputs = []
        for inp_tuple in self._TYPE_INPUTS[:6]:
            args = inp_tuple[:max(arity, 1)]
            if len(args) < arity:
                args = args + (None,) * (arity - len(args))
            _, out = self._exec_template(template, args, gene_id)
            candidate_outputs.append(repr(out))

        candidate_fp = hashlib.md5("|".join(candidate_outputs).encode()).hexdigest()

        # Bandingkan dengan semua gen di pool
        matching = 0
        total_compared = 0
        for existing_gene in list(self.existing_pool.values())[:30]:  # sample 30
            if existing_gene.id == gene_id:
                continue
            existing_outputs = []
            for inp_tuple in self._TYPE_INPUTS[:6]:
                args = inp_tuple[:max(existing_gene.arity, 1)]
                if len(args) < existing_gene.arity:
                    args = args + (None,) * (existing_gene.arity - len(args))
                _, out = self._exec_template(existing_gene.template, args, existing_gene.id)
                existing_outputs.append(repr(out))
            existing_fp = hashlib.md5("|".join(existing_outputs).encode()).hexdigest()
            if existing_fp == candidate_fp:
                matching += 1
            total_compared += 1

        if total_compared == 0:
            return 1.0

        duplicate_ratio = matching / total_compared
        # Makin banyak duplikat → skor rendah
        return max(0.0, 1.0 - duplicate_ratio * 3.0)

    # ── Stage 5 ────────────────────────────────────────────────────────────
    def _stage5_performance(self, gene_id: str, template: str, arity: int) -> Tuple[bool, float, str]:
        """Benchmark kecepatan eksekusi."""
        times = []
        n_runs = 8
        sample_inputs = self._TYPE_INPUTS[:n_runs]

        for inp_tuple in sample_inputs:
            args = inp_tuple[:max(arity, 1)]
            if len(args) < arity:
                args = args + (None,) * (arity - len(args))
            t0 = time.perf_counter()
            ok, _ = self._exec_template(template, args, gene_id)
            elapsed = time.perf_counter() - t0
            times.append(elapsed)

        avg_time = sum(times) / len(times) if times else 1.0
        max_time = max(times) if times else 1.0

        hard_limit = self.config.gauntlet_timeout
        if max_time > hard_limit * 2:
            return False, 0.0, f"Too slow: max={max_time:.3f}s"

        # Score: exponential decay berdasarkan waktu
        score = math.exp(-avg_time / (hard_limit * 0.5))
        return True, score, "ok"

    # ── Helper ─────────────────────────────────────────────────────────────
    def _exec_template(
        self, template: str, args: tuple, probe_name: str
    ) -> Tuple[bool, Any]:
        """Eksekusi template dengan args, return (success, output)."""
        arity = len(args)
        arg_str = ", ".join(f"arg{i+1}" for i in range(arity))
        code = (
            f"def _probe({arg_str}):\n"
            f"    result = None\n"
            f"{template}\n"
            f"    return result\n"
        )
        result = {"ok": False, "out": None}

        def _run():
            env = {}
            try:
                exec(code, dict(self.sandbox_globals), env)
                result["out"] = env["_probe"](*args)
                result["ok"] = True
            except Exception:
                result["ok"] = False

        t = threading.Thread(target=_run)
        t.start()
        t.join(self.config.gauntlet_timeout)
        return result["ok"], result["out"]

    def determine_initial_weight(self, gauntlet_score: float) -> float:
        """Tentukan bobot awal gen berdasarkan skor gauntlet."""
        if gauntlet_score >= self.config.gauntlet_elite_threshold:
            return self.config.gauntlet_elite_weight
        elif gauntlet_score >= self.config.gauntlet_probationary_threshold:
            return self.config.gauntlet_standard_weight
        else:
            return self.config.gauntlet_probationary_weight


# ─────────────────────────────────────────────────────────────────────────────
# ██████╗ GENE SYNTHESIZER  — Distilasi kode sukses → gen baru
# ─────────────────────────────────────────────────────────────────────────────

class GeneSynthesizer:
    """
    Mengamati kode yang berhasil berevolusi, lalu mendistilasi
    pernyataan-pernyataan yang berkontribusi menjadi CodeGene baru.
    """

    def __init__(self, gauntlet: GeneGauntlet, config: "EvolutionConfig"):
        self.gauntlet = gauntlet
        self.config = config
        self._seen_templates: Set[str] = set()

    def synthesize_from_genome(self, genome: "Genome") -> List["CodeGene"]:
        """Ekstrak gen baru dari genome yang sukses."""
        if not genome.compiled_code:
            return []

        try:
            tree = ast.parse(genome.compiled_code)
        except SyntaxError:
            return []

        candidates: List["CodeGene"] = []

        for func_node in ast.walk(tree):
            if not isinstance(func_node, ast.FunctionDef):
                continue

            stmts = [s for s in func_node.body if not isinstance(s, ast.Return)]

            for stmt in stmts:
                try:
                    template = self._stmt_to_template(stmt)
                    if not template:
                        continue

                    template_key = hashlib.md5(template.encode()).hexdigest()
                    if template_key in self._seen_templates:
                        continue
                    self._seen_templates.add(template_key)

                    arity = self._infer_arity(template)
                    gene_id = f"syn_{template_key[:10]}"

                    passed, score, reason = self.gauntlet.run(gene_id, template, arity)
                    if passed:
                        gene = CodeGene(
                            id=gene_id,
                            template=template,
                            arity=arity,
                            complexity=self._estimate_complexity(template),
                            description=f"synthesized from evolved code",
                            origin="synthesized",
                            gauntlet_score=score,
                            is_probationary=(score < self.config.gauntlet_probationary_threshold),
                            added_at=time.time(),
                            source_hint="genome_synthesis",
                        )
                        candidates.append(gene)

                except Exception:
                    continue

                if len(candidates) >= self.config.synthesizer_max_per_run:
                    break
            if len(candidates) >= self.config.synthesizer_max_per_run:
                break

        return candidates

    def _stmt_to_template(self, stmt: ast.stmt) -> Optional[str]:
        """Ubah AST statement menjadi template gen (dengan result=..., argN)."""
        try:
            src = ast.unparse(stmt)
        except Exception:
            return None

        if not src.strip():
            return None

        # Normalisasi: ganti nama variabel spesifik dengan arg1, arg2, result
        # Heuristic: variabel yang bukan builtins dan bukan result → arg1, arg2
        src = self._normalize_variables(src)

        # Harus ada 'result' di dalamnya
        if "result" not in src:
            src = f"result = {src.rstrip()}"

        template = f"    {src.strip()}\n"
        # Bersihkan kalau ada multi-line yang aneh
        if len(template.split("\n")) > 5:
            return None

        return template

    def _normalize_variables(self, src: str) -> str:
        """
        Heuristic: rename local variables ke arg1, arg2, result.
        Ini jauh dari sempurna, tapi cukup untuk gene template.
        """
        # Ganti assignment target ke 'result'
        src = re.sub(r'^(\w+)\s*=', 'result =', src, count=1)
        return src

    def _infer_arity(self, template: str) -> int:
        """Cari arg1, arg2, arg3 yang dipakai di template."""
        for n in range(3, 0, -1):
            if f"arg{n}" in template:
                return n
        return 1

    def _estimate_complexity(self, template: str) -> float:
        try:
            tree = ast.parse(f"def _f():\n{template}")
            return len(list(ast.walk(tree))) / 20.0
        except Exception:
            return 1.0


# ─────────────────────────────────────────────────────────────────────────────
# ██████╗ CODE HARVESTER  — Scan filesystem → gen baru
# ─────────────────────────────────────────────────────────────────────────────

class CodeHarvester:
    """
    Menjelajahi filesystem dan mengekstrak pola kode berguna
    dari file teks apapun untuk dijadikan gen kandidat.
    """

    # Pattern regex untuk menangkap ekspresi Python-like dari teks apapun
    _PY_EXPR_PATTERNS = [
        # assignment dengan operasi
        r'(\w+)\s*=\s*([^=\n;{]+(?:\([^)]*\))?[^=\n;{]*)',
        # list/dict comprehension
        r'\[([^\[\]]+)\s+for\s+\w+\s+in\s+[^\[\]]+\]',
        r'\{([^{}]+)\s+for\s+\w+\s+in\s+[^{}]+\}',
    ]

    def __init__(self, gauntlet: GeneGauntlet, config: "EvolutionConfig"):
        self.gauntlet = gauntlet
        self.config = config
        self._scanned_files: Set[str] = set()
        self._seen_templates: Set[str] = set()

    def harvest(self, root_paths: List[str]) -> List["CodeGene"]:
        """
        Scan direktori dan ekstrak gen kandidat.
        root_paths: list direktori yang akan di-scan.
        """
        all_candidates: List["CodeGene"] = []
        files_scanned = 0

        for root in root_paths:
            if not os.path.exists(root):
                continue
            for dirpath, dirnames, filenames in os.walk(root):
                # Skip direktori tersembunyi & cache
                dirnames[:] = [
                    d for d in dirnames
                    if not d.startswith(".")
                    and d not in {"__pycache__", "node_modules", ".git", "venv", ".venv"}
                ]
                for fname in filenames:
                    if files_scanned >= self.config.harvester_max_files:
                        return all_candidates
                    fpath = os.path.join(dirpath, fname)
                    if fpath in self._scanned_files:
                        continue
                    # Cek apakah file teks (by extension atau content)
                    if not self._is_text_file(fpath):
                        continue
                    self._scanned_files.add(fpath)
                    files_scanned += 1

                    ext = Path(fpath).suffix.lower()
                    if ext == ".py":
                        genes = self._harvest_python_file(fpath)
                    else:
                        genes = self._harvest_text_file(fpath)

                    all_candidates.extend(genes)

        return all_candidates

    def _is_text_file(self, fpath: str) -> bool:
        ext = Path(fpath).suffix.lower()
        if ext in self.config.harvester_scan_extensions:
            return True
        # Coba baca 512 byte pertama
        try:
            with open(fpath, "rb") as f:
                chunk = f.read(512)
            return b"\x00" not in chunk  # binary file biasanya punya null bytes
        except Exception:
            return False

    def _harvest_python_file(self, fpath: str) -> List["CodeGene"]:
        """Ekstrak fungsi dan ekspresi berguna dari file Python via AST."""
        candidates: List["CodeGene"] = []
        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                source = f.read()
            tree = ast.parse(source)
        except Exception:
            return candidates

        for node in ast.walk(tree):
            if len(candidates) >= self.config.harvester_max_genes_per_file:
                break
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Ekstrak body statements yang sederhana (bukan loop besar)
                for stmt in node.body:
                    if isinstance(stmt, (ast.Assign, ast.AugAssign, ast.Expr, ast.Return, ast.If)):
                        gene = self._stmt_to_gene(stmt, fpath)
                        if gene:
                            candidates.append(gene)
                    if len(candidates) >= self.config.harvester_max_genes_per_file:
                        break

        return candidates

    def _harvest_text_file(self, fpath: str) -> List["CodeGene"]:
        """Coba ekstrak ekspresi Python-like dari file teks non-.py."""
        candidates: List["CodeGene"] = []
        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except Exception:
            return candidates

        for line in lines:
            if len(candidates) >= self.config.harvester_max_genes_per_file:
                break
            line = line.strip()
            if not line or len(line) > 200:
                continue

            # Coba parse sebagai Python expression/statement
            for candidate_template in self._extract_from_line(line):
                gene = self._template_to_gene(candidate_template, fpath)
                if gene:
                    candidates.append(gene)

        return candidates

    def _extract_from_line(self, line: str) -> List[str]:
        """Coba ekstrak ekspresi Python dari baris teks."""
        results = []
        for pat in self._PY_EXPR_PATTERNS:
            for m in re.finditer(pat, line):
                expr = m.group(0).strip()
                # Normalisasi ke template
                tmpl = self._normalize_to_template(expr)
                if tmpl:
                    results.append(tmpl)
        return results[:3]

    def _normalize_to_template(self, expr: str) -> Optional[str]:
        """Ubah ekspresi mentah ke template gen (result = ..., argN)."""
        expr = expr.strip()
        if not expr:
            return None
        # Pastikan ada '='
        if "=" not in expr:
            expr = f"result = {expr}"
        else:
            # Ganti target ke result
            expr = re.sub(r'^\w+\s*=\s*', 'result = ', expr, count=1)
        template = f"    {expr}\n"
        try:
            ast.parse(f"def _f(arg1=None, arg2=None, arg3=None):\n    result=None\n{template}")
            return template
        except Exception:
            return None

    def _stmt_to_gene(self, stmt: ast.stmt, fpath: str) -> Optional["CodeGene"]:
        """Konversi AST statement dari file Python menjadi CodeGene."""
        try:
            src = ast.unparse(stmt)
        except Exception:
            return None

        template = self._normalize_to_template(src)
        if not template:
            return None

        return self._template_to_gene(template, fpath)

    def _template_to_gene(self, template: str, source_path: str) -> Optional["CodeGene"]:
        """Validasi template via gauntlet dan buat CodeGene."""
        template_key = hashlib.md5(template.encode()).hexdigest()
        if template_key in self._seen_templates:
            return None
        self._seen_templates.add(template_key)

        arity = self._infer_arity(template)
        gene_id = f"hrv_{template_key[:10]}"

        try:
            passed, score, reason = self.gauntlet.run(gene_id, template, arity)
        except Exception:
            return None

        if not passed:
            return None

        return CodeGene(
            id=gene_id,
            template=template,
            arity=arity,
            complexity=1.0,
            description=f"harvested from {Path(source_path).name}",
            origin="harvested",
            gauntlet_score=score,
            is_probationary=(score < self.config.gauntlet_probationary_threshold),
            added_at=time.time(),
            source_hint=source_path,
        )

    def _infer_arity(self, template: str) -> int:
        for n in range(3, 0, -1):
            if f"arg{n}" in template:
                return n
        return 1


# ─────────────────────────────────────────────────────────────────────────────
# ██████╗ TEMPLATE MUTATOR  — Mutasi gen yang ada → varian baru
# ─────────────────────────────────────────────────────────────────────────────

class TemplateMutator:
    """
    Mengambil gen yang sudah ada di pool dan membuat varian
    melalui mutasi di level AST. Bukan menghasilkan kode baru dari nol —
    tapi memodifikasi kode yang sudah terbukti layak.
    """

    # Mapping operator untuk substitusi
    _BINOP_SUBSTITUTIONS = [
        (ast.Add, ast.Sub), (ast.Sub, ast.Add),
        (ast.Mult, ast.Div), (ast.Div, ast.Mult),
        (ast.Mod, ast.FloorDiv), (ast.FloorDiv, ast.Mod),
        (ast.BitAnd, ast.BitOr), (ast.BitOr, ast.BitAnd),
    ]
    _CMPOP_SUBSTITUTIONS = [
        (ast.Lt, ast.LtE), (ast.Gt, ast.GtE),
        (ast.Eq, ast.NotEq),
    ]

    def __init__(self, gauntlet: GeneGauntlet, config: "EvolutionConfig"):
        self.gauntlet = gauntlet
        self.config = config
        self._seen: Set[str] = set()

    def mutate_gene(self, gene: "CodeGene") -> Optional["CodeGene"]:
        """
        Coba berbagai mutasi pada gen yang ada.
        Pilih satu mutasi secara acak dan test via gauntlet.
        """
        mutations = [
            self._mutate_operator,
            self._mutate_add_guard,
            self._mutate_swap_args,
            self._mutate_add_default,
            self._mutate_wrap_try,
        ]
        random.shuffle(mutations)

        for mut_fn in mutations:
            try:
                new_template = mut_fn(gene.template)
                if not new_template or new_template == gene.template:
                    continue

                key = hashlib.md5(new_template.encode()).hexdigest()
                if key in self._seen:
                    continue
                self._seen.add(key)

                arity = self._infer_arity(new_template)
                gene_id = f"mut_{key[:10]}"

                passed, score, _ = self.gauntlet.run(gene_id, new_template, arity)
                if passed:
                    return CodeGene(
                        id=gene_id,
                        template=new_template,
                        arity=arity,
                        complexity=gene.complexity * random.uniform(0.8, 1.3),
                        description=f"mutated from {gene.id}",
                        origin="mutated",
                        gauntlet_score=score,
                        is_probationary=(score < self.config.gauntlet_probationary_threshold),
                        added_at=time.time(),
                        source_hint=f"parent:{gene.id}",
                    )
            except Exception:
                continue
        return None

    # ── Mutation Strategies ────────────────────────────────────────────────

    def _mutate_operator(self, template: str) -> Optional[str]:
        """Ganti operator aritmatika/perbandingan secara acak."""
        try:
            wrapped = f"def _f(arg1=None, arg2=None, arg3=None):\n    result=None\n{template}"
            tree = ast.parse(wrapped)

            class OpReplacer(ast.NodeTransformer):
                def __init__(self):
                    self.changed = False
                def visit_BinOp(self, node):
                    if self.changed:
                        return node
                    for old_op, new_op in TemplateMutator._BINOP_SUBSTITUTIONS:
                        if isinstance(node.op, old_op) and random.random() < 0.4:
                            node.op = new_op()
                            self.changed = True
                            break
                    return node
                def visit_Compare(self, node):
                    if self.changed:
                        return node
                    new_ops = []
                    for op in node.ops:
                        changed_op = op
                        for old_op, new_op in TemplateMutator._CMPOP_SUBSTITUTIONS:
                            if isinstance(op, old_op) and random.random() < 0.4:
                                changed_op = new_op()
                                self.changed = True
                                break
                        new_ops.append(changed_op)
                    node.ops = new_ops
                    return node

            replacer = OpReplacer()
            new_tree = replacer.visit(copy.deepcopy(tree))
            if not replacer.changed:
                return None
            ast.fix_missing_locations(new_tree)
            new_src = ast.unparse(new_tree)
            # Ambil kembali hanya bagian template (hapus def wrapper)
            lines = new_src.split("\n")[2:]  # skip def dan result=None
            return "\n".join("    " + l.strip() for l in lines if l.strip() and l.strip() != "return result") + "\n"
        except Exception:
            return None

    def _mutate_add_guard(self, template: str) -> Optional[str]:
        """Tambahkan guard None/type check di awal template."""
        guards = [
            "    if arg1 is None: return None\n",
            "    if not isinstance(arg1, (int, float, list, str, dict)): return None\n",
            "    arg1 = arg1 if arg1 is not None else 0\n",
        ]
        guard = random.choice(guards)
        return guard + template

    def _mutate_swap_args(self, template: str) -> Optional[str]:
        """Tukar arg1 dan arg2 jika keduanya ada."""
        if "arg1" in template and "arg2" in template:
            new = template.replace("arg1", "__TMP__").replace("arg2", "arg1").replace("__TMP__", "arg2")
            return new if new != template else None
        return None

    def _mutate_add_default(self, template: str) -> Optional[str]:
        """Tambahkan fallback default jika result masih None setelah eksekusi."""
        return template + "    result = result if result is not None else arg1\n"

    def _mutate_wrap_try(self, template: str) -> Optional[str]:
        """Bungkus template dalam try/except sederhana."""
        indented = "".join("    " + line for line in template.split("\n") if line.strip())
        return f"    try:\n{indented}\n    except Exception:\n        result = None\n"

    def _infer_arity(self, template: str) -> int:
        for n in range(3, 0, -1):
            if f"arg{n}" in template:
                return n
        return 1


# ─────────────────────────────────────────────────────────────────────────────
# ██████╗ SELF-REFLECTIVE SCANNER  — Engine introspeksi source code-nya sendiri
# ─────────────────────────────────────────────────────────────────────────────

class SelfReflectiveScanner:
    """
    Engine membaca source code-nya sendiri dan mengekstrak
    sub-ekspresi atau pola yang bisa dijadikan gen baru.
    Ini fitur paling 'metacognitive' dari seluruh sistem.
    """

    def __init__(self, gauntlet: GeneGauntlet, config: "EvolutionConfig"):
        self.gauntlet = gauntlet
        self.config = config
        self._seen: Set[str] = set()
        self._own_source: Optional[str] = None

    def _get_own_source(self) -> str:
        """Ambil source code file ini sendiri."""
        if self._own_source:
            return self._own_source
        try:
            own_file = Path(__file__).resolve()
            with open(own_file, "r", encoding="utf-8") as f:
                self._own_source = f.read()
        except Exception:
            # Fallback: inspect module yang sedang running
            try:
                import sys
                main_module = sys.modules.get("__main__")
                if main_module and hasattr(main_module, "__file__"):
                    with open(main_module.__file__, "r") as f:
                        self._own_source = f.read()
            except Exception:
                self._own_source = ""
        return self._own_source or ""

    def scan(self) -> List["CodeGene"]:
        """
        Scan source code engine sendiri:
        1. Cari semua ekspresi return/assignment dalam method
        2. Cari one-liner yang mengandung operasi berguna
        3. Test via gauntlet
        """
        candidates: List["CodeGene"] = []
        source = self._get_own_source()
        if not source:
            return candidates

        try:
            tree = ast.parse(source)
        except Exception:
            return candidates

        for cls_node in ast.walk(tree):
            if not isinstance(cls_node, ast.ClassDef):
                continue
            for method_node in ast.walk(cls_node):
                if not isinstance(method_node, ast.FunctionDef):
                    continue
                if method_node.name.startswith("_") and not method_node.name.startswith("__"):
                    # Fokus ke private helper methods
                    for stmt in method_node.body:
                        gene = self._extract_gene_from_stmt(stmt, method_node.name)
                        if gene:
                            candidates.append(gene)
                        if len(candidates) >= 10:
                            return candidates

        return candidates

    def _extract_gene_from_stmt(
        self, stmt: ast.stmt, method_name: str
    ) -> Optional["CodeGene"]:
        """Ekstrak gene kandidat dari sebuah statement."""
        # Hanya proses assignment dan return sederhana
        if not isinstance(stmt, (ast.Assign, ast.Return, ast.AugAssign)):
            return None
        try:
            src = ast.unparse(stmt)
        except Exception:
            return None

        if len(src) > 150 or len(src) < 10:
            return None

        # Normalisasi ke template gen
        if isinstance(stmt, ast.Return) and stmt.value:
            try:
                val_src = ast.unparse(stmt.value)
                src = f"result = {val_src}"
            except Exception:
                return None
        elif "=" not in src:
            return None
        else:
            src = re.sub(r'^\w+\s*=\s*', 'result = ', src, count=1)

        template = f"    {src}\n"
        key = hashlib.md5(template.encode()).hexdigest()
        if key in self._seen:
            return None
        self._seen.add(key)

        arity = self._infer_arity(template)
        gene_id = f"slf_{key[:10]}"

        try:
            passed, score, _ = self.gauntlet.run(gene_id, template, arity)
        except Exception:
            return None

        if not passed:
            return None

        return CodeGene(
            id=gene_id,
            template=template,
            arity=arity,
            complexity=1.0,
            description=f"self-scan from {method_name}",
            origin="self_scan",
            gauntlet_score=score,
            is_probationary=True,  # self-scan selalu probationary dulu
            added_at=time.time(),
            source_hint=f"method:{method_name}",
        )

    def _infer_arity(self, template: str) -> int:
        for n in range(3, 0, -1):
            if f"arg{n}" in template:
                return n
        return 1


# ─────────────────────────────────────────────────────────────────────────────
# ██████╗ GENE PRUNER  — Buang gen lemah (Moderate policy)
# ─────────────────────────────────────────────────────────────────────────────

class GenePruner:
    """
    Membersihkan gene pool secara berkala.
    Policy: Moderate — buang gen yang KEDUANYA lemah DAN jarang dipakai.
    Gen default pool tidak pernah dihapus (protected).
    """

    _PROTECTED_ORIGINS = {"default"}

    def __init__(self, config: "EvolutionConfig"):
        self.config = config
        self.pruned_history: List[Dict] = []

    def prune(
        self,
        gene_pool: Dict[str, "CodeGene"],
        gene_weights: Dict[str, float],
    ) -> Tuple[Dict[str, "CodeGene"], List[str]]:
        """
        Prune pool, return (pool_baru, list_gene_id_yang_dihapus).
        """
        if len(gene_pool) <= self.config.pruner_min_pool_size:
            return gene_pool, []

        pruned_ids: List[str] = []
        new_pool = {}

        # Kalau pool di atas soft_max → jadilah sedikit lebih agresif
        above_soft_max = len(gene_pool) > self.config.pool_soft_max
        weight_threshold = self.config.pruner_weight_threshold
        if above_soft_max:
            weight_threshold *= 1.5  # naikkan threshold kalau pool membesar

        for gene_id, gene in gene_pool.items():
            # Protected genes tidak pernah dihapus
            if gene.origin in self._PROTECTED_ORIGINS:
                new_pool[gene_id] = gene
                continue

            w = gene_weights.get(gene_id, 1.0)
            usage = gene.usage_count

            # Kriteria prune: bobot rendah DAN jarang dipakai
            is_weak = w < weight_threshold
            is_unused = usage < self.config.pruner_min_usage

            # Probationary gene: lebih mudah dihapus (hanya perlu satu kondisi)
            if gene.is_probationary:
                should_prune = is_weak or (is_unused and w < weight_threshold * 2)
            else:
                should_prune = is_weak and is_unused

            if should_prune and len(new_pool) + (len(gene_pool) - len(pruned_ids) - 1) > self.config.pruner_min_pool_size:
                pruned_ids.append(gene_id)
                self.pruned_history.append({
                    "id": gene_id,
                    "origin": gene.origin,
                    "weight": round(w, 4),
                    "usage": usage,
                    "gauntlet_score": gene.gauntlet_score,
                    "pruned_at": time.time(),
                })
            else:
                new_pool[gene_id] = gene

        return new_pool, pruned_ids


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENGINE (v3 — Self-Expanding)
# ─────────────────────────────────────────────────────────────────────────────

class ExperienceDrivenEvolutionEngine:
    """
    Mesin evolusi generasi kedua. Menggabungkan rule-based evolution dengan
    kemampuan belajar dari pengalaman. Setiap task yang diselesaikan membuat
    mesin ini makin pintar untuk task berikutnya.
    """

    def __init__(
        self,
        gene_pool: Optional[List[CodeGene]] = None,
        config: Optional[EvolutionConfig] = None,
        knowledge_db: str = "memory/evolution/knowledge.db",
    ):
        self.gene_pool = {g.id: g for g in (gene_pool or DEFAULT_GENE_POOL)}
        self.config = config or EvolutionConfig()
        self.sandbox = AdvancedSandbox(timeout=self.config.timeout_seconds)
        self.kb = KnowledgeBase(knowledge_db)

        # ── Experience Memory ──────────────────────────────────────────────
        non_return = [g for g in self.gene_pool if g != "return_res"]

        # Bobot individual per gen (makin tinggi = makin sering dipilih)
        self.gene_weights: Dict[str, float] = {gid: 1.0 for gid in non_return}
        # Matriks transisi Markov: P(gen B | gen A sebelumnya)
        self.gene_transitions: Dict[str, Dict[str, float]] = {
            g1: {g2: 1.0 for g2 in non_return} for g1 in non_return
        }
        # Catatan sukses/gagal per gen
        self.gene_success: Dict[str, int] = {gid: 0 for gid in non_return}
        self.gene_failure: Dict[str, int] = {gid: 0 for gid in non_return}

        # ── Pattern Memory ─────────────────────────────────────────────────
        self.known_patterns: List[GenePattern] = []

        # ── Novelty Archive ────────────────────────────────────────────────
        self.novelty_archive: List[str] = []  # list of behavior fingerprints

        # ── Fitness Cache (avoid re-evaluating same genome) ────────────────
        self._fitness_cache: Dict[str, float] = {}

        # ── Adaptive State ─────────────────────────────────────────────────
        self.stagnation_counter: int = 0
        self.best_historical_fitness: float = float("-inf")
        self._current_mutation_rate: float = self.config.mutation_rate
        self._current_crossover_rate: float = self.config.crossover_rate

        # ── Self-improvement Counters ──────────────────────────────────────
        self._internal_cycle_count: int = 0
        self._meta_generation: int = 0

        # ── v3: Self-Expanding Subsystems ─────────────────────────────────
        self.gauntlet = GeneGauntlet(self.config, self.gene_pool)
        self.synthesizer = GeneSynthesizer(self.gauntlet, self.config)
        self.harvester = CodeHarvester(self.gauntlet, self.config)
        self.mutator = TemplateMutator(self.gauntlet, self.config)
        self.self_scanner = SelfReflectiveScanner(self.gauntlet, self.config)
        self.pruner = GenePruner(self.config)

        # Track jumlah gen berdasarkan origin
        self._pool_stats: Dict[str, int] = defaultdict(int)

        # Scan root paths (Termux default + cwd)
        self._harvest_roots: List[str] = self._detect_harvest_roots()

        # ── Load persisted experience ──────────────────────────────────────
        self._load_experience()

        logger.info(
            f"SelfExpandingEvolutionEngine v{self.config.version} initialized. "
            f"Gene pool: {len(self.gene_pool)}, Patterns loaded: {len(self.known_patterns)}. "
            f"Harvest roots: {self._harvest_roots}"
        )

    def _detect_harvest_roots(self) -> List[str]:
        """Auto-detect direktori yang relevan untuk di-scan."""
        roots = []
        candidates = [
            os.getcwd(),
            str(Path.home()),
            "/data/data/com.termux/files/home",  # Termux home
            "/data/data/com.termux/files/usr",   # Termux usr
            str(Path(__file__).parent),           # direktori file ini
        ]
        for c in candidates:
            if os.path.exists(c) and c not in roots:
                roots.append(c)
        return roots[:4]  # max 4 roots

    # ──────────────────────────────────────────────────────────────────────────
    # DYNAMIC GENE POOL MANAGEMENT
    # ──────────────────────────────────────────────────────────────────────────

    def _add_genes_to_pool(self, new_genes: List[CodeGene], source_label: str):
        """
        Tambahkan gen baru ke pool setelah lolos gauntlet.
        Inisialisasi weight, transition, dan success tracking.
        """
        added = 0
        for gene in new_genes:
            if gene.id in self.gene_pool:
                continue
            if len(self.gene_pool) >= self.config.pool_max_size:
                logger.debug(f"Pool max size reached ({self.config.pool_max_size}), skipping.")
                break

            self.gene_pool[gene.id] = gene
            init_weight = self.gauntlet.determine_initial_weight(gene.gauntlet_score)
            self.gene_weights[gene.id] = init_weight
            self.gene_success[gene.id] = 0
            self.gene_failure[gene.id] = 0

            # Tambahkan baris/kolom di matriks transisi
            for existing_id in list(self.gene_transitions.keys()):
                self.gene_transitions[existing_id][gene.id] = init_weight * 0.5
            self.gene_transitions[gene.id] = {
                gid: 1.0 for gid in self.gene_weights
            }

            self._pool_stats[gene.origin] += 1
            added += 1

        if added > 0:
            logger.info(
                f"[Pool] +{added} genes from {source_label}. "
                f"Pool size: {len(self.gene_pool)}"
            )
        return added

    def _run_synthesizer(self, best_genomes: List[Genome]):
        """Jalankan synthesizer pada genome terbaik."""
        new_genes: List[CodeGene] = []
        for genome in best_genomes[:3]:
            if genome.fitness > 0 and genome.compiled_code:
                new_genes.extend(self.synthesizer.synthesize_from_genome(genome))
        if new_genes:
            self._add_genes_to_pool(new_genes, "synthesizer")

    def _run_harvester(self):
        """Jalankan harvester pada filesystem."""
        new_genes = self.harvester.harvest(self._harvest_roots)
        if new_genes:
            self._add_genes_to_pool(new_genes, "harvester")

    def _run_template_mutator(self):
        """Jalankan mutator pada gen yang ada di pool."""
        # Pilih gen untuk dimutasi: utamakan yang weight-nya sedang (bukan tertinggi/terendah)
        candidates = sorted(
            [g for g in self.gene_pool.values() if g.origin != "default"],
            key=lambda g: abs(self.gene_weights.get(g.id, 1.0) - 1.0)
        )[:15]

        if not candidates:
            candidates = random.sample(list(self.gene_pool.values()), min(5, len(self.gene_pool)))

        new_genes: List[CodeGene] = []
        for gene in candidates[:self.config.mutator_max_per_run]:
            mutated = self.mutator.mutate_gene(gene)
            if mutated:
                new_genes.append(mutated)

        if new_genes:
            self._add_genes_to_pool(new_genes, "template_mutator")

    def _run_self_scanner(self):
        """Jalankan self-reflective scanner."""
        new_genes = self.self_scanner.scan()
        if new_genes:
            self._add_genes_to_pool(new_genes, "self_scanner")

    def _run_pruner(self):
        """Jalankan pruner untuk membersihkan gen lemah."""
        self.gene_pool, pruned = self.pruner.prune(self.gene_pool, self.gene_weights)

        # Bersihkan juga dari weights, transitions, success/failure
        for gid in pruned:
            self.gene_weights.pop(gid, None)
            self.gene_success.pop(gid, None)
            self.gene_failure.pop(gid, None)
            for trans_dict in self.gene_transitions.values():
                trans_dict.pop(gid, None)
            self.gene_transitions.pop(gid, None)

        # Update gauntlet pool reference
        self.gauntlet.existing_pool = self.gene_pool

        if pruned:
            logger.info(f"[Pruner] Removed {len(pruned)} genes. Pool size: {len(self.gene_pool)}")

        return pruned

    def _update_gene_usage(self, population: List[Genome]):
        """Update usage_count setiap gen yang dipakai di populasi."""
        for genome in population:
            for gene in genome.genes:
                if gene.id in self.gene_pool:
                    self.gene_pool[gene.id].usage_count += 1

    # ──────────────────────────────────────────────────────────────────────────
    # EXPERIENCE PERSISTENCE
    # ──────────────────────────────────────────────────────────────────────────

    def _load_experience(self):
        """Muat pengalaman dari sesi sebelumnya."""
        try:
            stored = self.kb.load_gene_weights()
            for gid, (w, s, f) in stored.items():
                if gid in self.gene_weights:
                    self.gene_weights[gid] = w
                    self.gene_success[gid] = s
                    self.gene_failure[gid] = f

            stored_trans = self.kb.load_gene_transitions()
            for from_g, to_dict in stored_trans.items():
                if from_g in self.gene_transitions:
                    for to_g, w in to_dict.items():
                        if to_g in self.gene_transitions[from_g]:
                            self.gene_transitions[from_g][to_g] = w

            self.known_patterns = self.kb.load_patterns()
            logger.info(f"Experience loaded: {len(stored)} gene weights, {len(self.known_patterns)} patterns.")
        except Exception as e:
            logger.warning(f"Could not load experience: {e}. Starting fresh.")

    def _save_experience(self):
        """Simpan pengalaman ke DB."""
        try:
            self.kb.save_gene_weights(self.gene_weights, self.gene_success, self.gene_failure)
            self.kb.save_gene_transitions(self.gene_transitions)
            self.kb.save_patterns(self.known_patterns)
        except Exception as e:
            logger.warning(f"Could not save experience: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # EXPERIENCE UPDATE (belajar dari populasi)
    # ──────────────────────────────────────────────────────────────────────────

    def _update_experience(self, population: List[Genome]):
        """
        Core learning method. Belajar dari top performers saat ini:
        - Update bobot gen individual
        - Update matriks transisi Markov
        - Update catatan sukses/gagal per gen
        """
        if not population:
            return

        n_top = max(1, len(population) // 5)
        top = sorted(population, key=lambda g: g.fitness, reverse=True)[:n_top]
        bottom = sorted(population, key=lambda g: g.fitness)[:n_top]

        max_fit = top[0].fitness if top[0].fitness > 0 else 1.0
        lr = self.config.learning_rate

        # Reward dari top performers
        for genome in top:
            if genome.fitness <= 0:
                continue
            reward = genome.fitness / max_fit

            for i, gene in enumerate(genome.genes):
                if gene.id == "return_res":
                    continue

                # Update bobot individual
                old_w = self.gene_weights[gene.id]
                self.gene_weights[gene.id] = (
                    (1 - lr) * old_w + lr * reward
                )
                self.gene_weights[gene.id] = max(
                    self.config.experience_min_weight,
                    min(self.config.experience_max_weight, self.gene_weights[gene.id])
                )
                self.gene_success[gene.id] += 1

                # Update transisi Markov
                if i < len(genome.genes) - 2:
                    next_gene = genome.genes[i + 1]
                    if next_gene.id != "return_res" and next_gene.id in self.gene_transitions.get(gene.id, {}):
                        old_t = self.gene_transitions[gene.id][next_gene.id]
                        self.gene_transitions[gene.id][next_gene.id] = (
                            (1 - lr) * old_t + lr * reward
                        )

        # Penalty dari bottom performers (belajar dari kegagalan)
        for genome in bottom:
            for gene in genome.genes:
                if gene.id == "return_res":
                    continue
                penalty = 0.05
                self.gene_weights[gene.id] = max(
                    self.config.experience_min_weight,
                    self.gene_weights[gene.id] - penalty * lr
                )
                self.gene_failure[gene.id] += 1

        # Natural forgetting: semua bobot perlahan drift ke 1.0
        decay = self.config.forgetting_rate
        for gid in self.gene_weights:
            self.gene_weights[gid] += decay * (1.0 - self.gene_weights[gid])

    # ──────────────────────────────────────────────────────────────────────────
    # WEIGHTED GENE SELECTION (Markov-aware)
    # ──────────────────────────────────────────────────────────────────────────

    def _weighted_random_gene(self, context_gene_id: Optional[str] = None) -> CodeGene:
        """
        Pilih gen berdasarkan pengalaman.
        Jika ada konteks gen sebelumnya → pakai matriks transisi Markov.
        Jika tidak → pakai bobot popularitas umum.
        """
        gene_ids = [gid for gid in self.gene_weights]
        if not gene_ids:
            return random.choice([g for g in self.gene_pool.values() if g.id != "return_res"])

        if context_gene_id and context_gene_id in self.gene_transitions:
            weights = [
                self.gene_transitions[context_gene_id].get(gid, 1.0)
                for gid in gene_ids
            ]
        else:
            weights = [self.gene_weights.get(gid, 1.0) for gid in gene_ids]

        # Softmax-like normalization untuk stabilitas
        max_w = max(weights) if weights else 1.0
        weights = [w / max_w for w in weights]

        chosen_id = random.choices(gene_ids, weights=weights, k=1)[0]
        return self.gene_pool[chosen_id]

    # ──────────────────────────────────────────────────────────────────────────
    # PATTERN MINING
    # ──────────────────────────────────────────────────────────────────────────

    def _mine_patterns(self, population: List[Genome]):
        """
        Ekstrak pola urutan gen yang sering muncul di top performers.
        Simpan pola dengan fitness rata-rata sebagai metadata.
        """
        n_top = max(3, len(population) // 4)
        top = sorted(population, key=lambda g: g.fitness, reverse=True)[:n_top]

        pattern_scores: Dict[str, List[float]] = defaultdict(list)

        for genome in top:
            if genome.fitness <= 0:
                continue
            ids = [g.id for g in genome.genes if g.id != "return_res"]

            for length in range(
                self.config.pattern_min_length,
                min(self.config.pattern_max_length + 1, len(ids) + 1)
            ):
                for start in range(len(ids) - length + 1):
                    subseq = ids[start: start + length]
                    key = "|".join(subseq)
                    pattern_scores[key].append(genome.fitness)

        new_patterns: List[GenePattern] = []
        for key, scores in pattern_scores.items():
            if len(scores) >= 2:
                avg_fit = sum(scores) / len(scores)
                gene_ids = key.split("|")
                # Pastikan semua gen valid
                if all(gid in self.gene_pool for gid in gene_ids):
                    new_patterns.append(GenePattern(
                        gene_ids=gene_ids,
                        avg_fitness=avg_fit,
                        occurrence_count=len(scores),
                        last_seen=time.time(),
                    ))

        # Merge dengan pola yang sudah ada
        existing = {"|".join(p.gene_ids): p for p in self.known_patterns}
        for p in new_patterns:
            key = "|".join(p.gene_ids)
            if key in existing:
                old = existing[key]
                # Running average
                total = old.occurrence_count + p.occurrence_count
                existing[key] = GenePattern(
                    gene_ids=p.gene_ids,
                    avg_fitness=(old.avg_fitness * old.occurrence_count + p.avg_fitness * p.occurrence_count) / total,
                    occurrence_count=total,
                    last_seen=time.time(),
                )
            else:
                existing[key] = p

        # Simpan top K pola terbaik
        self.known_patterns = sorted(
            existing.values(), key=lambda p: p.avg_fitness, reverse=True
        )[:self.config.pattern_top_k]

    def _genome_from_pattern(self, num_args: int) -> Optional[Genome]:
        """Buat genome baru berdasarkan pola yang diketahui berhasil."""
        if not self.known_patterns:
            return None

        # Pilih pola secara weighted by fitness
        weights = [max(0.01, p.avg_fitness) for p in self.known_patterns]
        pattern = random.choices(self.known_patterns, weights=weights, k=1)[0]

        genes = [self.gene_pool[gid] for gid in pattern.gene_ids if gid in self.gene_pool]
        if not genes:
            return None

        # Tambah beberapa gen random di sekitar pola untuk variasi
        prefix_len = random.randint(0, 2)
        suffix_len = random.randint(0, 2)

        prefix = [self._weighted_random_gene() for _ in range(prefix_len)]
        suffix = [self._weighted_random_gene(genes[-1].id if genes else None) for _ in range(suffix_len)]

        full_genes = prefix + genes + suffix + [self.gene_pool["return_res"]]
        return Genome(genes=full_genes)

    # ──────────────────────────────────────────────────────────────────────────
    # GENOME CREATION
    # ──────────────────────────────────────────────────────────────────────────

    def _random_genome(self, num_args: int) -> Genome:
        """
        Inisialisasi genome yang dipandu pengalaman.
        Ada peluang menggunakan pola yang diketahui berhasil.
        """
        # Gunakan pola jika tersedia
        if (self.known_patterns
                and random.random() < self.config.pattern_use_prob):
            candidate = self._genome_from_pattern(num_args)
            if candidate:
                return candidate

        # Fallback: buat dari weighted random
        length = random.randint(2, 7)
        genes = []
        last_id = None

        for _ in range(length):
            gene = self._weighted_random_gene(last_id)
            genes.append(gene)
            last_id = gene.id

        genes.append(self.gene_pool["return_res"])
        return Genome(genes=genes)

    # ──────────────────────────────────────────────────────────────────────────
    # MUTATIONS (5 tipe baru + mutasi asli yang diperbaiki)
    # ──────────────────────────────────────────────────────────────────────────

    def _mutate(self, genome: Genome) -> Genome:
        """Dispatcher mutasi — pilih tipe mutasi secara acak dengan bobot."""
        if len(genome.genes) <= 1:
            return genome

        # Bobot tiap tipe mutasi (bisa disesuaikan)
        mutation_types = [
            ("replace",   0.35),
            ("insert",    0.15),
            ("delete",    0.15),
            ("swap",      0.15),
            ("invert",    0.10),
            ("block",     0.10),
        ]
        m_type = random.choices(
            [t[0] for t in mutation_types],
            weights=[t[1] for t in mutation_types],
            k=1
        )[0]

        genes = [g for g in genome.genes if g.id != "return_res"]
        if not genes:
            return genome

        if m_type == "replace":
            genome = self._mutate_replace(genome)
        elif m_type == "insert":
            genome = self._mutate_insert(genome)
        elif m_type == "delete":
            genome = self._mutate_delete(genome)
        elif m_type == "swap":
            genome = self._mutate_swap(genome)
        elif m_type == "invert":
            genome = self._mutate_invert(genome)
        elif m_type == "block":
            genome = self._mutate_block(genome)

        # Pastikan return_res ada di akhir
        genome.genes = [g for g in genome.genes if g.id != "return_res"]
        genome.genes.append(self.gene_pool["return_res"])
        return genome

    def _mutate_replace(self, genome: Genome) -> Genome:
        """Ganti satu gen dengan gen baru (context-aware)."""
        non_ret = [i for i, g in enumerate(genome.genes) if g.id != "return_res"]
        if not non_ret:
            return genome
        idx = random.choice(non_ret)
        prev_id = genome.genes[idx - 1].id if idx > 0 else None
        genome.genes[idx] = self._weighted_random_gene(prev_id)
        return genome

    def _mutate_insert(self, genome: Genome) -> Genome:
        """Sisipkan gen baru di posisi acak."""
        if len(genome.genes) >= 10:  # batasi panjang maksimal
            return genome
        non_ret = [i for i, g in enumerate(genome.genes) if g.id != "return_res"]
        idx = random.randint(0, len(non_ret))
        prev_id = genome.genes[idx - 1].id if idx > 0 else None
        new_gene = self._weighted_random_gene(prev_id)
        genome.genes.insert(idx, new_gene)
        return genome

    def _mutate_delete(self, genome: Genome) -> Genome:
        """Hapus satu gen dari posisi acak (jika panjang cukup)."""
        non_ret = [i for i, g in enumerate(genome.genes) if g.id != "return_res"]
        if len(non_ret) <= 1:
            return genome
        idx = random.choice(non_ret)
        del genome.genes[idx]
        return genome

    def _mutate_swap(self, genome: Genome) -> Genome:
        """Tukar posisi dua gen."""
        non_ret = [i for i, g in enumerate(genome.genes) if g.id != "return_res"]
        if len(non_ret) < 2:
            return genome
        i, j = random.sample(non_ret, 2)
        genome.genes[i], genome.genes[j] = genome.genes[j], genome.genes[i]
        return genome

    def _mutate_invert(self, genome: Genome) -> Genome:
        """Balik urutan segmen gen."""
        non_ret = [i for i, g in enumerate(genome.genes) if g.id != "return_res"]
        if len(non_ret) < 2:
            return genome
        i = random.randint(0, len(non_ret) - 2)
        j = random.randint(i + 1, len(non_ret) - 1)
        genome.genes[i:j + 1] = genome.genes[i:j + 1][::-1]
        return genome

    def _mutate_block(self, genome: Genome) -> Genome:
        """Ganti blok gen dengan blok baru berdasarkan pola atau random."""
        non_ret = [i for i, g in enumerate(genome.genes) if g.id != "return_res"]
        if len(non_ret) < 2:
            return genome

        # Pilih segmen
        start = random.randint(0, len(non_ret) - 1)
        end = random.randint(start + 1, min(start + 3, len(non_ret)))

        # Ganti dengan pola atau gen baru
        if self.known_patterns and random.random() < 0.4:
            pattern = random.choice(self.known_patterns[:10])
            new_block = [self.gene_pool[gid] for gid in pattern.gene_ids if gid in self.gene_pool]
        else:
            block_len = end - start
            new_block = [self._weighted_random_gene() for _ in range(block_len)]

        actual_indices = non_ret[start:end]
        for i, idx in enumerate(actual_indices):
            if i < len(new_block):
                genome.genes[idx] = new_block[i]
        return genome

    # ──────────────────────────────────────────────────────────────────────────
    # CROSSOVER (intelligent multi-point)
    # ──────────────────────────────────────────────────────────────────────────

    def _crossover(self, p1: Genome, p2: Genome) -> Genome:
        """
        Crossover cerdas:
        - 40%: Uniform crossover (pilih dari p1/p2 per-gen)
        - 35%: Single-point crossover
        - 25%: Pattern-preserving crossover
        """
        r = random.random()
        if r < 0.40:
            return self._crossover_uniform(p1, p2)
        elif r < 0.75:
            return self._crossover_single_point(p1, p2)
        else:
            return self._crossover_pattern_preserving(p1, p2)

    def _crossover_single_point(self, p1: Genome, p2: Genome) -> Genome:
        g1 = [g for g in p1.genes if g.id != "return_res"]
        g2 = [g for g in p2.genes if g.id != "return_res"]
        if not g1 or not g2:
            return Genome(genes=p1.genes.copy())
        split = random.randint(1, min(len(g1), len(g2)))
        child_genes = g1[:split] + g2[split:] + [self.gene_pool["return_res"]]
        return Genome(genes=child_genes)

    def _crossover_uniform(self, p1: Genome, p2: Genome) -> Genome:
        """Tiap gen dipilih dari p1 atau p2 berdasarkan fitness ratio."""
        g1 = [g for g in p1.genes if g.id != "return_res"]
        g2 = [g for g in p2.genes if g.id != "return_res"]
        max_len = max(len(g1), len(g2))
        min_len = min(len(g1), len(g2))

        # Probabilitas pilih dari p1 berdasarkan fitness relative
        total_fit = abs(p1.fitness) + abs(p2.fitness) + 1e-9
        p1_prob = abs(p1.fitness) / total_fit

        child_genes = []
        for i in range(max_len):
            if i < min_len:
                gene = g1[i] if random.random() < p1_prob else g2[i]
            elif i < len(g1):
                gene = g1[i]
            else:
                gene = g2[i]
            child_genes.append(gene)

        child_genes.append(self.gene_pool["return_res"])
        return Genome(genes=child_genes)

    def _crossover_pattern_preserving(self, p1: Genome, p2: Genome) -> Genome:
        """
        Coba pertahankan pola yang diketahui dari salah satu parent.
        Pola tetap utuh, sisa diisi dari parent lain.
        """
        if not self.known_patterns:
            return self._crossover_single_point(p1, p2)

        # Pilih parent dengan fitness lebih tinggi sebagai "template"
        template, donor = (p1, p2) if p1.fitness >= p2.fitness else (p2, p1)

        t_ids = [g.id for g in template.genes if g.id != "return_res"]
        d_genes = [g for g in donor.genes if g.id != "return_res"]

        # Cari apakah ada pola dari known_patterns yang ada di template
        best_pattern = None
        best_pos = -1
        for pattern in self.known_patterns[:5]:
            pids = pattern.gene_ids
            for start in range(len(t_ids) - len(pids) + 1):
                if t_ids[start:start + len(pids)] == pids:
                    best_pattern = pattern
                    best_pos = start
                    break
            if best_pattern:
                break

        if best_pattern is None or best_pos < 0:
            return self._crossover_single_point(p1, p2)

        # Ambil pola dari template, sisa dari donor
        plen = len(best_pattern.gene_ids)
        pattern_genes = template.genes[best_pos: best_pos + plen]
        donor_prefix = d_genes[:best_pos] if best_pos < len(d_genes) else []
        donor_suffix = d_genes[best_pos + plen:] if (best_pos + plen) < len(d_genes) else []

        child_genes = donor_prefix + pattern_genes + donor_suffix + [self.gene_pool["return_res"]]
        return Genome(genes=child_genes)

    # ──────────────────────────────────────────────────────────────────────────
    # NOVELTY SEARCH
    # ──────────────────────────────────────────────────────────────────────────

    def _compute_behavior_fingerprint(
        self, genome: Genome, func_name: str, test_inputs: List[Tuple]
    ) -> str:
        """
        Hitung fingerprint perilaku genome berdasarkan outputnya pada test cases.
        Genome yang menghasilkan output berbeda = lebih novel.
        """
        outputs = []
        for inp in test_inputs[:5]:  # Hanya 5 sample untuk efisiensi
            success, res, _, _, _ = self.sandbox.execute(
                genome.compiled_code, func_name, inp
            )
            outputs.append(repr(res) if success else "ERR")

        fingerprint = "|".join(outputs)
        return hashlib.md5(fingerprint.encode()).hexdigest()

    def _compute_novelty_score(self, fingerprint: str) -> float:
        """
        Hitung novelty berdasarkan jarak ke K tetangga terdekat di archive.
        Pakai Hamming distance pada hex fingerprint.
        """
        if not self.novelty_archive:
            return 1.0

        def hamming_dist(a: str, b: str) -> float:
            min_len = min(len(a), len(b))
            return sum(1 for i in range(min_len) if a[i] != b[i]) / max(min_len, 1)

        distances = sorted([hamming_dist(fingerprint, arch) for arch in self.novelty_archive])
        k = min(self.config.novelty_k_nearest, len(distances))
        return sum(distances[:k]) / k if k > 0 else 0.0

    def _update_novelty_archive(self, fingerprint: str):
        """Tambahkan fingerprint ke archive, buang yang lama jika penuh."""
        if fingerprint not in self.novelty_archive:
            self.novelty_archive.append(fingerprint)
            if len(self.novelty_archive) > self.config.novelty_archive_size:
                self.novelty_archive.pop(0)

    # ──────────────────────────────────────────────────────────────────────────
    # DIVERSITY MEASUREMENT & INJECTION
    # ──────────────────────────────────────────────────────────────────────────

    def _measure_diversity(self, population: List[Genome]) -> float:
        """
        Ukur keberagaman populasi menggunakan entropy distribusi gen.
        Nilai 0 = semua sama, nilai 1 = sangat beragam.
        """
        if not population:
            return 0.0

        gene_counts: Dict[str, int] = defaultdict(int)
        total = 0
        for genome in population:
            for gene in genome.genes:
                gene_counts[gene.id] += 1
                total += 1

        if total == 0:
            return 0.0

        entropy = 0.0
        for count in gene_counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)

        # Normalisasi dengan log2(N) dimana N = jumlah gen unik
        max_entropy = math.log2(len(gene_counts)) if len(gene_counts) > 1 else 1.0
        return entropy / max_entropy if max_entropy > 0 else 0.0

    def _inject_diversity(self, population: List[Genome], num_args: int) -> List[Genome]:
        """Ganti individu terburuk dengan genome segar untuk prevent stagnasi."""
        n = self.config.diversity_inject_count
        # Hapus individu dengan fitness terendah
        population.sort(key=lambda g: g.fitness, reverse=True)
        population = population[:-n]
        # Tambah individu baru
        for _ in range(n):
            new_genome = self._random_genome(num_args)
            population.append(new_genome)
        return population

    # ──────────────────────────────────────────────────────────────────────────
    # ADAPTIVE HYPERPARAMETERS
    # ──────────────────────────────────────────────────────────────────────────

    def _adaptive_hyperparameters(self, current_best_fitness: float):
        """
        Sesuaikan laju mutasi dan crossover secara adaptif:
        - Stagnan → naikkan mutasi (eksplorasi agresif)
        - Progres → turunkan mutasi (eksploitasi fokus)
        Mirip Simulated Annealing tapi berbasis fitness, bukan waktu.
        """
        if current_best_fitness > self.best_historical_fitness:
            self.stagnation_counter = 0
            self.best_historical_fitness = current_best_fitness
            # Fokus: turunkan eksplorasi
            self._current_mutation_rate = max(
                self.config.mutation_rate_min,
                self._current_mutation_rate * self.config.annealing_cool_factor
            )
            self._current_crossover_rate = min(
                self.config.crossover_rate_max,
                self._current_crossover_rate * 1.05
            )
        else:
            self.stagnation_counter += 1

            if self.stagnation_counter >= self.config.stagnation_threshold:
                # Frustrasi: naikkan eksplorasi
                self._current_mutation_rate = min(
                    self.config.mutation_rate_max,
                    self._current_mutation_rate * self.config.annealing_heat_factor
                )
                self._current_crossover_rate = max(
                    self.config.crossover_rate_min,
                    self._current_crossover_rate * 0.9
                )
                logger.debug(
                    f"Stagnation {self.stagnation_counter}: "
                    f"mutation_rate={self._current_mutation_rate:.3f}"
                )

    # ──────────────────────────────────────────────────────────────────────────
    # TOURNAMENT SELECTION (with optional novelty bonus)
    # ──────────────────────────────────────────────────────────────────────────

    def _tournament_select(self, population: List[Genome]) -> Genome:
        size = min(self.config.tournament_size, len(population))
        tourn = random.sample(population, size)
        # Fitness gabungan: correctness + novelty
        return max(
            tourn,
            key=lambda g: g.fitness + self.config.weight_novelty * g.novelty_score
        )

    # ──────────────────────────────────────────────────────────────────────────
    # GENOME COMPILATION & EVALUATION
    # ──────────────────────────────────────────────────────────────────────────

    def _compile_genome(self, genome: Genome, func_name: str, num_args: int) -> str:
        args_str = ", ".join([f"arg{i+1}" for i in range(num_args)])
        code = f"def {func_name}({args_str}):\n    result = None\n"
        for gene in genome.genes:
            code += gene.template
        return code

    def _validate_syntax(self, code: str) -> bool:
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def _genome_cache_key(self, genome: Genome) -> str:
        gene_ids_str = "|".join(g.id for g in genome.genes)
        return hashlib.md5(gene_ids_str.encode()).hexdigest()

    def _evaluate_genome(
        self,
        genome: Genome,
        func_name: str,
        num_args: int,
        test_inputs: List[Tuple],
        expected_outputs: List[Any],
        compute_novelty: bool = False,
    ) -> float:
        genome.compiled_code = self._compile_genome(genome, func_name, num_args)

        # Cache check
        cache_key = self._genome_cache_key(genome)
        if cache_key in self._fitness_cache:
            genome.fitness = self._fitness_cache[cache_key]
            return genome.fitness

        if not self._validate_syntax(genome.compiled_code):
            genome.fitness = -100.0
            return genome.fitness

        total_correct = 0
        total_time = 0.0
        total_mem = 0.0

        for inp, exp in zip(test_inputs, expected_outputs):
            success, res, dur, mem, err = self.sandbox.execute(
                genome.compiled_code, func_name, inp
            )
            if success and res == exp:
                total_correct += 1
                total_time += dur
                total_mem += mem

        n = len(test_inputs)
        correctness = total_correct / n
        avg_time = total_time / max(n, 1)
        avg_mem = total_mem / max(n, 1)
        simplicity = 1.0 / (len(genome.compiled_code) + 1)

        fitness = (
            self.config.weight_correctness * correctness
            - self.config.weight_speed * avg_time
            - self.config.weight_memory * avg_mem
            + self.config.weight_simplicity * simplicity
        )

        # Novelty bonus
        if compute_novelty and genome.compiled_code:
            fp = self._compute_behavior_fingerprint(genome, func_name, test_inputs)
            genome.behavior_fingerprint = fp
            genome.novelty_score = self._compute_novelty_score(fp)
            self._update_novelty_archive(fp)
            fitness += self.config.weight_novelty * genome.novelty_score

        genome.fitness = fitness
        genome.execution_time = avg_time
        genome.memory_estimate = avg_mem
        genome.code_length = len(genome.compiled_code)

        # Cache result
        self._fitness_cache[cache_key] = fitness
        # Bersihkan cache kalau terlalu besar
        if len(self._fitness_cache) > 5000:
            keys_to_remove = list(self._fitness_cache.keys())[:1000]
            for k in keys_to_remove:
                del self._fitness_cache[k]

        return fitness

    # ──────────────────────────────────────────────────────────────────────────
    # WARM START
    # ──────────────────────────────────────────────────────────────────────────

    def _warm_start_genomes(self, task_id: str, num_args: int, count: int = 5) -> List[Genome]:
        """
        Coba seed populasi awal dengan genom dari task serupa yang pernah berhasil.
        Kesamaan task dinilai dari prefix task_id.
        """
        warm = []
        try:
            all_solutions = self.kb.get_all_solutions()
            # Ambil solution dengan task_id yang mirip (prefix match atau substring)
            similar = [
                s for s in all_solutions
                if s.task_id != task_id and (
                    task_id[:4] in s.task_id or s.task_id[:4] in task_id
                )
            ][:count]

            for sol in similar:
                # Parse kode solution menjadi urutan gen
                # (heuristik: lihat template gen yang muncul)
                guessed_genes = self._infer_genes_from_code(sol.code)
                if guessed_genes:
                    genome = Genome(genes=guessed_genes + [self.gene_pool["return_res"]])
                    warm.append(genome)
        except Exception as e:
            logger.debug(f"Warm start failed: {e}")

        return warm

    def _infer_genes_from_code(self, code: str) -> List[CodeGene]:
        """Heuristic: cari template gen mana yang muncul dalam kode."""
        found = []
        for gene in self.gene_pool.values():
            if gene.id == "return_res":
                continue
            # Cek kesamaan template di kode
            template_key = gene.template.strip()[:20]
            if template_key and template_key in code:
                found.append(gene)
        return found[:6]  # Batasi panjang

    # ──────────────────────────────────────────────────────────────────────────
    # ISLAND MODEL EVOLUTION
    # ──────────────────────────────────────────────────────────────────────────

    def _split_into_islands(
        self, population: List[Genome], n_islands: int
    ) -> List[List[Genome]]:
        """Bagi populasi menjadi N island secara round-robin."""
        islands: List[List[Genome]] = [[] for _ in range(n_islands)]
        for i, genome in enumerate(population):
            genome.island_id = i % n_islands
            islands[i % n_islands].append(genome)
        return islands

    def _migrate_between_islands(self, islands: List[List[Genome]]) -> List[List[Genome]]:
        """
        Migrasi ring: top-K dari island[i] dikirim ke island[(i+1) % N].
        """
        n = len(islands)
        if n < 2:
            return islands

        migrants = []
        for island in islands:
            top_k = sorted(island, key=lambda g: g.fitness, reverse=True)[:self.config.migration_size]
            migrants.append(top_k)

        for i, island in enumerate(islands):
            # Terima migran dari island sebelumnya
            new_migrants = migrants[(i - 1) % n]
            # Ganti individu terburuk
            island.sort(key=lambda g: g.fitness)
            for j, migrant in enumerate(new_migrants):
                if j < len(island):
                    island[j] = migrant
                    island[j].island_id = i

        return islands

    def _merge_islands(self, islands: List[List[Genome]]) -> List[Genome]:
        """Gabung semua island, ambil yang terbaik."""
        all_genomes = [g for island in islands for g in island]
        return sorted(all_genomes, key=lambda g: g.fitness, reverse=True)

    # ──────────────────────────────────────────────────────────────────────────
    # MAIN EVOLUTION LOOP
    # ──────────────────────────────────────────────────────────────────────────

    def evolve_external(
        self,
        task_id: str,
        inputs: List[Tuple],
        outputs: List[Any],
        generations: Optional[int] = None,
        pop_size: Optional[int] = None,
        resume_checkpoint: Optional[str] = None,
    ) -> Optional[str]:
        """
        Entry point utama evolusi.
        Sekarang menggunakan Island Model + Experience Memory + Adaptive HP.
        """
        if not inputs or not outputs:
            raise ValueError("inputs and outputs must be non-empty")
        if len(inputs) != len(outputs):
            raise ValueError("inputs and outputs length mismatch")

        num_args = len(inputs[0])
        gens = generations or self.config.generations
        pop = pop_size or self.config.population_size
        func_name = f"auto_{task_id}"

        # ── Knowledge Base Check ───────────────────────────────────────────
        if self.config.use_knowledge_base:
            cached = self.kb.get_solution(task_id)
            if cached:
                logger.info(f"[KB HIT] Task '{task_id}' found in knowledge base.")
                self.kb.update_usage(task_id)
                return cached.code

        # ── Inisialisasi Populasi ──────────────────────────────────────────
        population: List[Genome] = []

        if resume_checkpoint:
            try:
                population, _, _ = self.kb.load_checkpoint(resume_checkpoint, self.gene_pool)
                logger.info(f"Resumed from checkpoint '{resume_checkpoint}'")
            except Exception as e:
                logger.warning(f"Checkpoint load failed: {e}. Starting fresh.")

        if not population:
            # Warm start dari task serupa
            warm = self._warm_start_genomes(task_id, num_args, count=min(5, pop // 6))
            population = warm

            # Sisa dari random (guided by experience)
            while len(population) < pop:
                population.append(self._random_genome(num_args))

        # Reset adaptive state untuk task baru
        self.stagnation_counter = 0
        self.best_historical_fitness = float("-inf")
        self._current_mutation_rate = self.config.mutation_rate
        self._current_crossover_rate = self.config.crossover_rate

        # ── Island Split ───────────────────────────────────────────────────
        n_islands = self.config.num_islands
        islands = self._split_into_islands(population, n_islands)

        best_genome: Optional[Genome] = None
        best_fitness = float("-inf")

        # ── Generasi Loop ──────────────────────────────────────────────────
        for gen in range(gens):
            compute_nov = (gen % 5 == 0)  # novelty tiap 5 gen untuk efisiensi

            # Evolusi per-island
            new_islands: List[List[Genome]] = []
            for island_id, island in enumerate(islands):
                # Evaluate
                for g in island:
                    self._evaluate_genome(g, func_name, num_args, inputs, outputs, compute_nov)

                island.sort(key=lambda x: x.fitness, reverse=True)

                # Track global best
                if island[0].fitness > best_fitness:
                    best_fitness = island[0].fitness
                    best_genome = island[0]

                # Early stop: solusi sempurna
                if island[0].fitness >= self.config.weight_correctness:
                    logger.info(f"Perfect solution found at gen {gen}, island {island_id}!")
                    best_genome = island[0]
                    best_fitness = best_genome.fitness
                    # Simpan dan return
                    self._finalize(task_id, best_genome, best_fitness)
                    return best_genome.compiled_code

                # Diversity check per island
                div = self._measure_diversity(island)
                if div < self.config.diversity_threshold:
                    island = self._inject_diversity(island, num_args)

                # Build next generation
                island_size = len(island)
                new_island = island[:self.config.elitism_count]  # Elitisme

                while len(new_island) < island_size:
                    p1 = self._tournament_select(island)
                    p2 = self._tournament_select(island)

                    if random.random() < self._current_crossover_rate:
                        child = self._crossover(p1, p2)
                    else:
                        child = Genome(genes=p1.genes.copy())

                    if random.random() < self._current_mutation_rate:
                        child = self._mutate(child)

                    child.generation = gen + 1
                    child.parent_ids = (str(id(p1)), str(id(p2)))
                    child.island_id = island_id
                    new_island.append(child)

                new_islands.append(new_island)

            # Update experience dari populasi gabungan (tiap 3 gen)
            if gen % 3 == 0:
                merged = self._merge_islands(new_islands)
                self._update_experience(merged)
                self._update_gene_usage(merged)
                if gen % 9 == 0:
                    self._mine_patterns(merged)

            # ── v3: Self-Expanding Subsystems ─────────────────────────────
            # Gene Synthesizer — distilasi dari genome terbaik
            if gen % self.config.synthesizer_interval == 0 and gen > 0:
                merged_flat = self._merge_islands(new_islands)
                top_genomes = sorted(merged_flat, key=lambda g: g.fitness, reverse=True)[:5]
                self._run_synthesizer(top_genomes)

            # Template Mutator — varian dari gen yang ada
            if gen % self.config.mutator_interval == 0 and gen > 0:
                self._run_template_mutator()

            # Code Harvester — scan filesystem (jarang, mahal)
            if gen % self.config.harvester_interval == 0 and gen > 0:
                self._run_harvester()

            # Self-Reflective Scanner — introspeksi engine sendiri
            if gen % self.config.self_scan_interval == 0 and gen > 0:
                self._run_self_scanner()

            # Gene Pruner — bersihkan pool berkala
            if gen % self.config.pruner_interval == 0 and gen > 0:
                self._run_pruner()

            # Migrasi antar island
            if gen % self.config.migration_interval == 0 and gen > 0:
                new_islands = self._migrate_between_islands(new_islands)
                logger.debug(f"Gen {gen}: Migration occurred across {n_islands} islands.")

            # Adaptive hyperparameters
            self._adaptive_hyperparameters(best_fitness)

            islands = new_islands

            # Checkpoint
            if gen % 10 == 0 or gen == gens - 1:
                flat = self._merge_islands(islands)
                self.kb.save_checkpoint(f"{task_id}_gen{gen}", flat, gen, task_id)

            logger.debug(
                f"Gen {gen:3d} | Best: {best_fitness:.4f} | "
                f"MutRate: {self._current_mutation_rate:.3f} | "
                f"Stagnation: {self.stagnation_counter}"
            )

        # ── Finalisasi ─────────────────────────────────────────────────────
        if best_genome:
            self._finalize(task_id, best_genome, best_fitness)
            return best_genome.compiled_code
        else:
            logger.warning(f"No solution found for task '{task_id}'.")
            return None

    def _finalize(self, task_id: str, best_genome: Genome, best_fitness: float):
        """Simpan solusi terbaik dan update experience."""
        sol = Solution(
            task_id=task_id,
            code=best_genome.compiled_code,
            fitness=best_fitness,
            execution_time=best_genome.execution_time,
            memory_estimate=best_genome.memory_estimate,
            created_at=time.time(),
            last_used=time.time(),
            use_count=1,
            version=int(self.config.version),
        )
        self.kb.save_solution(sol)
        self._save_experience()
        logger.info(
            f"Solution saved for '{task_id}'. Fitness: {best_fitness:.4f}. "
            f"Experience persisted ({len(self.gene_weights)} gene weights)."
        )

    # ──────────────────────────────────────────────────────────────────────────
    # META-EVOLUTION (evolusi konfigurasi itu sendiri)
    # ──────────────────────────────────────────────────────────────────────────

    def _meta_evolve(self):
        """Mutasi hyperparameter konfigurasi secara acak kecil."""
        old = self.config
        new = EvolutionConfig(
            population_size=int(old.population_size * random.uniform(0.9, 1.1)),
            mutation_rate=old.mutation_rate * random.uniform(0.85, 1.15),
            crossover_rate=old.crossover_rate * random.uniform(0.85, 1.15),
            weight_correctness=old.weight_correctness * random.uniform(0.95, 1.05),
            weight_speed=old.weight_speed * random.uniform(0.9, 1.1),
            weight_memory=old.weight_memory * random.uniform(0.9, 1.1),
            weight_simplicity=old.weight_simplicity * random.uniform(0.9, 1.1),
            weight_novelty=old.weight_novelty * random.uniform(0.9, 1.1),
            learning_rate=old.learning_rate * random.uniform(0.9, 1.1),
            num_islands=old.num_islands,
        )
        # Clamp
        new.population_size = max(10, min(100, new.population_size))
        new.mutation_rate = max(0.05, min(0.9, new.mutation_rate))
        new.crossover_rate = max(0.2, min(0.95, new.crossover_rate))
        new.learning_rate = max(0.01, min(0.5, new.learning_rate))

        if random.random() < 0.3:
            self.config = new
            logger.info(f"Meta-evolution: new config applied (version={new.version})")

    # ──────────────────────────────────────────────────────────────────────────
    # INTERNAL OPTIMIZATION  (self-improvement)
    # ──────────────────────────────────────────────────────────────────────────

    def _get_source_of_method(self, method: Callable) -> str:
        return inspect.getsource(method)

    def _replace_method_in_file(
        self, file_path: Path, method_name: str, new_code: str
    ) -> bool:
        if not file_path.exists():
            logger.error(f"File {file_path} not found.")
            return False
        backup_path = file_path.with_suffix(file_path.suffix + ".bak")
        shutil.copy(file_path, backup_path)
        try:
            with open(file_path, "r") as f:
                content = f.read()
            tree = ast.parse(content)

            class MethodReplacer(ast.NodeTransformer):
                def visit_FunctionDef(self, node):
                    if node.name == method_name:
                        try:
                            new_ast = ast.parse(
                                f"def {method_name}(*args, **kwargs):\n{new_code}"
                            ).body[0]
                            node.body = new_ast.body
                        except:
                            logger.error("Failed to parse new_code.")
                    return node

            new_tree = MethodReplacer().visit(tree)
            ast.fix_missing_locations(new_tree)
            with open(file_path, "w") as f:
                f.write(ast.unparse(new_tree))
            logger.info(f"Method '{method_name}' updated in {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to replace method: {e}")
            shutil.copy(backup_path, file_path)
            return False

    def optimize_internal_method(
        self,
        method: Callable,
        test_inputs: List[Tuple],
        expected_outputs: List[Any],
        method_name: str,
        file_path: Path,
        generations: int = 20,
    ) -> bool:
        num_args = len(test_inputs[0])
        baseline_time = 0.0
        baseline_mem = 0.0

        for inp, exp in zip(test_inputs, expected_outputs):
            start = time.perf_counter()
            try:
                res = method(*inp)
                dur = time.perf_counter() - start
                if res != exp:
                    logger.warning("Baseline failed on test cases.")
                    return False
                baseline_time += dur
                baseline_mem += len(repr(res)) * 8
            except:
                return False

        baseline_avg_time = baseline_time / len(test_inputs)
        baseline_avg_mem = baseline_mem / len(test_inputs)

        pop_size = min(20, self.config.population_size)
        population = [self._random_genome(num_args) for _ in range(pop_size)]
        best_genome: Optional[Genome] = None
        best_fit = float("-inf")

        for gen in range(generations):
            for g in population:
                self._evaluate_genome(g, method_name, num_args, test_inputs, expected_outputs)
            population.sort(key=lambda x: x.fitness, reverse=True)
            if population[0].fitness > best_fit:
                best_fit = population[0].fitness
                best_genome = population[0]

            new_pop = population[:self.config.elitism_count]
            while len(new_pop) < pop_size:
                p1 = self._tournament_select(population)
                p2 = self._tournament_select(population)
                child = self._crossover(p1, p2) if random.random() < self._current_crossover_rate else Genome(genes=p1.genes.copy())
                if random.random() < self._current_mutation_rate:
                    child = self._mutate(child)
                new_pop.append(child)
            population = new_pop

        if best_genome:
            code = best_genome.compiled_code
            lines = code.split("\n")
            body = "\n".join(lines[1:]) if len(lines) > 1 else code

            new_t = new_m = 0.0
            ok = True
            for inp, exp in zip(test_inputs, expected_outputs):
                s, r, d, m, _ = self.sandbox.execute(code, method_name, inp)
                if not s or r != exp:
                    ok = False
                    break
                new_t += d; new_m += m

            if ok:
                n = len(test_inputs)
                if (new_t / n < baseline_avg_time * 0.95) or (new_m / n < baseline_avg_mem * 0.9):
                    logger.info(f"Improved internal method '{method_name}'")
                    return self._replace_method_in_file(file_path, method_name, body)
        return False

    # ──────────────────────────────────────────────────────────────────────────
    # AUTONOMOUS CYCLE & GOAL PROCESSING
    # ──────────────────────────────────────────────────────────────────────────

    def run_autonomous_cycle(self, arint_instance=None):
        self._internal_cycle_count += 1

        if (self.config.auto_internal_optimization
                and self._internal_cycle_count % self.config.internal_optimization_interval == 0):
            logger.info("Running internal optimization cycle...")
            try:
                from core import sws_logic
                method = sws_logic._reason
                test_inputs = [(sws_logic,)]
                expected = ["dummy insight"]
                file_path = Path(sws_logic.__file__)
                self.optimize_internal_method(
                    method, test_inputs, expected, "_reason", file_path, generations=10
                )
            except Exception as e:
                logger.debug(f"Internal optimization skipped: {e}")

        if random.random() < self.config.meta_evolution_rate:
            self._meta_evolve()

    def process_goal(self, goal_manager, goal_index: int):
        subgoals = goal_manager.goals.get("subgoals", [])
        if goal_index >= len(subgoals):
            return

        goal = subgoals[goal_index]
        metadata = goal.get("metadata", {})
        if not metadata.get("needs_code"):
            return

        test_cases = metadata.get("test_cases")
        if not test_cases:
            logger.warning("Goal marked needs_code but no test_cases.")
            return

        inputs = [tuple(tc["input"]) for tc in test_cases]
        outputs_list = [tc["output"] for tc in test_cases]
        task_id = goal.get("id", f"goal_{goal_index}")

        code = self.evolve_external(task_id, inputs, outputs_list)

        if code:
            deploy_path = Path(f"tools/generated_{task_id}.py")
            deploy_path.parent.mkdir(parents=True, exist_ok=True)
            with open(deploy_path, "w") as f:
                f.write(code)
            logger.info(f"Solution written to {deploy_path}")
            goal_manager.update_subgoal_progress(goal_index, 1.0)
            goal_manager.add_subgoal_insight(goal_index, f"Evolved solution for {task_id}")
            goal_manager.save()
        else:
            logger.warning(f"Failed to evolve for goal '{task_id}'")

    # ──────────────────────────────────────────────────────────────────────────
    # DIAGNOSTIC & REPORTING
    # ──────────────────────────────────────────────────────────────────────────

    def get_gene_leaderboard(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Tampilkan gen dengan bobot tertinggi (yang paling sering sukses)."""
        board = []
        for gid, w in sorted(self.gene_weights.items(), key=lambda x: x[1], reverse=True):
            gene = self.gene_pool.get(gid)
            if gene:
                total = self.gene_success[gid] + self.gene_failure[gid]
                sr = self.gene_success[gid] / max(total, 1)
                board.append({
                    "id": gid,
                    "description": gene.description,
                    "origin": gene.origin,
                    "weight": round(w, 4),
                    "success_rate": round(sr, 3),
                    "gauntlet_score": round(gene.gauntlet_score, 3),
                    "usage": gene.usage_count,
                    "success": self.gene_success[gid],
                    "failure": self.gene_failure[gid],
                })
        return board[:top_n]

    def get_top_patterns(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """Tampilkan pola gen terbaik yang ditemukan."""
        result = []
        for p in self.known_patterns[:top_n]:
            result.append({
                "pattern": " → ".join(p.gene_ids),
                "avg_fitness": round(p.avg_fitness, 4),
                "occurrences": p.occurrence_count,
            })
        return result

    def get_stats(self) -> Dict[str, Any]:
        """Ringkasan status mesin saat ini."""
        pool_by_origin = defaultdict(int)
        pool_probationary = 0
        for gene in self.gene_pool.values():
            pool_by_origin[gene.origin] += 1
            if gene.is_probationary:
                pool_probationary += 1

        return {
            "version": self.config.version,
            "gene_pool_size": len(self.gene_pool),
            "pool_by_origin": dict(pool_by_origin),
            "pool_probationary": pool_probationary,
            "known_patterns": len(self.known_patterns),
            "novelty_archive_size": len(self.novelty_archive),
            "fitness_cache_size": len(self._fitness_cache),
            "stagnation_counter": self.stagnation_counter,
            "best_historical_fitness": round(self.best_historical_fitness, 4),
            "current_mutation_rate": round(self._current_mutation_rate, 4),
            "current_crossover_rate": round(self._current_crossover_rate, 4),
            "internal_cycles": self._internal_cycle_count,
            "pruned_total": len(self.pruner.pruned_history),
            "harvest_roots": self._harvest_roots,
        }

    def get_pool_origins(self) -> List[Dict[str, Any]]:
        """Detail semua gen di pool berdasarkan asal-usulnya."""
        result = []
        for gene in sorted(self.gene_pool.values(), key=lambda g: self.gene_weights.get(g.id, 0), reverse=True):
            result.append({
                "id": gene.id,
                "origin": gene.origin,
                "gauntlet_score": round(gene.gauntlet_score, 3),
                "weight": round(self.gene_weights.get(gene.id, 0), 3),
                "usage": gene.usage_count,
                "probationary": gene.is_probationary,
                "source_hint": gene.source_hint[:50] if gene.source_hint else "",
            })
        return result


# ─────────────────────────────────────────────────────────────────────────────
# FACTORY
# ─────────────────────────────────────────────────────────────────────────────

def create_evolution_engine(
    config: Optional[EvolutionConfig] = None,
    knowledge_db: str = "memory/evolution/knowledge.db",
) -> ExperienceDrivenEvolutionEngine:
    """Factory function — drop-in replacement untuk create_unified_engine."""
    return ExperienceDrivenEvolutionEngine(config=config, knowledge_db=knowledge_db)


# Alias backward compat
create_unified_engine = create_evolution_engine
UnifiedEvolutionEngine = ExperienceDrivenEvolutionEngine
SelfExpandingEvolutionEngine = ExperienceDrivenEvolutionEngine


# ─────────────────────────────────────────────────────────────────────────────
# DEMO / SMOKE TEST
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("=== SelfExpandingEvolutionEngine v3.0 Demo ===")

    engine = create_evolution_engine(
        config=EvolutionConfig(
            population_size=30,
            generations=40,
            num_islands=3,
            use_knowledge_base=False,
            synthesizer_interval=5,
            mutator_interval=8,
            harvester_interval=20,
            self_scan_interval=25,
            pruner_interval=15,
        )
    )

    print(f"\n[Pool Awal] {len(engine.gene_pool)} genes (semua 'default')")

    # Task 1: Penjumlahan
    print("\n[Task 1] Mencari solusi penjumlahan...")
    code = engine.evolve_external(
        task_id="add_two",
        inputs=[(1, 2), (3, 4), (5, 6), (10, 20)],
        outputs=[3, 7, 11, 30],
    )
    print(f"Solusi: {'ditemukan' if code else 'tidak ditemukan'}")
    if code:
        print(code)

    # Task 2: Sum of list
    print("\n[Task 2] Sum of list...")
    code2 = engine.evolve_external(
        task_id="sum_list",
        inputs=[([1, 2, 3],), ([4, 5, 6],), ([10, 20, 30],)],
        outputs=[6, 15, 60],
    )
    print(f"Solusi: {'ditemukan' if code2 else 'tidak ditemukan'}")

    # Pool growth report
    print(f"\n[Pool Setelah Evolusi] {len(engine.gene_pool)} genes")

    print("\n[Gene Leaderboard Top 8]")
    for entry in engine.get_gene_leaderboard(8):
        print(
            f"  {entry['id']:30s} "
            f"origin={entry.get('origin','?'):12s} "
            f"weight={entry['weight']:.3f}  "
            f"sr={entry['success_rate']:.2f}"
        )

    print("\n[Pool Origins]")
    stats = engine.get_stats()
    for origin, count in stats["pool_by_origin"].items():
        print(f"  {origin:15s}: {count} genes")
    print(f"  Probationary    : {stats['pool_probationary']} genes")
    print(f"  Pruned (total)  : {stats['pruned_total']} genes")

    print("\n[Top Patterns]")
    for p in engine.get_top_patterns(3):
        print(f"  {p['pattern']}  (fit={p['avg_fitness']:.3f}, occ={p['occurrences']})")

    print("\n[Engine Stats]")
    for k, v in stats.items():
        if k not in ("pool_by_origin",):
            print(f"  {k}: {v}")
