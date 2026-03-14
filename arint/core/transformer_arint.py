
# core/transformer_arint.py
# Implementasi Arsitektur Transformer dan Antarmuka Arint dari nol dengan Python murni.

import math
import random
import json
import re
import os
from collections import Counter

# --- Komponen-Komponen Dasar ---

def softmax(x: list) -> list:
    """Menghitung softmax untuk sebuah list angka untuk stabilitas numerik."""
    if not x: return []
    max_val = max(x)
    e_x = [math.exp(i - max_val) for i in x]
    sum_e_x = sum(e_x)
    return [i / sum_e_x for i in e_x]

class LayerNormalization:
    """Implementasi Layer Normalization dengan Python murni."""
    def __init__(self, size, epsilon=1e-6):
        self.size = size
        self.epsilon = epsilon
        self.gamma = [1.0] * size # Bobot skala
        self.beta = [0.0] * size  # Bobot geser

    def forward(self, x: list) -> list:
        # x adalah sebuah vektor
        mean = sum(x) / self.size
        variance = sum([(i - mean) ** 2 for i in x]) / self.size
        std = math.sqrt(variance + self.epsilon)
        
        normalized = [(i - mean) / std for i in x]
        
        # Terapkan skala dan geser
        return [(self.gamma[i] * normalized[i]) + self.beta[i] for i in range(self.size)]

class PurePythonDenseLayer:
    """Lapisan dense fungsionalitas minimal yang diperlukan untuk Transformer."""
    def __init__(self, input_size, output_size):
        # Inisialisasi He untuk aktivasi ReLU
        limit = math.sqrt(6 / input_size)
        self.weights = [[random.uniform(-limit, limit) for _ in range(input_size)] for _ in range(output_size)]
        self.biases = [0.0] * output_size

    def forward(self, inputs: list) -> list:
        outputs = [0.0] * len(self.weights)
        for i in range(len(self.weights)):
            neuron_output = sum(inputs[j] * self.weights[i][j] for j in range(len(inputs))) + self.biases[i]
            outputs[i] = neuron_output
        return outputs

class PositionwiseFeedForward:
    """Implementasi Jaringan Feed-Forward Position-wise."""
    def __init__(self, d_model, d_ff):
        self.linear1 = PurePythonDenseLayer(d_model, d_ff)
        self.linear2 = PurePythonDenseLayer(d_ff, d_model)

    def relu(self, x: list) -> list:
        return [max(0, val) for val in x]

    def forward(self, x: list) -> list:
        # x adalah sebuah vektor [d_model]
        return self.linear2.forward(self.relu(self.linear1.forward(x)))


# --- Komponen Arsitektur Transformer ---

class MultiHeadAttention:
    """Implementasi Multi-Head Attention dengan Python murni."""
    def __init__(self, d_model, num_heads):
        self.num_heads = num_heads
        self.d_model = d_model
        assert d_model % num_heads == 0, "d_model harus bisa dibagi oleh num_heads"
        self.depth = d_model // num_heads

        self.wq = [PurePythonDenseLayer(d_model, self.depth) for _ in range(num_heads)]
        self.wk = [PurePythonDenseLayer(d_model, self.depth) for _ in range(num_heads)]
        self.wv = [PurePythonDenseLayer(d_model, self.depth) for _ in range(num_heads)]
        self.dense = PurePythonDenseLayer(d_model, d_model)

    def scaled_dot_product_attention(self, q, k, v, mask=None):
        matmul_qk = [[sum(q[i][d] * k[j][d] for d in range(self.depth)) for j in range(len(k))] for i in range(len(q))]
        
        scale_factor = math.sqrt(self.depth)
        scaled_attention_logits = [[x / scale_factor for x in row] for row in matmul_qk]

        if mask is not None:
            for i in range(len(scaled_attention_logits)):
                for j in range(len(scaled_attention_logits[i])):
                    if mask[i][j] == 0:
                        scaled_attention_logits[i][j] = -1e9

        attention_weights = [softmax(row) for row in scaled_attention_logits]
        
        output = [[sum(attention_weights[i][j] * v[j][d] for j in range(len(v))) for d in range(self.depth)] for i in range(len(q))]
        return output

    def forward(self, v: list, k: list, q: list, mask=None) -> list:
        heads = []
        for i in range(self.num_heads):
            query = [self.wq[i].forward(q_token) for q_token in q]
            key = [self.wk[i].forward(k_token) for k_token in k]
            value = [self.wv[i].forward(v_token) for v_token in v]
            head = self.scaled_dot_product_attention(query, key, value, mask)
            heads.append(head)
        
        concatenated = []
        for token_idx in range(len(q)):
            token_concat = []
            for head in heads:
                token_concat.extend(head[token_idx])
            concatenated.append(token_concat)

        output = [self.dense.forward(token_vec) for token_vec in concatenated]
        return output

class EncoderLayer:
    """Satu lapisan Encoder tunggal."""
    def __init__(self, d_model, num_heads, d_ff):
        self.mha = MultiHeadAttention(d_model, num_heads)
        self.ffn = PositionwiseFeedForward(d_model, d_ff)

        self.norm1 = LayerNormalization(d_model)
        self.norm2 = LayerNormalization(d_model)

    def forward(self, x: list, mask=None) -> list:
        # x adalah matriks: [seq_len, d_model]
        
        # Sub-lapisan 1: Multi-Head Attention
        attn_output = self.mha.forward(x, x, x, mask)
        # Koneksi residual dan normalisasi
        sublayer1_out = [[x[i][j] + attn_output[i][j] for j in range(len(x[0]))] for i in range(len(x))]
        sublayer1_out = [self.norm1.forward(vec) for vec in sublayer1_out]

        # Sub-lapisan 2: Feed-Forward Network
        ffn_output = [self.ffn.forward(vec) for vec in sublayer1_out]
        # Koneksi residual dan normalisasi
        sublayer2_out = [[sublayer1_out[i][j] + ffn_output[i][j] for j in range(len(sublayer1_out[0]))] for i in range(len(sublayer1_out))]
        sublayer2_out = [self.norm2.forward(vec) for vec in sublayer2_out]

        return sublayer2_out

# --- Tokenizer ---
class SimpleTokenizer:
    # ... (implementasi tokenizer tetap sama)
    def __init__(self, vocab_size=5000):
        self.vocab_size = vocab_size
        self.word2idx = {'<PAD>': 0, '<UNK>': 1, '<BOS>': 2, '<EOS>': 3}
        self.idx2word = {v: k for k, v in self.word2idx.items()}
        self.fitted = False

    def fit(self, texts):
        word_counts = Counter()
        for text in texts:
            words = re.findall(r'\w+', text.lower())
            word_counts.update(words)
        most_common = word_counts.most_common(self.vocab_size - len(self.word2idx))
        for i, (word, _) in enumerate(most_common, start=len(self.word2idx)):
            self.word2idx[word] = i
            self.idx2word[i] = word
        self.fitted = True

    def encode(self, text, max_len=50):
        words = re.findall(r'\w+', text.lower())
        ids = [self.word2idx.get(w, self.word2idx['<UNK>']) for w in words]
        ids = [self.word2idx['<BOS>']] + ids + [self.word2idx['<EOS>']]
        padded_ids = ids[:max_len] + [self.word2idx['<PAD>']] * (max_len - len(ids))
        return padded_ids

    def decode(self, ids):
        special_tokens = {self.word2idx['<PAD>'], self.word2idx['<BOS>'], self.word2idx['<EOS>']}
        return ' '.join(self.idx2word.get(i, '<UNK>') for i in ids if i not in special_tokens)

# --- Kelas Kerangka TransformerArint ---
class TransformerArint:
    def __init__(self, config=None):
        # ... (implementasi init tetap sama, tetapi sekarang akan membangun encoder)
        if config is None:
            config = {
                'd_model': 64, 'num_heads': 4, 'N': 2, 'd_ff': 128,
                'vocab_size': 5000, 'max_seq_len': 50
            }
        print("Initializing TransformerArint (Pure Python Version)...")
        self.config = config
        self.d_model = config['d_model']
        self.N = config['N']
        self.tokenizer = SimpleTokenizer(vocab_size=config['vocab_size'])
        self.model_path = "memory/transformer_arint_model.json"
        self.tokenizer_path = "memory/transformer_arint_tokenizer.json"

        # Inisialisasi komponen Transformer
        self.embedding = PurePythonDenseLayer(self.config['vocab_size'], self.d_model)
        self.encoder_layers = [EncoderLayer(self.d_model, config['num_heads'], config['d_ff']) for _ in range(self.N)]
        
        # TODO: Tambahkan Positional Encoding, Decoder, dan Final Layer

        print("TransformerArint initialized with Encoder blocks.")

    def encode_sentence(self, text: str) -> list:
        """Mengubah kalimat menjadi representasi vektor (embedding)."""
        # 1. Tokenize dan one-hot encode
        token_ids = self.tokenizer.encode(text, max_len=self.config['max_seq_len'])
        
        # Simple one-hot encoding
        one_hot_vectors = []
        for id in token_ids:
            vec = [0.0] * self.config['vocab_size']
            if id < self.config['vocab_size']:
                vec[id] = 1.0
            one_hot_vectors.append(vec)
            
        # 2. Embedding
        embedded_input = [self.embedding.forward(vec) for vec in one_hot_vectors]

        # TODO: Tambahkan Positional Encoding di sini

        # 3. Proses melalui Encoder
        encoder_output = embedded_input
        for i in range(self.N):
            encoder_output = self.encoder_layers[i].forward(encoder_output)

        # 4. Global Average Pooling (rata-rata vektor token)
        if not encoder_output or not encoder_output[0]: return [0.0] * self.d_model
        avg_vector = [0.0] * self.d_model
        for i in range(self.d_model):
            avg_vector[i] = sum(token_vec[i] for token_vec in encoder_output) / len(encoder_output)

        print(f"--- INFO: Successfully encoded '{text[:20]}...' to a vector. ---")
        return avg_vector

    # ... (metode stub untuk generate, save, load tetap sama untuk saat ini) ...
    def generate(self, prompt, max_new_tokens=20):
        print(f"--- WARNING: Transformer.generate is a stub. ---")
        return prompt # Hanya mengembalikan prompt

    def save(self):
        print(f"--- WARNING: Transformer.save is a stub. ---")

    def load(self):
        print("--- WARNING: Transformer.load is a stub. ---")

    def save_tokenizer(self):
        with open(self.tokenizer_path, 'w') as f:
            json.dump({
                'word2idx': self.tokenizer.word2idx,
                'idx2word': self.tokenizer.idx2word,
                'vocab_size': self.tokenizer.vocab_size
            }, f, indent=4)
        print(f"Tokenizer saved to {self.tokenizer_path}")

    def load_tokenizer(self):
        if os.path.exists(self.tokenizer_path):
            with open(self.tokenizer_path, 'r') as f:
                data = json.load(f)
                self.tokenizer.word2idx = data['word2idx']
                self.tokenizer.idx2word = {int(k): v for k, v in data['idx2word'].items()}
                self.tokenizer.vocab_size = data['vocab_size']
                self.tokenizer.fitted = True
            print(f"Tokenizer loaded from {self.tokenizer_path}")
        else:
            print("No tokenizer file found.")
