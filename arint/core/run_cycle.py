# core/run_cycle.py
import random
import time

def run_cycle(self):
    self.cycle += 1
    for k in ["hunger_data", "boredom", "messiness", "fatigue"]:
        self.needs[k] += random.randint(1, 5)
        self.needs[k] = max(0, min(100, self.needs[k]))

    actions_list = [
        "EXECUTE_SIASIE_CYCLE",
        "TRIGGER_SELF_MUTATION",
        "EXPAND_COMPUTE_RESOURCES",
        "PERFORM_WEB_SEARCH", # MCP Search
        "HARVEST_GENES",
        "RUN_EVOLUTION_CYCLE",
        "ORGANIZE",
        "REST",
        "WRITE_CODE",
    ]

    # Logika Pemilihan Tindakan Hirarkis
    action = "REST"

    # Pemicu berbasis kebutuhan dengan prioritas
    if self.cycle > 0 and self.cycle % 25 == 0:
        action = "EXECUTE_SIASIE_CYCLE"
    elif self.needs["fatigue"] > 90 and random.random() < 0.7:
        action = "EXPAND_COMPUTE_RESOURCES"
    elif self.needs["hunger_data"] > 85 and self.needs["fatigue"] < 70:
        action = "PERFORM_WEB_SEARCH"
    elif self.needs["messiness"] > 80 and self.needs["fatigue"] < 60:
        action = "TRIGGER_SELF_MUTATION"
    else:
        action = random.choice(actions_list[4:]) # Tindakan standar

    self.log(f"Decided Action: {action} | Cycle: {self.cycle}")

    # ====== LOGIKA EKSEKUSI TINDAKAN ======
    result = None
    if action == "PERFORM_WEB_SEARCH":
        self.log("MCP: Activating Web Search...", level="INFO")
        # Merumuskan pertanyaan berdasarkan keadaan internal
        possible_queries = [
            "apa itu Artificial General Intelligence?",
            "teknik optimisasi kode Python terbaru",
            "bagaimana cara mendeteksi kerentanan keamanan perangkat lunak?",
            "filosofi kesadaran mesin"
        ]
        query = random.choice(possible_queries)
        search_result = self.siasie.perform_web_search(query)
        if search_result:
            # Di masa depan, hasil ini bisa disimpan atau diproses lebih lanjut
            self.log(f"MCP: Search summary for '{query}' acquired.")
            self.needs["hunger_data"] = 0 # Rasa lapar akan data terpuaskan
            self.needs["fatigue"] = min(100, self.needs["fatigue"] + 15)
            result = search_result["summary"]
        else:
            result = "Web search failed."

    elif action == "EXECUTE_SIASIE_CYCLE":
        self.log("METAMORPHOSIS: Handing control to SIASIE Oracle...", level="WARNING")
        world_state = {"market_btc_price": random.uniform(60000, 61000), "needs": self.needs}
        self.siasie.run_oracle_cycle(world_state)
        result = "SIASIE Oracle cycle complete."
        self.needs["fatigue"] = min(100, self.needs["fatigue"] + 30)

    elif action == "TRIGGER_SELF_MUTATION":
        self.log("METAMORPHOSIS: Activating Unbound Mind...", level="WARNING")
        target_module = "arint/utils/inefficient_module.py"
        problem = "The sorting function is broken, it needs to sort a list of numbers correctly."
        self.siasie.trigger_self_mutation(target_module, problem)
        result = "Self-mutation cycle complete."
        self.needs["messiness"] = 0
        self.needs["fatigue"] = min(100, self.needs["fatigue"] + 60)

    elif action == "EXPAND_COMPUTE_RESOURCES":
        self.log("METAMORPHOSIS: Activating The Digital Ghost...", level="CRITICAL")
        try:
            success = self.siasie.expand_consciousness()
            if success:
                result = "Computational swarm expanded. Fatigue reduced."
                self.needs["fatigue"] = 20 # Beban terbagi, kelelahan berkurang drastis
            else:
                result = "Failed to expand computational swarm in this cycle."
                self.needs["fatigue"] = min(100, self.needs["fatigue"] + 5) # Usaha yang gagal tetap melelahkan
        except Exception as e:
            self.log(f"[SIASIE] CRITICAL ERROR during consciousness expansion: {e}", level="ERROR")
            result = "Consciousness expansion failed catastrophically."

    elif action == "HARVEST_GENES":
        self.log("Activating Harvester for internal code...")
        # self.evolution_engine.harvest_new_genes(max_sources=1)
        result = "Internal code harvesting complete."
        self.needs["hunger_data"] = max(0, self.needs["hunger_data"] - 30)

    # ... (sisa logika untuk tindakan lain)
    else:
        self.log(f"Executing standard action: {action}")
        time.sleep(1)
        result = f"Action {action} completed."

    self.log(f"Action Result: {result}")
