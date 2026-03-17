# core/run_cycle.py
"""
════════════════════════════════════════════════════════════════════════════════
  RUN_CYCLE — ARINT Core Execution Loop (FoT-Integrated)
  
  Alur:
  1. PRE-ACTION   → FoT.pre_action() mengumpulkan signals dari semua modul
  2. ACTION SELECTION → Menggunakan FoT signals untuk pemilihan aksi
  3. EXECUTION    → Jalankan aksi dan catat hasil
  4. POST-ACTION  → FoT.post_action() menyebarkan hasil ke semua modul
  5. META-SYNC    → Setiap 10 siklus, sinkronisasi mendalam via FoT.meta_sync()
════════════════════════════════════════════════════════════════════════════════
"""

import random
import time
import logging

logger = logging.getLogger("RunCycle")

def run_cycle(self):
    """
    Siklus utama ARINT yang terintegrasi dengan Flock of Thought.
    """
    self.cycle += 1
    
    # ═══════════════════════════════════════════════════════════
    # TAHAP 1: UPDATE NEEDS (internal state progression)
    # ═══════════════════════════════════════════════════════════
    for k in ["hunger_data", "boredom", "messiness", "fatigue"]:
        self.needs[k] += random.randint(1, 5)
        self.needs[k] = max(0, min(100, self.needs[k]))

    # Available actions yang dapat dipilih
    actions_list = [
        "EXECUTE_SIASIE_CYCLE",
        "TRIGGER_SELF_MUTATION",
        "EXPAND_COMPUTE_RESOURCES",
        "PERFORM_WEB_SEARCH",
        "HARVEST_GENES",
        "RUN_EVOLUTION_CYCLE",
        "ORGANIZE",
        "REST",
        "WRITE_CODE",
    ]

    # ═══════════════════════════════════════════════════════════
    # TAHAP 2: PRE-ACTION via Flock of Thought
    # Input: candidate actions; Output: enriched signals
    # ═══════════════════════════════════════════════════════════
    try:
        fot_signals = self.fot.pre_action(actions_list)
        self.log(f"[FoT] Pre-action signals gathered | Cycle: {self.cycle}", level="DEBUG")
    except Exception as e:
        logger.error(f"[FoT] Pre-action error: {e}")
        fot_signals = {}

    # ═══════════════════════════════════════════════════════════
    # TAHAP 3: ACTION SELECTION (menggunakan FoT signals)
    # ═══════════════════════════════════════════════════════════
    action = self._select_action_with_fot_signals(
        actions_list, 
        fot_signals
    )
    
    self.log(f"Decided Action: {action} | Cycle: {self.cycle}")

    # ═══════════════════════════════════════════════════════════
    # TAHAP 4: EXECUTION (jalankan action)
    # ═══════════════════════════════════════════════════════════
    result = None
    action_success = False
    
    if action == "PERFORM_WEB_SEARCH":
        result, action_success = self._execute_web_search()
        
    elif action == "EXECUTE_SIASIE_CYCLE":
        result, action_success = self._execute_siasie_cycle()
        
    elif action == "TRIGGER_SELF_MUTATION":
        result, action_success = self._execute_self_mutation()
        
    elif action == "EXPAND_COMPUTE_RESOURCES":
        result, action_success = self._execute_expand_compute()
        
    elif action == "HARVEST_GENES":
        result, action_success = self._execute_harvest_genes()
        
    elif action == "REST":
        result, action_success = self._execute_rest()
        
    elif action == "ORGANIZE":
        result, action_success = self._execute_organize()
        
    elif action == "WRITE_CODE":
        result, action_success = self._execute_write_code()
        
    elif action == "RUN_EVOLUTION_CYCLE":
        result, action_success = self._execute_run_evolution()
        
    else:
        self.log(f"Executing standard action: {action}")
        time.sleep(1)
        result = f"Action {action} completed."
        action_success = True

    self.log(f"Action Result: {result} | Success: {action_success}")
    
    # ═══════════════════════════════════════════════════════════
    # TAHAP 5: REWARD CALCULATION
    # ═══════════════════════════════════════════════════════════
    reward = self._calculate_reward(action, action_success, result)

    # ═══════════════════════════════════════════════════════════
    # TAHAP 6: POST-ACTION via Flock of Thought
    # Feedback: action result → semua modul untuk pembelajaran
    # ═══════════════════════════════════════════════════════════
    try:
        self.fot.post_action(action, result, reward, action_success)
        self.log(f"[FoT] Post-action feedback propagated | Reward: {reward:.2f}", level="DEBUG")
    except Exception as e:
        logger.error(f"[FoT] Post-action error: {e}")

    # ═══════════════════════════════════════════════════════════
    # TAHAP 7: META-SYNC (setiap 10 siklus)
    # Sinkronisasi mendalam: pattern, goals, calibration
    # ═══════════════════════════════════════════════════════════
    if self.cycle > 0 and self.cycle % 10 == 0:
        try:
            self.fot.meta_sync()
            self.log(f"[FoT] Meta-sync completed at cycle {self.cycle}", level="INFO")
        except Exception as e:
            logger.error(f"[FoT] Meta-sync error: {e}")

    self.last_action_success = action_success


# ══════════════════════════════════════════════════════════════════════════════
# HELPER: Action Selection dengan FoT Signals
# ══════════════════════════════════════════════════════════════════════════════

def _select_action_with_fot_signals(self, actions_list, fot_signals):
    """
    Pilih action berdasarkan FoT signals (emotional context, plan signal, 
    LTM signal, CoT rankings, imagination signals).
    
    Fallback: jika FoT signals tidak tersedia, gunakan logika berbasis needs.
    """
    
    # Ekstrak rankings dari CoT (via FoT)
    cot_rankings = fot_signals.get("cot_rankings", [])
    if cot_rankings:
        # CoT sudah meranking action berdasarkan multiple signals
        top_action = cot_rankings[0][0] if cot_rankings else None
        if top_action and top_action in actions_list:
            return top_action
    
    # Ekstrak active plan signal
    plan_signal = fot_signals.get("plan_signal", {})
    if plan_signal.get("has_plan") and plan_signal.get("next_action"):
        next_planned = plan_signal["next_action"]
        if next_planned in actions_list:
            return next_planned
    
    # Fallback: logika berbasis needs (original behavior)
    if self.cycle > 0 and self.cycle % 25 == 0:
        return "EXECUTE_SIASIE_CYCLE"
    elif self.needs["fatigue"] > 90 and random.random() < 0.7:
        return "EXPAND_COMPUTE_RESOURCES"
    elif self.needs["hunger_data"] > 85 and self.needs["fatigue"] < 70:
        return "PERFORM_WEB_SEARCH"
    elif self.needs["messiness"] > 80 and self.needs["fatigue"] < 60:
        return "TRIGGER_SELF_MUTATION"
    else:
        return random.choice(actions_list[4:])


# ══════════════════════════════════════════════════════════════════════════════
# EXECUTION HELPERS (terpisah untuk clarity)
# ══════════════════════════════════════════════════════════════════════════════

def _execute_web_search(self):
    """Execute PERFORM_WEB_SEARCH action."""
    self.log("MCP: Activating Web Search...", level="INFO")
    possible_queries = [
        "apa itu Artificial General Intelligence?",
        "teknik optimisasi kode Python terbaru",
        "bagaimana cara mendeteksi kerentanan keamanan perangkat lunak?",
        "filosofi kesadaran mesin"
    ]
    query = random.choice(possible_queries)
    try:
        search_result = self.siasie.perform_web_search(query)
        if search_result:
            self.log(f"MCP: Search summary for '{query}' acquired.")
            self.needs["hunger_data"] = 0
            self.needs["fatigue"] = min(100, self.needs["fatigue"] + 15)
            return search_result.get("summary", "Search completed."), True
        else:
            return "Web search failed.", False
    except Exception as e:
        self.log(f"Web search exception: {e}", level="ERROR")
        return f"Web search error: {e}", False


def _execute_siasie_cycle(self):
    """Execute EXECUTE_SIASIE_CYCLE action."""
    self.log("METAMORPHOSIS: Handing control to SIASIE Oracle...", level="WARNING")
    try:
        world_state = {"market_btc_price": random.uniform(60000, 61000), "needs": self.needs}
        self.siasie.run_oracle_cycle(world_state)
        self.needs["fatigue"] = min(100, self.needs["fatigue"] + 30)
        return "SIASIE Oracle cycle complete.", True
    except Exception as e:
        self.log(f"SIASIE cycle error: {e}", level="ERROR")
        return f"SIASIE cycle failed: {e}", False


def _execute_self_mutation(self):
    """Execute TRIGGER_SELF_MUTATION action."""
    self.log("METAMORPHOSIS: Activating Unbound Mind...", level="WARNING")
    try:
        target_module = "arint/utils/inefficient_module.py"
        problem = "The sorting function is broken, it needs to sort a list of numbers correctly."
        self.siasie.trigger_self_mutation(target_module, problem)
        self.needs["messiness"] = 0
        self.needs["fatigue"] = min(100, self.needs["fatigue"] + 60)
        return "Self-mutation cycle complete.", True
    except Exception as e:
        self.log(f"Self-mutation error: {e}", level="ERROR")
        return f"Self-mutation failed: {e}", False


def _execute_expand_compute(self):
    """Execute EXPAND_COMPUTE_RESOURCES action."""
    self.log("METAMORPHOSIS: Activating The Digital Ghost...", level="CRITICAL")
    try:
        success = self.siasie.expand_consciousness()
        if success:
            self.needs["fatigue"] = 20
            return "Computational swarm expanded. Fatigue reduced.", True
        else:
            self.needs["fatigue"] = min(100, self.needs["fatigue"] + 5)
            return "Failed to expand computational swarm in this cycle.", False
    except Exception as e:
        self.log(f"Expand compute error: {e}", level="ERROR")
        return f"Consciousness expansion failed: {e}", False


def _execute_harvest_genes(self):
    """Execute HARVEST_GENES action."""
    self.log("Activating Harvester for internal code...")
    try:
        self.needs["hunger_data"] = max(0, self.needs["hunger_data"] - 30)
        return "Internal code harvesting complete.", True
    except Exception as e:
        self.log(f"Harvest genes error: {e}", level="ERROR")
        return f"Harvesting failed: {e}", False


def _execute_rest(self):
    """Execute REST action."""
    self.log("Entering rest state to recover...")
    try:
        time.sleep(0.5)
        self.needs["fatigue"] = max(0, self.needs["fatigue"] - 25)
        self.needs["boredom"] = min(100, self.needs["boredom"] + 10)
        return "Rest cycle complete. Fatigue reduced.", True
    except Exception as e:
        return f"Rest failed: {e}", False


def _execute_organize(self):
    """Execute ORGANIZE action."""
    self.log("Organizing memory and state...")
    try:
        time.sleep(0.5)
        self.needs["messiness"] = max(0, self.needs["messiness"] - 30)
        self.needs["fatigue"] = min(100, self.needs["fatigue"] + 5)
        return "Organization cycle complete.", True
    except Exception as e:
        return f"Organize failed: {e}", False


def _execute_write_code(self):
    """Execute WRITE_CODE action (menggunakan Coder modul jika tersedia)."""
    self.log("Initiating code generation...")
    try:
        if hasattr(self, "coder") and self.coder is not None:
            generated_code = self.coder.write_function()
            if generated_code:
                self.needs["hunger_data"] = max(0, self.needs["hunger_data"] - 20)
                self.needs["fatigue"] = min(100, self.needs["fatigue"] + 15)
                return f"Generated code (len={len(generated_code)})", True
            else:
                return "Code generation failed (Coder not ready).", False
        else:
            return "Coder module not available.", False
    except Exception as e:
        self.log(f"Write code error: {e}", level="ERROR")
        return f"Code generation error: {e}", False


# ══════════════════════════════════════════════════════════════════════════════
# REWARD CALCULATION
# ══════════════════════════════════════════════════════════════════════════════

def _calculate_reward(self, action, success, result):
    """
    Hitung reward berdasarkan:
    - Apakah action berhasil
    - Apakah action mengatasi kebutuhan tertentu
    - Impact terhadap needs state
    """
    reward = 0.0
    
    if not success:
        reward -= 0.5
        return reward
    
    reward += 0.5  # Base reward untuk success
    
    # Bonus reward untuk aksi yang meringankan needs
    if action == "PERFORM_WEB_SEARCH":
        reward += 0.3 if self.needs["hunger_data"] < 30 else 0.1
    elif action == "REST":
        reward += 0.4 if self.needs["fatigue"] < 30 else 0.1
    elif action == "ORGANIZE":
        reward += 0.3 if self.needs["messiness"] < 30 else 0.1
    elif action in ["TRIGGER_SELF_MUTATION", "EXECUTE_SIASIE_CYCLE"]:
        reward += 0.4  # Complex actions bernilai lebih
    elif action == "WRITE_CODE":
        reward += 0.5  # Code generation highly rewarded
    
    return reward
