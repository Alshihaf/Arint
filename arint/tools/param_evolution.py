import random
from tools.unified_evolution import UnifiedEvolutionEngine, EvolutionConfig, CodeGene

class ParameterOptimizer:
    def __init__(self, arint):
        self.arint = arint
        self.config = EvolutionConfig(
            population_size=20,
            generations=30,
            mutation_rate=0.2,
            crossover_rate=0.7,
            weight_correctness=10.0,
            weight_speed=0.0,
            weight_memory=0.0,
            weight_simplicity=0.1
        )
        self.engine = UnifiedEvolutionEngine(config=self.config)

    def create_param_genome(self, params):
        genes = []
        for name, value in params.items():
            genes.append(CodeGene(
                id=f"param_{name}",
                template=f"    {name} = {value}\n",
                arity=0,
                complexity=1.0,
                description=f"Parameter {name}"
            ))
        return genes

    def evaluate_params(self, genome, test_cycles=100):
        params = {}
        for gene in genome.genes:
            if gene.id.startswith("param_"):
                name = gene.id[6:]
                value = float(gene.template.split('=')[1].strip())
                params[name] = value
        original = {name: getattr(self.arint, name, None) for name in params}
        for name, value in params.items():
            setattr(self.arint, name, value)
        total_reward = 0
        for _ in range(test_cycles):
            self.arint.run_cycle()
            total_reward += self.arint.last_reward

        for name, value in original.items():
            if value is not None:
                setattr(self.arint, name, value)
        return total_reward / test_cycles