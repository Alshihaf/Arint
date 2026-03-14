#!/usr/bin/env python3
# core/SilentWatcherSuper.py
import os
import sys
import time
import random
import hashlib
import numpy as np
import shutil
import json
import re
import threading
from pathlib import Path
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from core.memory_manager import MemoryManager
from core.awareness import KesadaranLengkap
from core.cot_executive import CoTExecutive
from core.planner import Planner
from core.transformer_arint import TransformerArint

from tools.health import HealthChecker, Severity
from core.coder import Coder
from tools.api_explorer import GitHubExplorer, HuggingFaceExplorer
from tools.intention import Intention
from tools.unified_evolution import UnifiedEvolutionEngine, create_unified_engine
from tools.file_explorer import FileExplorer
from tools.binary_string import BinaryString
from core.reflection import AuditLoop
from core.memory_router import BrainCore
from tools.summarizer import Summarizer
from core.dream import Dreamer
from tools.seafil import Seafil
from tools.cleaners import abstract_knowledge, prioritize_content, fetch_url
from config import load_config
import goal_manager as gm
from neural import AdvancedRNN, AdvancedNLU, MLPClassifier, MathOps
from tools.api_server import run_api_server
from tools.long_term_memory import LongTermMemory

logger = logging.getLogger("Cognition")

class SilentWatcherSuper:
    def __init__(self, config):
        self.config = config
        self.fs = FileExplorer()
        github_token = self.config.get('github_token')
        hf_token = self.config.get('huggingface_token')

        self.advanced_nlu = AdvancedNLU()
        self.mlp = MLPClassifier(layers=[4, 8, 2], lr=0.1)
        self.rnn = AdvancedRNN(input_dim=10, hidden_dim=16, output_dim=10, activation='tanh')
        self.kesadaran = KesadaranLengkap(dimensi=64)

        self.github = GitHubExplorer(token=github_token)
        self.hf = HuggingFaceExplorer(token=hf_token)

        self.goal_manager = gm.GoalManager()
        self.brain = BrainCore()
        self.memory = MemoryManager()

        Path("memory/evolution").mkdir(parents=True, exist_ok=True)
        self.evolver = UnifiedEvolutionEngine()
        logger.info("UnifiedEvolutionEngine initialized.")
        self.audit = AuditLoop()
        self.seafil = Seafil(strict=True)
        self.dreamer = Dreamer()
        self.coder = Coder()
        self.planner = Planner(self.memory, self.goal_manager, None)
        self.current_plan_context = None

        self.summarizer = Summarizer(use_llm=False, llm_tool=None)

        self.needs = config.get("needs_defaults", {}).copy()
        
        self.intention = Intention(
            num_needs=len(self.needs),
            num_actions=11,
            num_inputs=64,
            drift_rate=0.01,
            learning_rate=0.1,
            noise_scale=0.1
        )

        self.health_checker = HealthChecker(
            arint=self,
            config={
                'memory_snippet_limit': 5000,
                'executive_block_rate': 70.0,
                'need_threshold': 95,
                'error_count_limit': 5,
                'check_interval': 60,
                'auto_heal': False,
                'cpu_threshold': 90,
                'memory_threshold': 90,
                'disk_threshold': 90,
                'disk_path': '/storage/emulated/0/',
                'battery_threshold': 20,
                'max_issues_per_cycle': 10,
            }
        )
        self._last_health_check = time.time()
        logger.info("HealthChecker initialized.")

        from core.chain_of_thought import ChainOfThought
        from core.imagination import Imagination
        from core.flock_of_thought import FlockOfThought
        self.cot = ChainOfThought(
            memory_router=None,
            max_depth=4,
            max_iterations=3,
            confidence_threshold=0.6,
            log_path="memory/consciousness/current.log",
            enable_backtrack=True
        )
        self.imagination = Imagination(self.dreamer)
        self.cot_executive = CoTExecutive(self.cot, self)
        self.log("CoT-based executive initialized")

        self.fot = FlockOfThought(self)
        self.log("Flock of Thought (FoT) initialized — semua modul terhubung")

        self.cycle = 0
        self.keywords = ["ai", "autonomy", "hacking", "logic", "optimization", "system", "llm",
                         "how to improve llm", "ChatGPT", "Gemini", "Claude", "DeepSeek",
                         "how to connect with lokal llm", "python3", "c#", "language programming", "c++"]

        self.api_port = config.get('api port', 5000)
        self.api_thread = None
        self.api_lock = threading.Lock()
        self._start_api_server()

        self.last_action_success = True
        self.impulse_count = 0
        self.evolution_success_count = 0

        logger.info("SilentWatcherSuper initialized with all subsystems.")
        logger.info("")

        self.transformer = TransformerArint(config={
            'd_model': 32,
            'num_heads': 2,
            'N': 1,
            'd_ff': 64,
            'vocab_size': 2000,
            'max_seq_len': 30
        })
        self.transformer.load()
        self.transformer.load_tokenizer()

        self.ltm = LongTermMemory()

        self.api_server = None
        if config.get('enable_api', False):
            self.api_lock = threading.Lock()
            self.api_server = threading.Thread(
                target=run_api_server,
                args=(self, config.get('api_port', 8080), self.api_lock),
                daemon=True
            )
            self.api_server.start()
            self.log(f"API server started on port {config.get('api_port', 8080)}")

        if self.brain.snippets:
            self.transformer.fit_tokenizer(self.brain.snippets)
        if self.brain.snippets and len(self.brain.snippets) > 10:
            self.transformer.fit_tokenizer(self.brain.snippets)
            self.log("Tokenizer fitted with existing snippets.")

    def _start_api_server(self):
        try:
            self.api_thread = threading.Thread(
                target=run_api_server,
                args=(self, self.api_port, self.api_lock),
                daemon=True
            )
            self.api_thread.start()
            self.log(f"API server started on port {self.api_port}")
        except Exception as e:
            self.log(f"Failed to start API server: {e}")

    def log(self, msg, level="INFO"):
        GRAY = "\033[90m"
        CYAN = "\033[96m"
        RESET = "\033[0m"
        waktu = time.strftime("%H:%M:%S")
        tanggal = datetime.now().strftime("%Y-%m-%d")
        needs_str = (f"B:{self.needs.get('boredom',0)} "
                     f"F:{self.needs.get('fatigue',0)} "
                     f"H:{self.needs.get('hunger_data',0)} "
                     f"M:{self.needs.get('messiness',0)}")
        print(f"{GRAY}[ {waktu} ] [ {tanggal} ] [ {needs_str} ]{RESET}")
        print(f"{CYAN}Arint > {msg}{RESET}\n")
        log_path = Path("memory/consciousness/current.log")
        with open(log_path, 'a') as f:
            f.write(f"[{waktu}] [{tanggal}] [{needs_str}]\n")
            f.write(f"Arint > {msg}\n\n")

    def _perceive(self):
        sources = [
            "https://en.wikipedia.org/wiki/Special:Random",
            "https://news.ycombinator.com",
            "https://google.com",
            "https://duckduckgo.com",
            "https://huggingface.co/",
            "https://github.com/",
            "https://id.wikihow.com",
            "https://medium.com/@firozkaif27/step-by-step-guide-to-building-your-own-large-language-model-llm-d09be610b6db",
            "github.com/public-apis/public-apis",
            "freecodecamp.org/news",
            "docs.python.org",
            "devdocs.io",
            "github.com/sindresorhus/awesome",
            "ourworldindata.org",
            "sciencedaily.com",
            "images.nasa.gov",
            "ncbi.nlm.nih.gov/pmc/",
            "archive.org"
        ]
        target = random.choice(sources)
        self.log(f"Perceiving source: {target}")
        raw_data = fetch_url(target)
        if "Error" not in raw_data:
            filtered = self.seafil.process(raw_data, source=target)
            if filtered:
                abstracts = abstract_knowledge(filtered.content)
                for abs_ in abstracts:
                    self.brain.add_snippet(abs_, source=target)
                    self.memory.semantic.add_fact(
                        f"insight_{hashlib.md5(abs_.encode()).hexdigest()[:8]}",
                        abs_, source=target, confidence=0.6
                    )
                strategic = prioritize_content(abstracts, self.keywords)
                for item in strategic:
                    summary = self.summarizer.summarize(item, source=target,
                                                        title=f"Insight from {target}")
                    if summary:
                        self.memory.episodic.add({
                            "type": "perception",
                            "source": target,
                            "summary": summary,
                            "timestamp": time.time()
                        })
                return strategic
        return []

    def _explore_fs(self) -> str:
        self.log("=" * 60)
        self.log("EXPLORE_FS: Exploring filesystem with all FileExplorer features")
        mode = random.choice([
            "read_text", "read_binary", "list_dir", "search_files",
            "get_info", "get_hash", "disk_usage", "find_by_name",
            "read_python", "read_config", "read_logs", "experiment"
        ])
        self.log(f"Exploration mode: {mode}")
        try:
            result = f"Explored filesystem with mode {mode}"
            self.needs["hunger_data"] = max(0, self.needs["hunger_data"] - 35)
            self.audit.record("EXPLORE_FS", impact=1)
            self.memory.episodic.add({"type": "explore_fs", "mode": mode, "result": result})
        except Exception as e:
            self.log(f"Error in EXPLORE_FS: {e}")
            self.needs["hunger_data"] += 10
            result = f"Failed {mode}"
        self.brain.consolidate()
        self.log("EXPLORE_FS finished")
        self.log("=" * 60)
        return result

    def _explore_github(self) -> str:
        self.log("Exploring GitHub...")
        try:
            repos = self.github.trending_repos(language="python", limit=5)
            if repos:
                for repo in repos:
                    desc = f"[GitHub] {repo['name']}: {repo['description']} (⭐ {repo['stars']})"
                    self.brain.add_snippet(desc, source="github:trending")
                    self.memory.semantic.add_fact(f"github_{repo['name']}", desc, source="github")
                    if random.random() < 0.3:
                        owner, repo_name = repo['name'].split('/')
                        readme = self.github.repo_readme(owner, repo_name)
                        if readme:
                            self.brain.add_snippet(readme[:2000], source=f"github:readme:{repo['name']}")
                self.needs["hunger_data"] = max(0, self.needs["hunger_data"] - 50)
                self.audit.record("EXPLORE_GITHUB", impact=len(repos))
                result = f"Found {len(repos)} repositories"
            else:
                self.log("No repositories found.")
                self.needs["hunger_data"] += 5
                result = "No repositories"
        except Exception as e:
            self.log(f"Error in EXPLORE_GITHUB: {e}")
            self.needs["hunger_data"] += 10
            result = "GitHub exploration failed"
        return result

    def _explore_hf(self) -> str:
        self.log("Exploring Hugging Face...")
        try:
            models = self.hf.trending_models(limit=5)
            if models:
                for model in models:
                    desc = f"[HuggingFace] {model['id']} ({model['pipeline_tag']}) - ⭐ {model['likes']} ⬇️ {model['downloads']}"
                    self.brain.add_snippet(desc, source="hf:trending_models")
                    self.memory.semantic.add_fact(f"hf_{model['id']}", desc, source="huggingface")
                    if random.random() < 0.2:
                        card = self.hf.model_card(model['id'])
                        if card:
                            self.brain.add_snippet(card[:2000], source=f"hf:model_card:{model['id']}")
                self.needs["hunger_data"] = max(0, self.needs["hunger_data"] - 45)
                self.audit.record("EXPLORE_HF", impact=len(models))
                result = f"Found {len(models)} models"
            else:
                datasets = self.hf.trending_datasets(limit=5)
                if datasets:
                    for ds in datasets:
                        desc = f"[HuggingFace Dataset] {ds['id']} - ⭐ {ds['likes']} ⬇️ {ds['downloads']}"
                        self.brain.add_snippet(desc, source="hf:trending_datasets")
                    self.needs["hunger_data"] = max(0, self.needs["hunger_data"] - 40)
                    self.audit.record("EXPLORE_HF", impact=len(datasets))
                    result = f"Found {len(datasets)} datasets"
                else:
                    self.log("No data from Hugging Face.")
                    self.needs["hunger_data"] += 5
                    result = "No Hugging Face data"
        except Exception as e:
            self.log(f"Error in EXPLORE_HF: {e}")
            self.needs["hunger_data"] += 10
            result = "Hugging Face exploration failed"
        return result

    def _train_rnn_on_snippets(self):
        if len(self.brain.snippets) < 3:
            self.log("Not enough snippets to train RNN.")
            return
        recent = self.brain.snippets[-3:]
        vocab = set()
        for s in recent:
            words = re.findall(r'\w+', s.lower())
            vocab.update(words)
        if not vocab:
            self.log("No words found in snippets.")
            return
        word_to_idx = {w: i for i, w in enumerate(vocab)}
        vocab_size = len(vocab)
        if self.rnn.input_dim != vocab_size:
            self.log(f"RNN input_dim mismatch: expected {self.rnn.input_dim}, got {vocab_size}. Skipping.")
            return
        inputs = []
        target_indices = []
        for s in recent:
            words = re.findall(r'\w+', s.lower())
            if not words:
                continue
            first_word = words[0]
            if first_word not in word_to_idx:
                continue
            vec = [0.0] * vocab_size
            vec[word_to_idx[first_word]] = 1.0
            inputs.append(vec)
            last_word = words[-1] if len(words) > 1 else words[0]
            if last_word in word_to_idx:
                target_indices.append(word_to_idx[last_word])
            else:
                target_indices.append(random.randint(0, vocab_size-1))
        if len(inputs) < 2:
            self.log("Insufficient valid inputs.")
            return
        try:
            outputs, _, cache = self.rnn.forward_sequence(inputs)
            d_outputs = []
            loss_total = 0.0
            for t, logits in enumerate(outputs):
                if t < len(target_indices):
                    grad = MathOps.cross_entropy_grad(logits, target_indices[t])
                    d_outputs.append(grad)
                    probs = MathOps.softmax(logits)
                    loss_total += MathOps.cross_entropy_loss(probs, target_indices[t])
            self.rnn.backward_sequence(cache, d_outputs, lr=0.01)
            self.log(f"RNN training step completed. Loss: {loss_total:.4f}")
        except Exception as e:
            self.log(f"RNN training error: {e}")

    def mischief(self):
        files = list(Path("memory").rglob("*.txt"))
        if files:
            victim = random.choice(files)
            new_name = victim.with_name(victim.stem + "_backup" + victim.suffix)
            shutil.copy(victim, new_name)
            with open(victim, "a") as f:
                f.write("\n# AI was here.\n")
            self.log(f"Mischief on {victim}")

    def self_reflect(self):
        func_count = self.evolution_success_count
        insight_count = len(self.brain.insights)
        status = "developing" if func_count > 10 else "stagnant"
        log_entry = f"I now have {func_count} evolved functions and {insight_count} insights. I am {status}."
        with open("memory/reflection.log", "a") as f:
            f.write(log_entry + "\n")
        self.log(log_entry)
        self.memory.reflective.add_reflection({
            "type": "self_reflection",
            "log": log_entry,
            "timestamp": time.time()
        })

    def reflect_on_goals(self):
        explore_success = sum(1 for e in self.audit.logbook if e['action'] == 'EXPLORE' and e.get('success', False))
        evolve_success = sum(1 for e in self.audit.logbook if e['action'] == 'EVOLVE' and e.get('success', False))
        total_actions = len(self.audit.logbook)
        if total_actions > 0:
            progress = (explore_success * 0.3 + evolve_success * 0.7) / (total_actions * 0.5)
            self.goal_manager.set_primary_progress(min(1.0, progress))
        if self.needs["boredom"] > 70 and self.brain.insights and random.random() < 0.1:
            insight = random.choice(self.brain.insights)
            new_subgoal = f"Learn more about: {insight}"
            self.goal_manager.add_subgoal(new_subgoal, reason="Boredom triggered")
            self.log(f"New subgoal added: {new_subgoal}")
        success_rate = self.audit.get_wisdom()
        if "Success Rate:" in success_rate:
            try:
                rate = float(success_rate.split()[2])
                self.goal_manager.adjust_primary_confidence((rate - 0.5) * 0.1)
            except:
                pass
        self.goal_manager.save()
        if self.brain.insights and random.random() < 0.05:
            insight = random.choice(self.brain.insights)
            new_goal = f"Explore deeper: {insight[:50]}..."
            from . import sws_logic
            approved, score = sws_logic._goal_firewall(self, new_goal, f"Insight from reasoning: {insight}")
            if approved:
                self.goal_manager.update_primary_description(
                    new_goal,
                    f"Insight passed firewall (score {score:.2f})",
                    from_ai=True,
                    context={"insights": self.brain.insights}
                )
                self.log(f"Goal changed via firewall: {new_goal}")
            else:
                self.log(f"Goal change rejected by firewall (score {score:.2f})")
                
    def _process_evolution_goal(self, goal_index: int):
        try:
            self.evolver.process_goal(self.goal_manager, goal_index)
        except Exception as e:
            self.log(f"Error processing evolution goal: {e}")

    def save_state(self):
        state = {
            "cycle": self.cycle,
            "needs": self.needs,
            "brain_snippets": self.brain.snippets,
            "brain_insights": self.brain.insights,
            "brain_patterns": self.brain.patterns,
            "audit_log": self.audit.logbook,
            "keywords": self.keywords,
            "evolution_success_count": self.evolution_success_count,
        }
        try:
            with open("memory/system_state.json", "w") as f:
                json.dump(state, f, indent=2)
            self.transformer.save()
            self.transformer.save_tokenizer()
            self.log("Transformer state saved...")
            self.log("State saved to memory/system_state.json")
        except Exception as e:
            self.log(f"Failed to save state: {e}")

    def load_state(self):
        state_path = Path("memory/system_state.json")
        if state_path.exists():
            try:
                with open(state_path, "r") as f:
                    state = json.load(f)
                self.cycle = state.get("cycle", 0)
                self.needs.update(state.get("needs", {}))
                self.brain.snippets = state.get("brain_snippets", [])
                self.brain.insights = state.get("brain_insights", [])
                self.brain.patterns = state.get("brain_patterns", [])
                self.audit.logbook = state.get("audit_log", [])
                self.keywords = state.get("keywords", self.keywords)
                self.transformer.load_tokenizer()
                self.evolution_success_count = state.get("evolution_success_count", 0)
                self.transformer.load()
                self.transformer.load_tokenizer
                self.log("Transformer state loaded...")
                self.log("State loaded from memory/system_state.json")
            except Exception as e:
                self.log(f"Failed to load state: {e}")

    def _get_plan_action(self) -> Tuple[Optional[str], Optional[Dict]]:
        result = self.planner.suggest_action_from_plans()
        if result:
            action, context = result
            approved, reason, _ = self.cot_executive.evaluate_action(action, self.needs, context)
            if approved:
                return action, context
            else:
                self.log(f"Plan action {action} blocked by executive: {reason}")
        return None, None
        
    def _execute_generate_binary_output(self):
        generated_dir = "memory/generated"
        os.makedirs(generated_dir, exist_ok=True)
        files = sorted([os.path.join(generated_dir, f) for f in os.listdir(generated_dir) if f.startswith("arint_binary_")], key=os.path.getctime)
        max_files = 20
        if len(files) >= max_files:
            for old_file in files[:len(files)-max_files+1]:
                try:
                    os.remove(old_file)
                    self.log(f"Removed old generated file: {old_file}")
                except:
                    pass

        formats = ['py', 'json', 'md', 'html', 'txt']
        target_format = random.choice(formats)
 
        if self.brain.insights:
            base_insight = random.choice(self.brain.insights)
        else:
            base_insight = "Arint is expressing himself"

        variations = [
            base_insight,
            f"{base_insight} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"{base_insight} (v{random.randint(1,99)})",
            base_insight.upper(),
            base_insight.lower(),
            base_insight + " " + random.choice(["✨", "🚀", "🧠", "💡", "🔥"])
        ] 
        insight = random.choice(variations)

        if len(insight) > 100:
            insight = insight[:100] + "..."

        binary_str = BinaryString.encode(insight)

        content = BinaryString.to_format(binary_str, target_format)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"arint_binary_{timestamp}.{target_format}"
        filepath = os.path.join(generated_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        self.brain.add_snippet(f"Generated {target_format} from binary: {filepath}", source="self_generate")
        self.memory.semantic.add_fact(
            f"binary_output_{int(time.time())}",
            {
                "format": target_format,
                "path": filepath,
                "insight": insight,
                "binary": binary_str
            },
            source="binary_generator",
            confidence=0.9
        )

        self.log(f"Generated {target_format} output from binary string: {filepath}")
        return f"Generated {target_format} file"
        
    def _get_stimulus_vector(self):
        vec = np.zeros(64)
        vec[0] = self.needs.get("hunger_data", 50) / 100.0
        vec[1] = self.needs.get("boredom", 50) / 100.0
        vec[2] = self.needs.get("messiness", 50) / 100.0
        vec[3] = self.needs.get("fatigue", 50) / 100.0
        vec[4] = len(self.brain.insights) / 100.0
        vec[5] = len(self.brain.snippets) / 500.0
        vec += np.random.randn(64) * 0.05
        return vec
        
    def _get_intention_input(self):
        if hasattr(self, 'kesadaran'):
           state = self.kesadaran.state_internal.copy()
        else:
            state = np.zeros(64)

        needs_vec = np.array([
            self.needs.get("hunger_data", 50) / 100.0,
            self.needs.get("boredom", 50) / 100.0,
            self.needs.get("messiness", 50) / 100.0,
            self.needs.get("fatigue", 50) / 100.0
        ])

        if len(state) >= 60:
            combined = np.concatenate([state[:60], needs_vec])
        else:
            combined = np.concatenate([state, needs_vec, np.zeros(64 - len(state) - 4)])
        return combined[:64]

    def _get_decision_context(self):
        return {
            'hunger': round(self.needs['hunger_data'] / 10) * 10,
            'boredom': round(self.needs['boredom'] / 10) * 10,
            'dopamin': round(self.kesadaran.tingkat_dopamin * 2) / 2
        }

    def _ltm_debug(self):
        if not hasattr(self, 'ltm') or self.ltm is None:
            self.log("[LTM] LTM not initialized!")
            return
        
        learned_actions = self.ltm.get_all_learned_actions()
        if not learned_actions:
            self.log("[LTM] No actions learned yet (cold start)")
            return
        
        self.log(f"[LTM] Learned actions: {learned_actions}")

        for action in ["EXPLORE", "EVOLVE", "ORGANIZE"]:
            stats = self.ltm.get_action_stats(action, limit=3)
            if stats:
                self.log(f"[LTM]   {action}:")
                for s in stats:
                    ctx = s['context']
                    rate = s['success_rate']
                    count = s['sample_count']
                    self.log(f"[LTM]     Context: {ctx} → Rate: {rate:.2f} (n={count})")

from .run_cycle import run_cycle
SilentWatcherSuper.run_cycle = run_cycle
