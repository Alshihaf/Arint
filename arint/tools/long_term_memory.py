
# arint/tools/long_term_memory.py
import sqlite3
import json
import threading
import time
import numpy as np
from pathlib import Path
from typing import List, Any, Optional, Tuple

# Impor operasi matematika yang sekarang terpusat
from arint.neural.math_ops import cosine_similarity

class LongTermMemory:
    """
    LTM yang dirombak total untuk kognisi berbasis vektor.
    Menyimpan state_vector mentah untuk setiap tindakan dan menggunakan
    pencarian vektor (KNN) untuk mengingat pengalaman serupa.
    """
    
    def __init__(self, db_path="arint/memory/long_term_vector.db", vector_size=64):
        self.db_path = db_path
        self.vector_size = vector_size
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        """Inisialisasi DB dengan skema yang mendukung vektor."""
        with self.lock:
            cursor = self.conn.cursor()
            # Tabel utama untuk menyimpan setiap instance pengalaman
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS experiences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cycle INTEGER NOT NULL,
                    action_name TEXT NOT NULL,
                    state_vector BLOB NOT NULL,
                    outcome_score REAL NOT NULL, -- Skor hasil (misal: perubahan 'purpose', atau 1.0/-1.0 untuk sukses/gagal)
                    timestamp REAL NOT NULL
                )
            """ )
            # Index untuk mempercepat pencarian berdasarkan nama tindakan
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_action_name ON experiences (action_name)")
            self.conn.commit()

    def _serialize_vector(self, vector: np.ndarray) -> bytes:
        """Mengubah vektor NumPy menjadi format biner untuk disimpan di DB."""
        return vector.astype(np.float32).tobytes()

    def _deserialize_vector(self, blob: bytes) -> np.ndarray:
        """Mengubah data biner dari DB kembali menjadi vektor NumPy."""
        return np.frombuffer(blob, dtype=np.float32)

    def log_experience(self, cycle: int, action_name: str, state_vector: np.ndarray, outcome_score: float):
        """Mencatat satu pengalaman (keadaan -> tindakan -> hasil) ke LTM."""
        if state_vector.shape[0] != self.vector_size:
            raise ValueError(f"Invalid vector size: expected {self.vector_size}, got {state_vector.shape[0]}")

        serialized_vector = self._serialize_vector(state_vector)
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    "INSERT INTO experiences (cycle, action_name, state_vector, outcome_score, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (cycle, action_name, serialized_vector, outcome_score, time.time())
                )
                self.conn.commit()
            except Exception as e:
                print(f"[LTM ERROR] Failed to log experience: {e}")

    def recall_similar_experiences(self, current_state_vector: np.ndarray, action_name: str, k: int = 5) -> Optional[float]:
        """
        Mengingat pengalaman masa lalu yang paling mirip untuk tindakan tertentu dan memprediksi hasilnya.
        Ini adalah implementasi K-Nearest Neighbors (KNN) di dalam LTM.
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    "SELECT state_vector, outcome_score FROM experiences WHERE action_name = ?",
                    (action_name,)
                )
                rows = cursor.fetchall()
                
                if not rows:
                    return None # Tidak ada pengalaman untuk tindakan ini

                # Hitung kemiripan (cosine similarity) antara keadaan saat ini dan semua pengalaman masa lalu
                similarities = []
                for vector_blob, outcome in rows:
                    past_vector = self._deserialize_vector(vector_blob)
                    sim = cosine_similarity(current_state_vector, past_vector)
                    similarities.append((sim, outcome))
                
                if not similarities:
                    return None

                # Urutkan berdasarkan kemiripan tertinggi
                similarities.sort(key=lambda x: x[0], reverse=True)
                
                # Ambil K tetangga terdekat
                top_k_neighbors = similarities[:k]

                if not top_k_neighbors:
                    return None

                # Hitung rata-rata tertimbang dari hasil K tetangga terdekat
                # Semakin mirip pengalamannya, semakin besar bobotnya
                total_weight = sum(sim for sim, _ in top_k_neighbors)
                if total_weight == 0:
                    # Jika semua kemiripan adalah 0, ambil rata-rata biasa
                    return sum(outcome for _, outcome in top_k_neighbors) / len(top_k_neighbors)
                
                weighted_sum = sum(sim * outcome for sim, outcome in top_k_neighbors)
                predicted_outcome = weighted_sum / total_weight
                
                return predicted_outcome

            except Exception as e:
                print(f"[LTM ERROR] Failed to recall experiences: {e}")
                return None

    def get_last_action(self) -> Optional[str]:
        """Mendapatkan tindakan terakhir yang dieksekusi."""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT action_name FROM experiences ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            return row[0] if row else None

