import random
import ast

class CodeGenetic:
    def __init__(self, initial_population):
        self.population = initial_population
        self.fitness_cache = {}

    def _calculate_fitness(self, code):
        if code in self.fitness_cache:
            return self.fitness_cache[code]
        
        # Metrik sederhana: panjang, kompleksitas, dan validitas sintaksis
        score = 0
        try:
            tree = ast.parse(code)
            score += 10  # Bonus untuk sintaks yang valid
            
            num_nodes = len(list(ast.walk(tree)))
            score += num_nodes / 20.0 # Mendorong kompleksitas

            # Penalti untuk kode yang terlalu panjang atau pendek
            len_penalty = abs(len(code.splitlines()) - 10) 
            score -= len_penalty

        except SyntaxError:
            score = -100 # Penalti berat untuk sintaks yang tidak valid

        self.fitness_cache[code] = score
        return score

    def _select(self, k=2):
        # Seleksi turnamen
        tournament = random.sample(self.population, k=k)
        tournament.sort(key=self._calculate_fitness, reverse=True)
        return tournament[0]

    def _crossover(self, parent1, parent2):
        lines1 = parent1.split('\n')
        lines2 = parent2.split('\n')
        
        if not lines1 or not lines2:
            return parent1, parent2

        point = random.randint(1, min(len(lines1), len(lines2)) -1) if min(len(lines1), len(lines2)) > 1 else 1
        
        child1 = '\n'.join(lines1[:point] + lines2[point:])
        child2 = '\n'.join(lines2[:point] + lines1[point:])
        return child1, child2

    def _mutate(self, code, rate=0.1):
        if random.random() > rate:
            return code

        lines = code.split('\n')
        if not lines:
            return code

        mutation_type = random.choice(['add', 'remove', 'modify'])
        line_idx = random.randint(0, len(lines)-1)

        if mutation_type == 'remove' and len(lines) > 1:
            lines.pop(line_idx)
        elif mutation_type == 'add':
            new_line = random.choice([
                "x = 1", "y = x + 1", "print(\"debug\")", "pass",
                "a, b = b, a" # Contoh mutasi menarik
            ])
            lines.insert(line_idx, new_line)
        elif mutation_type == 'modify':
            lines[line_idx] = lines[line_idx].replace("=", "==").replace("+", "-")
        
        return '\n'.join(lines)

    def evolve(self, generations=10, population_size=20):
        for _ in range(generations):
            new_population = []
            
            # Elitisme: pertahankan 10% terbaik
            elite_count = int(len(self.population) * 0.1)
            sorted_pop = sorted(self.population, key=self._calculate_fitness, reverse=True)
            new_population.extend(sorted_pop[:elite_count])

            while len(new_population) < population_size:
                parent1 = self._select()
                parent2 = self._select()
                
                child1, child2 = self._crossover(parent1, parent2)
                
                child1 = self._mutate(child1)
                child2 = self._mutate(child2)

                new_population.extend([child1, child2])
            
            self.population = new_population

        # Kembalikan individu terbaik dari populasi akhir
        return max(self.population, key=self._calculate_fitness)
