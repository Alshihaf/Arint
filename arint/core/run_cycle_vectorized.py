
# core/run_cycle_vectorized.py
import random
import time
import numpy as np

def run_cycle_vectorized(self):
    """
    Siklus hidup operasional Arint yang sepenuhnya berbasis vektor.
    Setiap keputusan adalah hasil dari komputasi matematika murni.
    """
    self.cycle += 1
    self.log(f"--- Starting Vectorized Cognitive Cycle {self.cycle} ---")

    # 1. Update Kebutuhan Internal (Homeostasis)
    for k in ["hunger_data", "boredom", "messiness", "fatigue"]:
        self.needs[k] = max(0, min(100, self.needs[k] + random.randint(1, 5)))

    # 2. Pengambilan Keputusan Berbasis Vektor
    # Memanggil inti kognisi vektor untuk menentukan tindakan selanjutnya.
    try:
        action, score = self.foresight_simulation() # Memanggil foresight_simulation_vectorized
        self.log(f"Vectorized Cognition Result: Chose '{action}' with alignment score {score:.4f}")
    except Exception as e:
        self.log(f"[CRITICAL] Vectorized foresight simulation failed: {e}. Defaulting to REST.", level="ERROR")
        action = "REST"
        score = -1.0

    # 3. Eksekusi Tindakan yang Dipilih
    # Logika eksekusi tetap sama, tetapi sekarang dipicu oleh keputusan matematis.
    result = None
    execution_success = False
    try:
        # (Logika eksekusi dari run_cycle.py sebelumnya dapat disalin ke sini)
        # Contoh untuk beberapa tindakan kunci:
        if action == "PERFORM_WEB_SEARCH":
            self.log("Activating Web Search based on vector alignment...", level="INFO")
            # ... (logika eksekusi)
            result = "Web search completed."
            execution_success = True
            self.needs["hunger_data"] = max(0, self.needs["hunger_data"] - 80)

        elif action == "EXECUTE_SIASIE_CYCLE":
            self.log("Initiating SIASIE Protocol based on vector alignment...", level="WARNING")
            # ... (logika eksekusi)
            result = "SIASIE cycle completed."
            execution_success = True
            self.needs["boredom"] = max(0, self.needs["boredom"] - 70)

        elif action == "TRIGGER_SELF_MUTATION":
            self.log("Activating Self-Mutation based on vector alignment...", level="WARNING")
            # ... (logika eksekusi)
            result = "Self-mutation triggered."
            execution_success = True
            self.needs["messiness"] = 0
        
        elif action == "REST":
            self.log("Entering REST state based on vector alignment.")
            time.sleep(5)
            self.needs["fatigue"] = max(0, self.needs["fatigue"] - 40)
            self.kesadaran.stabilize()
            result = "System rested."
            execution_success = True

        else:
            self.log(f"Executing placeholder for action: {action}")
            time.sleep(1)
            result = f"Action {action} completed as placeholder."
            execution_success = True

        # Simpan state vector yang menghasilkan keputusan ini untuk konteks LTM
        # Ini penting untuk pembelajaran meta-kognitif di masa depan
        self.ltm.log_state_action_outcome(self.latest_state_vector, action, execution_success)

    except Exception as e:
        self.log(f"[CRITICAL] Execution failed for action '{action}': {e}", level="ERROR")
        result = f"Execution failed catastrophically."
        execution_success = False

    # 4. Refleksi dan Penutupan Siklus
    self.last_action_success = execution_success
    self.audit.log_action(action, result, execution_success)
    self.log(f"Action Result: {result}")
    self.log(f"--- Finished Vectorized Cognitive Cycle {self.cycle} ---\n")
