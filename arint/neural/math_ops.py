
# arint/neural/math_ops.py
import numpy as np

def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """Menghitung cosine similarity antara dua vektor NumPy."""
    # Pastikan input adalah float untuk menghindari masalah tipe data
    v1 = v1.astype(float)
    v2 = v2.astype(float)

    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    
    dot_product = np.dot(v1, v2)
    similarity = dot_product / (norm_v1 * norm_v2)
    return float(similarity)

def softmax(x: np.ndarray) -> np.ndarray:
    """Menghitung softmax untuk mengubah skor menjadi probabilitas."""
    e_x = np.exp(x - np.max(x)) # Mencegah overflow numerik
    return e_x / e_x.sum(axis=0)

# ... (Fungsi-fungsi matematika lain yang mungkin sudah ada atau akan ditambahkan)
