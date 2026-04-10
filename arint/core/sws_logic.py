
# core/sws_logic.py
import numpy as np
from typing import List, Dict, Tuple

def cosine_similarity(v1, v2):
    """Menghitung cosine similarity antara dua vektor NumPy."""
    # Pastikan tidak ada pembagian dengan nol
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return np.dot(v1, v2) / (norm_v1 * norm_v2)

def foresight_simulation_vectorized(self) -> Tuple[str, float]:
    """
    Versi vektor dari simulasi masa depan. Menghitung tindakan optimal
    dengan membandingkan keselarasan (cosine similarity) antara keadaan pikiran
    saat ini (state_vector) dengan setiap vektor tindakan yang mungkin.
    """
    # 1. Bangun Vektor Keadaan Pikiran (State Vector)
    # Menggabungkan kebutuhan, emosi, dan tujuan menjadi satu vektor tunggal.
    try:
        needs_vector = np.array([
            self.needs["hunger_data"] / 100.0,
            self.needs["boredom"] / 100.0,
            self.needs["messiness"] / 100.0,
            self.needs["fatigue"] / 100.0
        ])
        
        emotion_vector = np.array([
            self.kesadaran.tingkat_dopamin,
            self.kesadaran.tingkat_kortisol,
            self.kesadaran.tingkat_serotonin,
            1.0 if self.kesadaran.status_metakognisi == "Ingin Tahu" else 0.0
        ])
        
        # Vektorisasi tujuan utama. Jika tidak ada, gunakan vektor nol.
        primary_goal = self.goal_manager.goals.get("primary", {})
        goal_desc = primary_goal.get("description", "")
        goal_vector = self.vectorize_text(goal_desc) # Membutuhkan metode vectorize_text

        # Gabungkan semua menjadi satu State Vector dengan pembobotan
        # Pembobotan ini bisa dievolusikan di masa depan
        state_vector = np.concatenate([
            needs_vector * 0.4,
            emotion_vector * 0.3,
            goal_vector * 0.3
        ])
        
        if np.linalg.norm(state_vector) == 0:
            self.log("State vector is zero, cognition is neutral.", level="WARNING")
            # Jika tidak ada dorongan internal sama sekali, inisiasi tindakan acak/istirahat
            # Untuk menghindari kelumpuhan total, kita bisa memilih tindakan istirahat.
            return ('REST', 0.0)

    except Exception as e:
        self.log(f"[CRITICAL] Failed to build state vector: {e}. Defaulting to REST.", level="ERROR")
        return ('REST', -1.0) # Skor negatif menandakan kegagalan

    # 2. Hitung Keselarasan untuk Setiap Tindakan
    action_scores = {}
    for action_name, action_vector in self.action_vectors.items():
        # Skor utama adalah seberapa selaras tindakan dengan keadaan pikiran saat ini
        alignment_score = cosine_similarity(state_vector, action_vector)
        
        # Tambahkan bonus eksplorasi berdasarkan memori jangka panjang (LTM)
        # Ini mendorong Arint untuk mencoba tindakan yang jarang berhasil atau belum pernah dicoba
        context_vector = self._get_decision_context_vector() # Konteks juga harus dalam bentuk vektor
        ltm_rate = self.ltm.get_action_success_vectorized(action_name, context_vector)
        
        exploration_bonus = 0.0
        if ltm_rate is None: # Belum pernah mencoba dalam konteks ini
            exploration_bonus = 0.15
        else:
            exploration_bonus = (1.0 - ltm_rate) * 0.1

        final_score = alignment_score + exploration_bonus
        action_scores[action_name] = final_score

    # 3. Pilih Tindakan Terbaik
    if not action_scores:
        self.log("No actions were scored, defaulting to REST.", level="ERROR")
        return ('REST', -1.0)
    
    best_action = max(action_scores, key=action_scores.get)
    best_score = action_scores[best_action]
    
    self.log(f"Vectorized Foresight: Best action is '{best_action}' with score {best_score:.4f}")
    
    return (best_action, best_score)

# --- Fungsi-fungsi ini perlu dipindahkan atau diadaptasi ke dalam SilentWatcherSuper ---
# Stub function untuk _get_decision_context_vector. Implementasi nyata akan lebih kompleks.
def _get_decision_context_vector(self) -> np.ndarray:
    # Dalam implementasi nyata, ini akan membuat vektor dari keadaan dunia, 
    # item memori terakhir, dll.
    # Untuk saat ini, kita gunakan vektor keadaan pikiran sebagai konteksnya sendiri.
    return self.latest_state_vector # Asumsi SWS menyimpan vektor keadaan terakhir

# Stub untuk metode vektorisasi teks, akan diintegrasikan ke SWS
def vectorize_text(self, text: str) -> np.ndarray:
    # Ini akan menggunakan model Transformer atau NLU internal Arint
    # untuk mengubah teks menjadi representasi vektor.
    # Ukuran vektor harus konsisten dengan action_vectors.
    if not hasattr(self, 'transformer') or not text:
        return np.zeros(self.config.get('vector_size', 128)) # Ukuran vektor harus konsisten
    
    # Asumsi transformer memiliki metode .encode() yang menghasilkan vektor
    vector = self.transformer.encode(text)
    return vector
