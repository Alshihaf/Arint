# code_genetic.py
import ast
import random
import copy
import multiprocessing
import time
import math
import sys
from typing import List, Dict, Any, Union, Tuple

# --- AST Utilities untuk Generasi Kode Dinamis ---
class ASTGen:
    OPERATORS = [ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.BitXor]
    COMPARES = [ast.Eq, ast.NotEq, ast.Lt, ast.Gt, ast.LtE, ast.GtE]
    
    @staticmethod
    def random_constant():
        # Menghasilkan angka acak (int/float)
        val = random.choice([random.randint(-10, 10), random.random() * 10])
        return ast.Constant(value=val)

    @staticmethod
    def random_var(arg_name='x'):
        return ast.Name(id=arg_name, ctx=ast.Load())

    @staticmethod
    def generate_expression(depth=0, max_depth=3, var_name='x'):
        if depth >= max_depth or random.random() < 0.3:
            return ASTGen.random_var(var_name) if random.random() > 0.5 else ASTGen.random_constant()
        
        op_class = random.choice(ASTGen.OPERATORS)
        left = ASTGen.generate_expression(depth + 1, max_depth, var_name)
        right = ASTGen.generate_expression(depth + 1, max_depth, var_name)
        return ast.BinOp(left=left, op=op_class(), right=right)

    @staticmethod
    def create_solution_template(body_nodes: List[ast.stmt], arg_name='x'):
        func_def = ast.FunctionDef(
            name='solution',
            args=ast.arguments(
                posonlyargs=[], args=[ast.arg(arg=arg_name)], kwonlyargs=[],
                kw_defaults=[], defaults=[]
            ),
            body=body_nodes,
            decorator_list=[]
        )
        return ast.fix_missing_locations(ast.Module(body=[func_def], type_ignores=[]))

class CodeGenetic:
    def __init__(self, target_tests: List[Dict[str, Any]], 
                 population_size: int = 50, 
                 max_depth: int = 4):
        self.target_tests = target_tests
        self.pop_size = population_size
        self.max_depth = max_depth
        self.population = []
        self.fitness_cache = {}
        
        self.timeout = 0.5
        self.mutation_rate = 0.4
        self.crossover_rate = 0.5
        self.elitism_count = 3

    @staticmethod
    def _safe_exec(code_str: str, test_input: Any, return_dict: dict):
        try:
            local_env = {}
            compiled = compile(code_str, '<string>', 'exec')
            exec(compiled, {}, local_env)
            
            func = local_env.get('solution')
            if not callable(func):
                return_dict['error'] = "No function found"
                return

            res = func(test_input)
            return_dict['result'] = res
        except Exception as e:
            return_dict['error'] = str(e)

    def _calculate_error(self, actual, expected) -> float:
        if actual == expected:
            return 0.0
        
        if type(actual) != type(expected):
            return 1e9

        if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
            try:
                diff = abs(actual - expected)
                # Cegah overflow
                if diff > 1e9: return 1e9
                return diff
            except:
                return 1e9
        
        return 0.0 if actual == expected else 100.0

    def _evaluate(self, code: str) -> float:
        if code in self.fitness_cache:
            return self.fitness_cache[code]
        
        total_error = 0.0
        passed_count = 0
        
        try:
            ast.parse(code)
        except SyntaxError:
            return -1.0

        for test in self.target_tests:
            manager = multiprocessing.Manager()
            ret_dict = manager.dict()
            
            p = multiprocessing.Process(target=self._safe_exec, 
                                        args=(code, test['input'], ret_dict))
            p.start()
            p.join(self.timeout)

            if p.is_alive():
                p.terminate()
                p.join()
                total_error += 1000.0
            elif 'error' in ret_dict:
                total_error += 500.0
            else:
                actual = ret_dict.get('result')
                err = self._calculate_error(actual, test['output'])
                total_error += err
                if err == 0.0:
                    passed_count += 1

        try:
            error_score = 1.0 / (1.0 + total_error)
        except OverflowError:
            error_score = 0.0

        pass_ratio = passed_count / len(self.target_tests)
        
        final_fitness = (pass_ratio * 100) + (error_score * 10)
        final_fitness -= len(code) * 0.005

        self.fitness_cache[code] = final_fitness
        return final_fitness

    def init_population(self):
        self.population = []
        for _ in range(self.pop_size):

            expr = ASTGen.generate_expression(max_depth=self.max_depth)
            body = [ast.Return(value=expr)]

            if random.random() < 0.3:
                assign = ast.Assign(
                    targets=[ast.Name(id='temp', ctx=ast.Store())],
                    value=ASTGen.generate_expression(max_depth=2)
                )
                body.insert(0, assign)

            tree = ASTGen.create_solution_template(body)
            try:
                self.population.append(ast.unparse(tree))
            except:
                self.population.append("def solution(x):\n    return 0")

    def crossover(self, code1: str, code2: str) -> str:
        try:
            tree1 = ast.parse(code1)
            tree2 = ast.parse(code2)

            nodes1 = [n for n in ast.walk(tree1) if isinstance(n, ast.BinOp)]
            nodes2 = [n for n in ast.walk(tree2) if isinstance(n, ast.BinOp)]
            
            if nodes1 and nodes2:
                target = random.choice(nodes1)
                source = copy.deepcopy(random.choice(nodes2))

                target.left = source.left
                target.op = source.op
                target.right = source.right
                
                return ast.unparse(tree1)
        except:
            pass
        return code1

    def mutate(self, code: str) -> str:
        try:
            tree = ast.parse(code)
        except:
            return code

        mutation_type = random.choice(['op_flip', 'const_jitter', 'expr_replace', 'insert_stmt'])
        
        class Mutator(ast.NodeTransformer):
            def __init__(self, mode):
                self.mode = mode
                self.mutated = False

            def visit_BinOp(self, node):
                if self.mutated: return node
                
                if self.mode == 'op_flip' and random.random() < 0.5:
                    node.op = random.choice(ASTGen.OPERATORS)()
                    self.mutated = True
                
                elif self.mode == 'expr_replace' and random.random() < 0.2:
                    self.mutated = True
                    return ASTGen.generate_expression(max_depth=2)
                
                return self.generic_visit(node)

            def visit_Constant(self, node):
                if self.mutated: return node
                if self.mode == 'const_jitter' and isinstance(node.value, (int, float)):

                    if random.random() < 0.5:
                        node.value += random.choice([-1, 1])
                    else:
                        node.value = int(node.value * random.uniform(0.5, 1.5))
                    self.mutated = True
                return node

        mutator = Mutator(mutation_type)
        new_tree = mutator.visit(tree)

        if mutation_type == 'insert_stmt' and not mutator.mutated:
            for node in ast.walk(new_tree):
                if isinstance(node, ast.FunctionDef) and node.name == 'solution':

                    new_stmt = ast.Assign(
                        targets=[ast.Name(id='x', ctx=ast.Store())],
                        value=ast.BinOp(
                            left=ast.Name(id='x', ctx=ast.Load()),
                            op=ast.Add(),
                            right=ast.Constant(value=random.randint(1, 5))
                        )
                    )
                    node.body.insert(0, new_stmt)
                    break

        ast.fix_missing_locations(new_tree)
        return ast.unparse(new_tree)

    def evolve(self, generations: int = 50):
        self.init_population()
        
        best_overall_code = ""
        best_overall_fitness = -float('inf')

        print(f"Starting evolution with pop_size={self.pop_size}...")

        for gen in range(generations):
            scored_pop = []
            for indiv in self.population:
                fit = self._evaluate(indiv)
                scored_pop.append((fit, indiv))

            scored_pop.sort(key=lambda x: x[0], reverse=True)
            
            current_best_fit, current_best_code = scored_pop[0]

            if current_best_fit > best_overall_fitness:
                best_overall_fitness = current_best_fit
                best_overall_code = current_best_code

            avg_fit = sum(s[0] for s in scored_pop) / len(scored_pop)
            print(f"Gen {gen+1:02d} | Best Fit: {current_best_fit:.4f} | Avg: {avg_fit:.2f} | Code: {current_best_code.replace('def solution(x):', '').strip()[:30]}...")

            if current_best_fit >= 105: 
                print("\n>>> Perfect Solution Found!")
                break

            new_pop = []

            for i in range(self.elitism_count):
                new_pop.append(scored_pop[i][1])

            while len(new_pop) < self.pop_size:
                parent1 = self._tournament_select(scored_pop)
                parent2 = self._tournament_select(scored_pop)
                
                child = parent1

                if random.random() < self.crossover_rate:
                    child = self.crossover(parent1, parent2)
                if random.random() < self.mutation_rate:
                    child = self.mutate(child)
                
                new_pop.append(child)
            
            self.population = new_pop

        return best_overall_code

    def _tournament_select(self, scored_pop):
        k = 4
        candidates = random.sample(scored_pop, k)
        return max(candidates, key=lambda x: x[0])[1]

# --- Main Driver ---
if __name__ == "__main__":

    inputs = list(range(-5, 6)) 
    tests = [{'input': i, 'output': (i**2) + (2*i) + 1} for i in inputs]
    
    print(f"Target: x^2 + 2x + 1")
    print("-" * 30)
    
    ga = CodeGenetic(target_tests=tests, population_size=100, max_depth=4)

    ga.mutation_rate = 0.6 
    
    start_time = time.time()
    best_code = ga.evolve(generations=40)
    end_time = time.time()
    
    print("\n" + "="*30)
    print("FINAL RESULT")
    print("="*30)
    print(best_code)
    print(f"\nExecution Time: {end_time - start_time:.2f}s")

    try:
        ns = {}
        exec(best_code, {}, ns)
        sol = ns['solution']
        print(f"Test x=10 -> {sol(10)} (Expected: {10**2 + 20 + 1})")
    except:
        print("Code produced error on verification.")