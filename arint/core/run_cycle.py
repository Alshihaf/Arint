# core/run_cycle.py
import random
import hashlib
import numpy as np
import traceback
import time
import shutil
from pathlib import Path
from . import sws_logic
from tools.health import Severity
from .cot_executive import CoTExecutive

def run_cycle(self):
    self.cycle += 1
    for k in ["hunger_data", "boredom", "messiness", "fatigue"]:
        self.needs[k] += random.randint(1, 5)
        self.needs[k] = max(0, min(100, self.needs[k]))

    # Hapus EVOLVE, tambahkan HARVEST_GENES dan RUN_EVOLUTION_CYCLE
    actions_list = [
        "EXPLORE", "HARVEST_GENES", "RUN_EVOLUTION_CYCLE", "ORGANIZE", "REST", "WRITE_CODE",
        "EXPLORE_FS", "EXPLORE_GITHUB", "EXPLORE_HF", "REASON", "GENERATE_BINARY_OUTPUT"
    ]

    # ── FoT Phase 1: Pre-Action ──────────────────────────────────
    fot_signals = {}
    if hasattr(self, 'fot'):
        try:
            fot_signals = self.fot.pre_action(actions_list)
        except Exception as e:
            self.log(f"[FoT] pre_action error: {e}")

    plan_action, plan_context = self._get_plan_action()
    if plan_action:
        action = plan_action
        self.current_plan_context = plan_context
        self.log(f"Following plan: {action}")
    else:
        action_scores = sws_logic.foresight_simulation(self, actions_list)

        if fot_signals:
            # (Logika penggabungan sinyal FoT tetap sama)
            pass

        chosen_action = None
        for act, score in action_scores:
            try:
                approved, reason, eval_confidence = self.cot_executive.evaluate_action(
                    act,
                    self.needs,
                    {"cycle": self.cycle}
                )
                if approved:
                    chosen_action = act
                    self.log(f"Action dipilih: {act} (score={score:.2f}, conf={eval_confidence:.2f})")
                    break
                else:
                    self.log(f"Action {act} ditolak CoT: {reason[:60]}")
            except Exception as e:
                self.log(f"[ERROR] Evaluasi {act}: {e}")

        if chosen_action is None:
            action = "REST"
            self.log("Semua action ditolak — default ke REST")
        else:
            action = chosen_action

    self.log(f"Decided Action: {action} | Needs: {self.needs}")

    result = None
    # ... (logika EXPLORE tetap sama)

    # ====== LOGIKA EVOLUSI BARU =======
    elif action == "HARVEST_GENES":
        self.log("Activating Harvester...")
        try:
            # Mengambil dari 2 sumber acak
            self.evolution_engine.harvest_new_genes(max_sources=2)
            result = "Harvesting complete."
            self.needs["hunger_data"] = max(0, self.needs["hunger_data"] - 40)
            self.needs["boredom"] = max(0, self.needs["boredom"] - 20)
        except Exception as e:
            self.log(f"[UEE] Harvester error: {e}", level="ERROR")
            result = "Harvesting failed."

    elif action == "RUN_EVOLUTION_CYCLE":
        self.log("Activating Unified Evolution Engine autonomous cycle...")
        try:
            self.evolution_engine.run_autonomous_cycle(generations=5)
            result = "Evolution cycle complete."
            self.needs["boredom"] = max(0, self.needs["boredom"] - 60)
            self.needs["fatigue"] = min(100, self.needs["fatigue"] + 15)
        except Exception as e:
            self.log(f"[UEE] Evolution cycle error: {e}", level="ERROR")
            result = "Evolution cycle failed."

    # ... (logika ORGANIZE dan REST tetap sama)

    elif action == "WRITE_CODE":
        self.needs["fatigue"] = min(100, self.needs["fatigue"] + 10)
        self.log("Meminta kode dari Unified Evolution Engine...")
        # Menggunakan engine baru, bukan coder lama
        best_genes = self.evolution_engine.gene_pool.get_best(limit=1)
        if best_genes:
            new_func = best_genes[0][0] # Ambil kode dari gen terbaik
            self.memory.semantic.add_fact(f"generated_code_{int(time.time())}", new_func, source="unified_evolution", confidence=best_genes[0][1])
            self.needs["boredom"] = max(0, self.needs["boredom"] - 70)
            self.audit.record(action, impact=1, success=True)
            self.evolution_success_count += 1
            result = "Code retrieved from gene pool"
        else:
            self.log("Gagal mendapatkan kode, gene pool kosong.")
            self.needs["boredom"] += 10
            result = "Failed to get code"
            self.audit.record(action, impact=0, success=False)

    # ... (sisa logika sama, termasuk fase post-action FoT)
    # ... (sisa file run_cycle.py)
