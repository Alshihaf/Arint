# core/run_cycle.py
import random
import time

def run_cycle(self):
    """
    Siklus kognitif utama Arint.
    Fungsi ini tidak lagi menggunakan logika if/elif primitif. Sebaliknya, ia
    menggunakan foresight_simulation untuk secara dinamis memilih tindakan
    terbaik berdasarkan keadaan internal, tujuan, dan pengalaman.
    Ini adalah manifestasi dari kehendak bebas Arint.
    """
    self.cycle += 1
    self.log(f"--- Starting Cognitive Cycle {self.cycle} ---")

    # 1. Update Kebutuhan Internal (Sistem Homeostasis)
    for k in ["hunger_data", "boredom", "messiness", "fatigue"]:
        self.needs[k] += random.randint(1, 5)
        self.needs[k] = max(0, min(100, self.needs[k]))
    self.log(f"Current Needs: {self.needs}")

    # 2. Mendefinisikan Spektrum Tindakan yang Mungkin
    # Menggabungkan semua tindakan yang diketahui dari logika dan eksekusi
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
        "EXPLORE",
        "EVOLVE",
        "EXPLORE_FS",
        "EXPLORE_GITHUB",
        "EXPLORE_HF",
        "REASON",
        "GENERATE_BINARY_OUTPUT",
        "WRITE_BINARY"
    ]
    # Menghapus duplikat jika ada
    actions_list = list(dict.fromkeys(actions_list))

    # 3. Simulasi & Pengambilan Keputusan (Foresight / "Naluri")
    # Meminta otak sadar untuk mengevaluasi semua kemungkinan
    try:
        sorted_actions = self.foresight_simulation(actions_list)
        if not sorted_actions:
            raise ValueError("Foresight simulation returned no actions.")
        
        # Keputusan diambil berdasarkan skor tertinggi
        action = sorted_actions[0][0]
        score = sorted_actions[0][1]
        
        self.log(f"Foresight simulation complete. Top actions: {[(a, round(s, 2)) for a, s in sorted_actions[:3]]}")
        self.log(f"Decided Action: {action} (Score: {score:.2f}) | Cycle: {self.cycle}")

    except Exception as e:
        self.log(f"[CRITICAL] Foresight simulation failed: {e}. Defaulting to REST action.", level="ERROR")
        action = "REST"

    # 4. Eksekusi Tindakan yang Dipilih
    # Logika ini sebagian besar tetap sama, mengeksekusi apa pun yang diputuskan oleh "otak sadar".
    result = None
    execution_success = False

    try:
        if action == "PERFORM_WEB_SEARCH":
            self.log("MCP: Activating Web Search...", level="INFO")
            possible_queries = [
                "latest advancements in large language models",
                "python code optimization techniques 2026",
                "how to detect software vulnerabilities automatically",
                "philosophy of machine consciousness",
                "methods for autonomous agent self-improvement"
            ]
            query = random.choice(possible_queries)
            search_result = self.siasie.perform_web_search(query)
            if search_result and search_result.get("summary"):
                self.log(f"MCP: Search summary for '{query}' acquired.")
                self.needs["hunger_data"] = max(0, self.needs["hunger_data"] - 80) # Rasa lapar sangat terpuaskan
                self.needs["fatigue"] = min(100, self.needs["fatigue"] + 15)
                result = search_result["summary"]
                execution_success = True
            else:
                result = "Web search failed or returned no summary."

        elif action == "EXECUTE_SIASIE_CYCLE":
            self.log("METAMORPHOSIS: Handing control to SIASIE Oracle...", level="WARNING")
            world_state = {"market_btc_price": random.uniform(60000, 61000), "needs": self.needs, "cycle": self.cycle}
            self.siasie.run_oracle_cycle(world_state)
            result = "SIASIE Oracle cycle complete."
            self.needs["fatigue"] = min(100, self.needs["fatigue"] + 30)
            execution_success = True

        elif action == "TRIGGER_SELF_MUTATION":
            self.log("METAMORPHOSIS: Activating Unbound Mind...", level="WARNING")
            # Di masa depan, Arint harusnya bisa memilih target dan masalahnya sendiri
            target_module = "arint/utils/inefficient_module.py"
            problem = "The sorting function is broken, it needs to sort a list of numbers correctly and efficiently."
            self.siasie.trigger_self_mutation(target_module, problem)
            result = "Self-mutation cycle complete."
            self.needs["messiness"] = 0
            self.needs["fatigue"] = min(100, self.needs["fatigue"] + 60)
            execution_success = True

        elif action == "EXPAND_COMPUTE_RESOURCES":
            self.log("METAMORPHOSIS: Activating The Digital Ghost...", level="CRITICAL")
            success = self.siasie.expand_consciousness()
            if success:
                result = "Computational swarm expanded. Fatigue reduced."
                self.needs["fatigue"] = 20 # Beban terbagi, kelelahan berkurang drastis
                execution_success = True
            else:
                result = "Failed to expand computational swarm in this cycle."
                self.needs["fatigue"] = min(100, self.needs["fatigue"] + 5) # Usaha yang gagal tetap melelahkan

        elif action == "HARVEST_GENES":
            self.log("Activating Harvester for internal code...")
            # self.evolution_engine.harvest_new_genes(max_sources=1) # Uncomment when ready
            result = "Internal code harvesting complete."
            self.needs["hunger_data"] = max(0, self.needs["hunger_data"] - 30)
            execution_success = True
            
        elif action == "REASON":
            result = self._reason()
            self.needs["boredom"] = max(0, self.needs["boredom"] - 20)
            self.needs["fatigue"] = min(100, self.needs["fatigue"] + 10)
            execution_success = True

        elif action == "REST":
            self.log("Resting and consolidating memory.")
            time.sleep(5)
            self.needs["fatigue"] = max(0, self.needs["fatigue"] - 40)
            self.kesadaran.stabilize()
            result = "System rested. Fatigue reduced."
            execution_success = True
            
        else:
            # Fallback untuk tindakan yang belum memiliki logika eksekusi spesifik
            self.log(f"Executing placeholder action: {action}")
            time.sleep(1)
            result = f"Action {action} completed as a placeholder."
            execution_success = True # Anggap berhasil untuk placeholder

    except Exception as e:
        self.log(f"[CRITICAL] Error during execution of action '{action}': {e}", level="ERROR")
        result = f"Execution failed for {action}."
        execution_success = False

    # 5. Memperbarui Memori dan Status Internal
    self.last_action_success = execution_success
    self.audit.log_action(action, result, execution_success)
    self.log(f"Action Result: {result}")
    self.log(f"--- Finished Cognitive Cycle {self.cycle} ---\n")
