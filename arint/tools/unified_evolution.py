#!/usr/bin/env python3
# tools/gene_lab.py
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

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Callable

logger = logging.getLogger("UnifiedEvolution")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

@dataclass
class EvolutionConfig:
    population_size: int = 30
    generations: int = 50
    mutation_rate: float = 0.3
    crossover_rate: float = 0.8
    elitism_count: int = 2
    tournament_size: int = 5
    timeout_seconds: float = 2.0
    # Bobot multi‑objective
    weight_correctness: float = 10.0
    weight_speed: float = 1.0
    weight_memory: float = 0.5
    weight_simplicity: float = 0.2
    # Self‑improvement
    auto_internal_optimization: bool = True
    internal_optimization_interval: int = 100
    # Knowledge base
    use_knowledge_base: bool = True
    max_knowledge_age: float = 7 * 24 * 3600
    # Meta‑evolution
    meta_evolution_rate: float = 0.01
    version: float = 1.0


@dataclass
class CodeGene:
    id: str
    template: str
    arity: int
    complexity: float 
    description: str = ""


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

class AdvancedSandbox:
    SAFE_BUILTINS = {
        "range": range,
        "len": len,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        "sum": sum,
        "max": max,
        "min": min,
        "abs": abs,
        "round": round,
        "enumerate": enumerate,
        "zip": zip,
        "sorted": sorted,
        "reversed": reversed,
        "any": any,
        "all": all,
        "print": lambda *x: None,
    }

    def __init__(self, timeout: float = 2.0):
        self.timeout = timeout

    def execute(self, code: str, func_name: str, args: tuple) -> Tuple[bool, Any, float, float, str]:
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

        thread = threading.Thread(target=target)
        thread.start()
        thread.join(self.timeout)

        if thread.is_alive():
            return False, None, self.timeout, 0.0, "TimeoutError: Execution took too long"

        mem = 0.0
        if result["output"] is not None:
            try:
                mem = len(repr(result["output"])) * 8
            except:
                pass

        return (
            result["success"],
            result["output"],
            result["exec_time"],
            mem,
            result["error"],
        )

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
            c.execute("""
                CREATE TABLE IF NOT EXISTS solutions (
                    task_id TEXT PRIMARY KEY,
                    code TEXT,
                    fitness REAL,
                    exec_time REAL,
                    mem_estimate REAL,
                    created_at REAL,
                    last_used REAL,
                    use_count INTEGER,
                    version INTEGER
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id TEXT PRIMARY KEY,
                    population TEXT,
                    generation INTEGER,
                    task_id TEXT,
                    timestamp REAL
                )
            """)
            self.conn.commit()

    def get_solution(self, task_id: str) -> Optional[Solution]:
        with self.lock:
            c = self.conn.cursor()
            c.execute("SELECT * FROM solutions WHERE task_id = ?", (task_id,))
            row = c.fetchone()
            if row:
                return Solution(*row)
            return None

    def save_solution(self, sol: Solution):
        with self.lock:
            c = self.conn.cursor()
            c.execute("""
                INSERT OR REPLACE INTO solutions
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sol.task_id, sol.code, sol.fitness, sol.execution_time,
                sol.memory_estimate, sol.created_at, sol.last_used,
                sol.use_count, sol.version
            ))
            self.conn.commit()

    def update_usage(self, task_id: str):
        with self.lock:
            c = self.conn.cursor()
            c.execute("""
                UPDATE solutions SET last_used = ?, use_count = use_count + 1
                WHERE task_id = ?
            """, (time.time(), task_id))
            self.conn.commit()

    def save_checkpoint(self, ckpt_id: str, population: List[Genome], generation: int, task_id: str):
        data = []
        for g in population:
            data.append({
                "genes": [gene.id for gene in g.genes],
                "fitness": g.fitness,
                "generation": g.generation,
                "parent_ids": g.parent_ids,
                "exec_time": g.execution_time,
                "mem": g.memory_estimate,
            })
        with self.lock:
            c = self.conn.cursor()
            c.execute("""
                INSERT OR REPLACE INTO checkpoints
                VALUES (?, ?, ?, ?, ?)
            """, (ckpt_id, json.dumps(data), generation, task_id, time.time()))
            self.conn.commit()

    def load_checkpoint(self, ckpt_id: str, gene_pool: Dict[str, CodeGene]) -> Tuple[List[Genome], int, str]:
        with self.lock:
            c = self.conn.cursor()
            c.execute("SELECT population, generation, task_id FROM checkpoints WHERE id = ?", (ckpt_id,))
            row = c.fetchone()
            if not row:
                raise ValueError("Checkpoint not found")
            data = json.loads(row[0])
            generation = row[1]
            task_id = row[2]
            population = []
            for d in data:
                genes = [gene_pool[gid] for gid in d["genes"] if gid in gene_pool]
                g = Genome(
                    genes=genes,
                    fitness=d.get("fitness", 0.0),
                    generation=d.get("generation", 0),
                    parent_ids=tuple(d.get("parent_ids", ("", ""))),
                    execution_time=d.get("exec_time", 0.0),
                    memory_estimate=d.get("mem", 0.0),
                )
                population.append(g)
            return population, generation, task_id

    def close(self):
        self.conn.close()

DEFAULT_GENE_POOL = [
    # --- OPERASI MATEMATIKA DASAR & LANJUT ---
    CodeGene("assign_add", "    result = arg1 + arg2\n", 2, 1.0, "penjumlahan"),
    CodeGene("assign_sub", "    result = arg1 - arg2\n", 2, 1.0, "pengurangan"),
    CodeGene("assign_mul", "    result = arg1 * arg2\n", 2, 1.0, "perkalian"),
    CodeGene("assign_div", "    result = (arg1 / arg2) if arg2 != 0 else 0\n", 2, 1.2, "pembagian aman"),
    CodeGene("math_pow", "    result = math.pow(arg1, arg2) if abs(arg1) < 100 and arg2 < 10 else 0\n", 2, 2.0, "pangkat"),
    CodeGene("math_sqrt", "    result = math.sqrt(abs(arg1))\n", 1, 1.5, "akar kuadrat"),
    CodeGene("math_log", "    result = math.log(abs(arg1) + 1)\n", 1, 2.0, "logaritma natural"),
    
    # --- STATISTIK & ANALISIS DATA ---
    CodeGene("stat_mean", "    result = statistics.mean(arg1) if arg1 else 0\n", 1, 2.0, "rata-rata"),
    CodeGene("stat_median", "    result = statistics.median(arg1) if arg1 else 0\n", 1, 2.5, "nilai tengah"),
    CodeGene("stat_stdev", "    result = statistics.stdev(arg1) if len(arg1) > 1 else 0\n", 1, 3.0, "standar deviasi"),
    CodeGene("list_max_min", "    result = (max(arg1), min(arg1)) if arg1 else (0, 0)\n", 1, 1.8, "nilai ekstrim"),
    
    # --- MANIPULASI STRING & REGEX ---
    CodeGene("string_concat", "    result = str(arg1) + str(arg2)\n", 2, 1.0, "gabung string"),
    CodeGene("string_split", "    result = str(arg1).split(str(arg2)) if str(arg2) else str(arg1).split()\n", 2, 2.0, "split string"),
    CodeGene("regex_find", "    result = re.findall(str(arg2), str(arg1))\n", 2, 3.5, "regex findall"),
    CodeGene("string_clean", "    result = ''.join(e for e in str(arg1) if e.isalnum())\n", 1, 2.2, "pembersihan karakter"),

    # --- LIST COMPREHENSION & TRANSFORMASI KOMPLEKS ---
    CodeGene("list_sort", "    result = sorted(arg1)\n", 1, 2.0, "pengurutan"),
    CodeGene("list_reverse", "    result = arg1[::-1]\n", 1, 1.2, "membalik list"),
    CodeGene("list_unique", "    result = list(set(arg1))\n", 1, 2.0, "elemen unik"),
    CodeGene("list_filter_pos", "    result = [x for x in arg1 if isinstance(x, (int, float)) and x > 0]\n", 1, 2.5, "filter bilangan positif"),
    CodeGene("list_map_scale", "    result = [x * arg2 for x in arg1] if isinstance(arg1, list) else arg1\n", 2, 2.5, "skalasi list"),
    CodeGene("list_flatten", "    result = list(itertools.chain.from_iterable(arg1)) if any(isinstance(i, list) for i in arg1) else arg1\n", 1, 3.5, "meratakan list nested"),

    # --- LOGIKA & KONTROL ---
    CodeGene("logic_if_else", "    result = arg1 if bool(arg1) else arg2\n", 2, 1.5, "percabangan simpel"),
    CodeGene("logic_and", "    result = arg1 and arg2\n", 2, 1.0, "logika AND"),
    CodeGene("dict_count", "    result = {x: arg1.count(x) for x in set(arg1)}\n", 1, 3.0, "frekuensi elemen (counter)"),

# --- ERROR HANDLING & VALIDATION ---
CodeGene("try_parse_int", "    try: result = int(arg1)\n    except: result = 0\n", 1, 2.0, "konversi int aman"),
CodeGene("val_is_not_none", "    result = arg1 is not None\n", 1, 1.0, "validasi non-null"),

# --- COMPLEX LOGIC ---
CodeGene("logic_compare", "    result = (arg1 == arg2) if arg3 == '==' else (arg1 > arg2) if arg3 == '>' else (arg1 < arg2)\n", 3, 2.5, "perbandingan dinamis"),
CodeGene("logic_in_range", "    result = arg2 <= arg1 <= arg3\n", 3, 2.0, "cek rentang nilai"),
CodeGene("logic_is_instance", "    result = isinstance(arg1, arg2)\n", 2, 1.5, "pengecekan tipe data"),

# --- FUNCTIONAL PROGRAMMING ---
CodeGene("list_reduce_sum", "    result = sum(arg1) if isinstance(arg1, list) else 0\n", 1, 1.2, "total nilai list"),
CodeGene("list_any_all", "    result = any(arg1) if arg2 == 'any' else all(arg1)\n", 2, 2.0, "cek keberadaan/seluruhnya"),
CodeGene("list_chunk", "    result = [arg1[i:i + arg2] for i in range(0, len(arg1), arg2)] if arg2 > 0 else arg1\n", 2, 3.5, "pemecahan list (chunking)"),

# --- ADVANCED DATA STRUCTURES ---
CodeGene("dict_get", "    result = arg1.get(arg2, None) if isinstance(arg1, dict) else {}\n", 2, 1.5, "ambil nilai dict"),
CodeGene("dict_merge", "    result = {**arg1, **arg2} if isinstance(arg1, dict) and isinstance(arg2, dict) else arg1\n", 2, 2.5, "gabung dictionary"),
CodeGene("list_zip", "    result = list(zip(arg1, arg2)) if isinstance(arg1, list) and isinstance(arg2, list) else []\n", 2, 2.0, "pasangkan dua list"),
CodeGene("list_enumerate", "    result = list(enumerate(arg1)) if isinstance(arg1, list) else []\n", 1, 1.5, "indeksasi list"),
    
    # --- TERMINAL ---
    CodeGene("return_res", "    return result\n", 0, 0.5, "return hasil akhir"),
]

class UnifiedEvolutionEngine:
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

        self._internal_cycle_count = 0
        self._original_source = None 

        self._meta_generation = 0
        self._best_config = self.config

        logger.info("UnifiedEvolutionEngine initialized.")
    def _compile_genome(self, genome: Genome, func_name: str, num_args: int) -> str:
        args_str = ", ".join([f"arg{i+1}" for i in range(num_args)])
        code = f"def {func_name}({args_str}):\n"
        code += "    result = None\n"
        for gene in genome.genes:
            code += gene.template
        return code

    def _validate_syntax(self, code: str) -> bool:
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def _random_genome(self, num_args: int) -> Genome:
        non_return = [g for g in self.gene_pool.values() if g.id != "return_res"]
        length = random.randint(2, 6)
        genes = random.choices(non_return, k=length)
        return_gene = self.gene_pool["return_res"]
        genes.append(return_gene)
        return Genome(genes=genes)

    def _crossover(self, p1: Genome, p2: Genome) -> Genome:
        split = min(len(p1.genes), len(p2.genes)) // 2
        child_genes = p1.genes[:split] + p2.genes[split:]
        child_genes = [g for g in child_genes if g.id != "return_res"]
        child_genes.append(self.gene_pool["return_res"])
        return Genome(genes=child_genes)

    def _mutate(self, genome: Genome) -> Genome:
        if len(genome.genes) <= 1:
            return genome
        idx = random.randint(0, len(genome.genes) - 2)
        non_return = [g for g in self.gene_pool.values() if g.id != "return_res"]
        genome.genes[idx] = random.choice(non_return)
        return genome

    def _tournament_select(self, population: List[Genome]) -> Genome:
        size = min(self.config.tournament_size, len(population))
        tourn = random.sample(population, size)
        return max(tourn, key=lambda g: g.fitness)

    def _evaluate_genome(
        self,
        genome: Genome,
        func_name: str,
        num_args: int,
        test_inputs: List[Tuple],
        expected_outputs: List[Any],
    ) -> float:
        genome.compiled_code = self._compile_genome(genome, func_name, num_args)

        if not self._validate_syntax(genome.compiled_code):
            return -100.0

        total_correct = 0
        total_time = 0.0
        total_mem = 0.0
        errors = 0

        for inp, exp in zip(test_inputs, expected_outputs):
            success, res, dur, mem, err = self.sandbox.execute(
                genome.compiled_code, func_name, inp
            )
            if success and res == exp:
                total_correct += 1
                total_time += dur
                total_mem += mem
            else:
                errors += 1

        correctness = total_correct / len(test_inputs)
        avg_time = total_time / max(len(test_inputs), 1)
        avg_mem = total_mem / max(len(test_inputs), 1)
        simplicity = 1.0 / (len(genome.compiled_code) + 1)

        fitness = (
            self.config.weight_correctness * correctness
            - self.config.weight_speed * avg_time
            - self.config.weight_memory * avg_mem
            + self.config.weight_simplicity * simplicity
        )

        genome.fitness = fitness
        genome.execution_time = avg_time
        genome.memory_estimate = avg_mem
        genome.code_length = len(genome.compiled_code)

        return fitness

    def evolve_external(
        self,
        task_id: str,
        inputs: List[Tuple],
        outputs: List[Any],
        generations: Optional[int] = None,
        pop_size: Optional[int] = None,
        resume_checkpoint: Optional[str] = None,
    ) -> Optional[str]:
        if not inputs or not outputs:
            raise ValueError("inputs and outputs must be non-empty")
        if len(inputs) != len(outputs):
            raise ValueError("inputs and outputs length mismatch")

        num_args = len(inputs[0])
        gens = generations or self.config.generations
        pop = pop_size or self.config.population_size
        func_name = f"auto_{task_id}_{int(time.time())}"

        if self.config.use_knowledge_base:
            cached = self.kb.get_solution(task_id)
            if cached:
                logger.info(f"Task {task_id} found in knowledge base, reusing.")
                self.kb.update_usage(task_id)
                return cached.code

        population: List[Genome] = []
        if resume_checkpoint:
            try:
                population, start_gen, _ = self.kb.load_checkpoint(resume_checkpoint, self.gene_pool)
                logger.info(f"Resumed from checkpoint {resume_checkpoint}")
            except Exception as e:
                logger.warning(f"Failed to load checkpoint: {e}, starting fresh.")
                population = [self._random_genome(num_args) for _ in range(pop)]
        else:
            population = [self._random_genome(num_args) for _ in range(pop)]
            for g in population:
                g.generation = 0

        best_genome: Optional[Genome] = None
        best_fitness = float("-inf")

        for gen in range(gens):
            for g in population:
                self._evaluate_genome(g, func_name, num_args, inputs, outputs)

            population.sort(key=lambda x: x.fitness, reverse=True)
            current_best = population[0]
            if current_best.fitness > best_fitness:
                best_fitness = current_best.fitness
                best_genome = current_best

            logger.debug(f"Gen {gen}: best={current_best.fitness:.2f}")

            if current_best.fitness >= self.config.weight_correctness * 1.0:
                logger.info(f"Perfect solution found at generation {gen}.")
                break

            new_pop = population[: self.config.elitism_count]  # elitisme

            while len(new_pop) < pop:
                p1 = self._tournament_select(population)
                p2 = self._tournament_select(population)

                if random.random() < self.config.crossover_rate:
                    child = self._crossover(p1, p2)
                else:
                    child = Genome(genes=p1.genes.copy())

                if random.random() < self.config.mutation_rate:
                    child = self._mutate(child)

                child.generation = gen + 1
                child.parent_ids = (str(id(p1)), str(id(p2)))
                new_pop.append(child)

            population = new_pop

            if gen % 10 == 0 or gen == gens - 1:
                ckpt_id = f"{task_id}_gen{gen}"
                self.kb.save_checkpoint(ckpt_id, population, gen, task_id)

        if best_genome:
            code = best_genome.compiled_code
            sol = Solution(
                task_id=task_id,
                code=code,
                fitness=best_fitness,
                execution_time=best_genome.execution_time,
                memory_estimate=best_genome.memory_estimate,
                created_at=time.time(),
                last_used=time.time(),
                use_count=1,
                version=1,
            )
            self.kb.save_solution(sol)
            return code
        else:
            logger.warning("No solution found.")
            return None

    def _get_source_of_method(self, method: Callable) -> str:
        import inspect
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
                            func_ast = ast.parse(f"def {method_name}(*args, **kwargs):\n{new_code}").body[0]
                            node.body = func_ast.body
                        except:
                            logger.error("Failed to parse new_code as function body.")
                            return node
                    return node

            new_tree = MethodReplacer().visit(tree)
            ast.fix_missing_locations(new_tree)
            new_content = ast.unparse(new_tree)

            with open(file_path, "w") as f:
                f.write(new_content)

            logger.info(f"Method {method_name} in {file_path} updated successfully.")
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
        func_name = method_name

        baseline_success = True
        baseline_time = 0.0
        baseline_mem = 0.0
        for inp, exp in zip(test_inputs, expected_outputs):
            # Panggil method asli
            start = time.perf_counter()
            try:
                res = method(*inp)
                dur = time.perf_counter() - start
                if res != exp:
                    baseline_success = False
                    break
                baseline_time += dur
                baseline_mem += len(repr(res)) * 8  # estimasi
            except Exception as e:
                baseline_success = False
                break

        if not baseline_success:
            logger.warning("Baseline method failed on test cases. Cannot optimize.")
            return False

        baseline_avg_time = baseline_time / len(test_inputs)
        baseline_avg_mem = baseline_mem / len(test_inputs)

        pop_size = min(20, self.config.population_size)
        population = [self._random_genome(num_args) for _ in range(pop_size)]
        best_genome: Optional[Genome] = None
        best_fitness = float("-inf")

        for gen in range(generations):

            for g in population:
                self._evaluate_genome(g, func_name, num_args, test_inputs, expected_outputs)

            population.sort(key=lambda x: x.fitness, reverse=True)
            if population[0].fitness > best_fitness:
                best_fitness = population[0].fitness
                best_genome = population[0]

            new_pop = population[: self.config.elitism_count]
            while len(new_pop) < pop_size:
                p1 = self._tournament_select(population)
                p2 = self._tournament_select(population)
                if random.random() < self.config.crossover_rate:
                    child = self._crossover(p1, p2)
                else:
                    child = Genome(genes=p1.genes.copy())
                if random.random() < self.config.mutation_rate:
                    child = self._mutate(child)
                new_pop.append(child)
            population = new_pop

        if best_genome:
            code = best_genome.compiled_code
            lines = code.split("\n")
            if len(lines) > 1:
                body = "\n".join(lines[1:])
            else:
                body = code

            new_time = 0.0
            new_mem = 0.0
            success = True
            for inp, exp in zip(test_inputs, expected_outputs):
                ok, res, dur, mem, err = self.sandbox.execute(code, func_name, inp)
                if not ok or res != exp:
                    success = False
                    break
                new_time += dur
                new_mem += mem

            if success:
                new_avg_time = new_time / len(test_inputs)
                new_avg_mem = new_mem / len(test_inputs)

                if (new_avg_time < baseline_avg_time * 0.95) or (new_avg_mem < baseline_avg_mem * 0.9):
                    logger.info(f"Found improved version: time {new_avg_time:.6f} vs {baseline_avg_time:.6f}")
                    # Ganti file
                    return self._replace_method_in_file(file_path, method_name, body)
                else:
                    logger.debug("New version not significantly better.")
            else:
                logger.debug("New version failed tests.")
        else:
            logger.debug("No better solution found.")

        return False

    def run_autonomous_cycle(self, arint_instance):
        self._internal_cycle_count += 1

        if self.config.auto_internal_optimization:
            if self._internal_cycle_count % self.config.internal_optimization_interval == 0:
                logger.info("Running internal optimization...")
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
                    logger.error(f"Internal optimization failed: {e}")

        if random.random() < self.config.meta_evolution_rate:
            self._meta_evolve()

    def _meta_evolve(self):
        old = self.config
        new = EvolutionConfig(
            population_size=int(old.population_size * random.uniform(0.9, 1.1)),
            mutation_rate=old.mutation_rate * random.uniform(0.8, 1.2),
            crossover_rate=old.crossover_rate * random.uniform(0.8, 1.2),
            weight_correctness=old.weight_correctness * random.uniform(0.9, 1.1),
            weight_speed=old.weight_speed * random.uniform(0.9, 1.1),
            weight_memory=old.weight_memory * random.uniform(0.9, 1.1),
            weight_simplicity=old.weight_simplicity * random.uniform(0.9, 1.1),
        )
        new.population_size = max(10, min(100, int(new.population_size)))
        new.mutation_rate = max(0.1, min(0.9, new.mutation_rate))
        new.crossover_rate = max(0.2, min(0.95, new.crossover_rate))

        if random.random() < 0.3:
            self.config = new
            logger.info(f"Meta‑evolution: new config {self.config}")

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
        outputs = [tc["output"] for tc in test_cases]
        task_id = goal.get("id", f"goal_{goal_index}")

        code = self.evolve_external(task_id, inputs, outputs)

        if code:
            deploy_path = Path(f"tools/generated_{task_id}.py")
            with open(deploy_path, "w") as f:
                f.write(code)
            logger.info(f"Solution written to {deploy_path}")

            goal_manager.update_subgoal_progress(goal_index, 1.0)
            goal_manager.add_subgoal_insight(goal_index, f"Evolved solution for {task_id}")
            goal_manager.save()
        else:
            logger.warning(f"Failed to evolve for goal {task_id}")

def create_unified_engine(config: Optional[EvolutionConfig] = None) -> UnifiedEvolutionEngine:
    return UnifiedEvolutionEngine(config=config)