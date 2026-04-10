
# arint/neural/nlu.py
import numpy as np
import re

class VectorNLU:
    """
    NLU berbasis vektor yang telah dirombak total.
    Mengubah teks menjadi representasi vektor numerik (embedding) menggunakan
    kosakata yang dibangun secara internal.
    """
    def __init__(self, vector_size=64):
        self.vector_size = vector_size
        self.vocabulary = {}
        self.vectors = {}
        self.next_index = 0

    def _add_to_vocab(self, word: str):
        """Menambahkan kata ke kosakata jika belum ada."""
        word = word.lower().strip()
        if word and word not in self.vocabulary:
            self.vocabulary[word] = self.next_index
            # Membuat vektor unik yang stabil berdasarkan hash kata
            # Ini bukan embedding semantik, tapi ini deterministik dan unik.
            np.random.seed(hash(word) & 0xFFFFFFFF)
            vector = np.random.randn(self.vector_size)
            self.vectors[word] = vector / np.linalg.norm(vector)
            self.next_index += 1

    def build_vocabulary_from_actions(self, action_names: list[str]):
        """
        Membangun kosakata awal dari nama tindakan yang diketahui dan konsep inti.
        """
        # Konsep inti
        core_concepts = ["evolve", "explore", "reason", "organize", "rest", "search", "code", "memory", "mutation", "goal"]
        
        for concept in core_concepts:
            self._add_to_vocab(concept)

        for action_name in action_names:
            # Pecah nama tindakan menjadi kata-kata komponennya
            words = action_name.lower().replace('_', ' ').split()
            for word in words:
                self._add_to_vocab(word)
        print(f"Vocabulary built with {len(self.vocabulary)} unique words.")

    def tokenize(self, text: str) -> list[str]:
        """Tokenisasi teks sederhana."""
        return re.findall(r'\b\w+\b', text.lower())

    def vectorize(self, text: str) -> np.ndarray:
        """
        Mengubah teks menjadi satu vektor dengan merata-ratakan vektor kata-katanya.
        Ini adalah pendekatan "Bag of Words" yang di-vektorisasi.
        """
        tokens = self.tokenize(text)
        if not tokens:
            return np.zeros(self.vector_size)

        vector_sum = np.zeros(self.vector_size)
        word_count = 0
        for token in tokens:
            if token in self.vectors:
                vector_sum += self.vectors[token]
                word_count += 1
        
        if word_count == 0:
            return np.zeros(self.vector_size)
            
        return vector_sum / word_count

# Menghapus kelas lama untuk digantikan dengan yang baru
# class AdvancedNLU: ...
