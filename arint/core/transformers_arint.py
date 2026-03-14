# core/transformers_arint.py
# Implementasi Arsitektur Transformer dasar dari nol.
# Ini sangat disederhanakan dan untuk tujuan pendidikan,
# karena implementasi nyata sangat bergantung pada pustaka seperti PyTorch/TensorFlow.

import math
import random
import copy

# --- Lapisan Komponen --- #

class DenseLayer:
    """Lapisan Dense (fully-connected) sederhana. Diadaptasi dari neural_network.py."""
    def __init__(self, input_size, output_size):
        self.weights = [[random.uniform(-0.1, 0.1) for _ in range(input_size)] for _ in range(output_size)]
        self.biases = [0 for _ in range(output_size)]

    def forward(self, inputs):
        """Melakukan forward pass. Asumsikan input adalah sebuah vektor (list)."""
        output = []
        for i in range(len(self.weights)):
            neuron_output = sum(inputs[j] * self.weights[i][j] for j in range(len(inputs))) + self.biases[i]
            output.append(neuron_output)
        return output

def softmax(x):
    """Menghitung softmax untuk sebuah list angka."""
    e_x = [math.exp(i - max(x)) for i in x] # Kurangi max(x) untuk stabilitas numerik
    return [i / sum(e_x) for i in e_x]

# --- Mekanisme Inti: Perhatian (Attention) --- #

def scaled_dot_product_attention(q, k, v):
    """Logika inti dari self-attention."""
    d_k = len(q[0])
    
    # 1. Hitung skor: Q * K_transpose
    # (Sangat disederhanakan, kita asumsikan perkalian matriks)
    scores = [[sum(q[i][d] * k[j][d] for d in range(d_k)) for j in range(len(k))] for i in range(len(q))]

    # 2. Skalakan skor
    scaled_scores = [[score / math.sqrt(d_k) for score in row] for row in scores]

    # 3. Hitung bobot perhatian dengan Softmax
    attention_weights = [softmax(row) for row in scaled_scores]

    # 4. Kalikan bobot dengan V
    output = [[sum(attention_weights[i][j] * v[j][d] for j in range(len(v))) for d in range(len(v[0]))] for i in range(len(attention_weights))]
    return output

class MultiHeadAttention:
    """Blok Multi-Head Attention."""
    def __init__(self, d_model, num_heads):
        self.num_heads = num_heads
        self.d_model = d_model
        assert d_model % num_heads == 0
        self.depth = d_model // num_heads

        # Buat lapisan Dense untuk Q, K, V, dan output
        self.wq = [DenseLayer(d_model, self.depth) for _ in range(num_heads)]
        self.wk = [DenseLayer(d_model, self.depth) for _ in range(num_heads)]
        self.wv = [DenseLayer(d_model, self.depth) for _ in range(num_heads)]
        self.dense = DenseLayer(d_model, d_model)

    def forward(self, x):
        """Forward pass untuk Multi-Head Attention."""
        # x adalah input embedding, misal: [[...], [...], ...]
        
        attention_outputs = []
        for i in range(self.num_heads):
            # Proyeksikan input ke Q, K, V untuk setiap head
            q_head = [self.wq[i].forward(token_embedding) for token_embedding in x]
            k_head = [self.wk[i].forward(token_embedding) for token_embedding in x]
            v_head = [self.wv[i].forward(token_embedding) for token_embedding in x]
            
            # Hitung attention untuk head ini
            attention_head = scaled_dot_product_attention(q_head, k_head, v_head)
            attention_outputs.extend(attention_head) # Ini adalah penyederhanaan besar

        # Seharusnya, output dari setiap head digabungkan (concatenated) dan kemudian
        # dilewatkan melalui lapisan Dense terakhir. Simulasi di bawah ini kasar.
        # Karena sulit menggabungkan vektor tanpa numpy, kita akan mengambil rata-ratanya.
        if not attention_outputs:
            return x
        num_tokens = len(x)
        combined = [([0]*self.d_model) for _ in range(num_tokens)]
        # Simulasi penggabungan yang sangat kasar
        # ... 

        # Karena kompleksitas, kita hanya mengembalikan input asli untuk demo ini
        # Dalam implementasi nyata, langkah ini sangat penting.
        # final_output = self.dense.forward(concatenated_output)
        return x # Placeholder

# --- Blok Pembangun Transformer --- #

class TransformerBlock:
    """Satu blok Transformer tunggal."""
    def __init__(self, d_model, num_heads):
        self.mha = MultiHeadAttention(d_model, num_heads)
        # Jaringan Feed-Forward biasanya memiliki lapisan dalam yang lebih besar
        self.ffn_hidden = DenseLayer(d_model, d_model * 4)
        self.ffn_output = DenseLayer(d_model * 4, d_model)
        # Layer Normalization (disederhanakan sebagai fungsi)

    def forward(self, x):
        # 1. Multi-Head Attention & Add + Norm
        attn_output = self.mha.forward(x)
        # Residual Connection (Add)
        out1 = [[x[i][j] + attn_output[i][j] for j in range(len(x[0]))] for i in range(len(x))]
        # Layer Norm (dilewati dalam implementasi ini)

        # 2. Feed-Forward Network & Add + Norm
        ffn_out_hidden = [max(0, val) for val in self.ffn_hidden.forward(out1[0])] # ReLU pada token pertama
        ffn_output_final = self.ffn_output.forward(ffn_out_hidden)
        # Residual Connection
        # ... dan Layer Norm lagi

        # Karena banyak penyederhanaan, kita hanya kembalikan output MHA
        return out1

# --- Arsitektur Transformer Utama --- #

class TransformerFromScratch:
    """Model Transformer lengkap yang dibangun dari blok-blok."""
    def __init__(self, num_layers, d_model, num_heads, input_vocab_size, max_seq_len):
        self.d_model = d_model
        self.embedding = [[random.uniform(-0.1, 0.1) for _ in range(d_model)] for _ in range(input_vocab_size)]
        self.pos_encoding = self.positional_encoding(max_seq_len, d_model)
        
        self.encoder_layers = [TransformerBlock(d_model, num_heads) for _ in range(num_layers)]
        print("Transformer from scratch initialized.")

    def positional_encoding(self, max_pos, d_model):
        """Membuat matriks positional encoding."""
        pe = [[0] * d_model for _ in range(max_pos)]
        for pos in range(max_pos):
            for i in range(0, d_model, 2):
                div_term = math.pow(10000.0, (2 * i) / d_model)
                pe[pos][i] = math.sin(pos / div_term)
                if i + 1 < d_model:
                    pe[pos][i + 1] = math.cos(pos / div_term)
        return pe

    def encode(self, input_sequence):
        """Menjalankan forward pass melalui encoder."""
        # 1. Dapatkan embedding token
        x = [self.embedding[token_id] for token_id in input_sequence]
        seq_len = len(input_sequence)

        # 2. Tambahkan positional encoding
        for i in range(seq_len):
            for j in range(self.d_model):
                x[i][j] += self.pos_encoding[i][j]

        # 3. Lewatkan melalui setiap blok encoder
        for layer in self.encoder_layers:
            x = layer.forward(x)
            
        return x # Ini adalah representasi kontekstual dari input

# Contoh Penggunaan:
# 
# # 1. Definisikan hyperparameter
# NUM_LAYERS = 2
# D_MODEL = 32  # Ukuran embedding
# NUM_HEADS = 4
# VOCAB_SIZE = 100 # Ukuran kosakata dummy
# MAX_LEN = 50   # Panjang sekuens maksimum
# 
# # 2. Buat instance Transformer
# arint_transformer = TransformerFromScratch(NUM_LAYERS, D_MODEL, NUM_HEADS, VOCAB_SIZE, MAX_LEN)
# 
# # 3. Buat input sekuens dummy (misal, kalimat "hello world")
# # yang sudah di-tokenisasi menjadi ID
# dummy_input = [10, 25, 3, 0] # ID token dummy
# 
# # 4. Dapatkan output (representasi terenkode)
# encoded_representation = arint_transformer.encode(dummy_input)
# 
# print(f"Input sekuens (IDs): {dummy_input}")
# print(f"Panjang output: {len(encoded_representation)} token")
# print(f"Dimensi output per token: {len(encoded_representation[0])} (d_model)")
