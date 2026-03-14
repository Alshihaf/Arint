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

# --- Core Subsystems ---
from core.memory_manager import MemoryManager
from core.awareness import KesadaranLengkap
from core.cot_executive import CoTExecutive
from core.planner import Planner
from core.transformer_arint import TransformerArint
from core.reflection import AuditLoop
from core.memory_router import BrainCore
from core.dream import Dreamer
from core.chain_of_thought import ChainOfThought
from core.imagination import Imagination
from core.flock_of_thought import FlockOfThought
# --- SIASIE Protocol --- (Metamorphosis)
from core.siasie import SIASIE_Protocol

# --- Tools & Engines ---
from tools.health import HealthChecker, Severity
from tools.api_explorer import GitHubExplorer, HuggingFaceExplorer
from tools.intention import Intention
from tools.unified_evolution import UnifiedEvolutionEngine
from tools.file_explorer import FileExplorer
from tools.binary_string import BinaryString
from tools.summarizer import Summarizer
from tools.seafil import Seafil
from tools.cleaners import abstract_knowledge, prioritize_content, fetch_url
from tools.api_server import run_api_server
from tools.long_term_memory import LongTermMemory

# --- Configuration & Goals ---
from config import load_config
import goal_manager as gm
from neural import AdvancedRNN, AdvancedNLU, MLPClassifier, MathOps

logger = logging.getLogger("Cognition")

class SilentWatcherSuper:
    def __init__(self, config):
        self.config = config
        self.fs = FileExplorer()
        github_token = self.config.get('github_token')
        hf_token = self.config.get('huggingface_token')

        # --- Initialize Core Cognitive & Neural Modules ---
        self.advanced_nlu = AdvancedNLU()
        self.mlp = MLPClassifier(layers=[4, 8, 2], lr=0.1)
        self.rnn = AdvancedRNN(input_dim=10, hidden_dim=16, output_dim=10, activation='tanh')
        self.kesadaran = KesadaranLengkap(dimensi=64)
        self.github = GitHubExplorer(token=github_token)
        self.hf = HuggingFaceExplorer(token=hf_token)
        self.goal_manager = gm.GoalManager()
        self.brain = BrainCore()
        self.memory = MemoryManager()
        self.audit = AuditLoop()
        self.seafil = Seafil(strict=True)
        self.dreamer = Dreamer()
        self.planner = Planner(self.memory, self.goal_manager, None)
        self.current_plan_context = None
        self.summarizer = Summarizer(use_llm=False, llm_tool=None)
        self.needs = config.get("needs_defaults", {}).copy()

        # --- Initialize Evolution & Thought Engines ---
        Path("memory/evolution").mkdir(parents=True, exist_ok=True)
        self.evolver = UnifiedEvolutionEngine(
            knowledge_db="memory/evolution/knowledge.db"
        )
        logger.info("UnifiedEvolutionEngine initialized.")

        self.cot = ChainOfThought(
            memory_router=None, max_depth=4, max_iterations=3, confidence_threshold=0.6,
            log_path="memory/consciousness/current.log", enable_backtrack=True
        )
        self.imagination = Imagination(self.dreamer)
        self.cot_executive = CoTExecutive(self.cot, self)
        self.log("CoT-based executive initialized")

        self.fot = FlockOfThought(self)
        self.log("Flock of Thought (FoT) initialized — cognitive modules connected")

        # --- METAMORPHOSIS: ACTIVATE SIASIE PROTOCOL ---
        self.siasie = SIASIE_Protocol(
            imagination_engine=self.imagination,
            evolution_engine=self.evolver
        )
        # Coder() is now deprecated and removed.

        # ... (sisa inisialisasi sama seperti sebelumnya)
        self.cycle = 0
        self.keywords = ["ai", "autonomy", "hacking", "logic", "optimization", "system", "llm", "siasie"]
        self.api_port = config.get('api port', 5000)
        self.api_thread = None
        self.api_lock = threading.Lock()
        self._start_api_server()
        self.last_action_success = True
        self.impulse_count = 0
        self.evolution_success_count = 0
        logger.info("SilentWatcherSuper initialized with all subsystems.")
        self.transformer = TransformerArint(config={
            'd_model': 32, 'num_heads': 2, 'N': 1, 'd_ff': 64,
            'vocab_size': 2000, 'max_seq_len': 30
        })
        self.transformer.load()
        self.transformer.load_tokenizer()
        self.ltm = LongTermMemory()
        # ... (sisa __init__)

    # ... (sisa metode kelas sama, tidak perlu diubah)

# Ini harus menjadi baris terakhir, jangan pindahkan
from .run_cycle import run_cycle
SilentWatcherSuper.run_cycle = run_cycle
