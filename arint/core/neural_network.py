# core/neural_network
import numpy as np
np.random.seed(42)

# ==========================================
# 1. Fungsi Bantuan Dasar (The Basics)
# ==========================================

def softmax(x, axis=-1):
    x_shifted = x - np.max(x, axis=axis, keepdims=True)
    exp_x = np.exp(x_shifted)
    return exp_x / np.sum(exp_x, axis=axis, keepdims=True)

def relu(x):
    return np.maximum(0, x)

def create_causal_mask(seq_len):
    mask = np.triu(np.ones((seq_len, seq_len)), k=1).astype('float32')
    mask = mask * -1e9 
    return mask[np.newaxis, np.newaxis, :, :]

# ==========================================
# 2. Komponen Arsitektur (The Bricks)
# ==========================================

class Linear:
    def __init__(self, d_in, d_out):
        self.W = np.random.randn(d_in, d_out) / np.sqrt(d_in)
        self.b = np.zeros((d_out,))

    def forward(self, x):
        return np.dot(x, self.W) + self.b
 
class LayerNormalization:
    def __init__(self, d_model, eps=1e-6):
        self.eps = eps
        self.gamma = np.ones((d_model,))
        self.beta = np.zeros((d_model,))

    def forward(self, x):
        mean = np.mean(x, axis=-1, keepdims=True)
        std = np.std(x, axis=-1, keepdims=True)
        
        x_norm = (x - mean) / (std + self.eps)
        return self.gamma * x_norm + self.beta

class PositionalEncoding:
    def __init__(self, d_model, max_seq_len=500):
        self.PE = np.zeros((max_seq_len, d_model))
        positions = np.arange(max_seq_len)[:, np.newaxis]
        div_term = np.exp(np.arange(0, d_model, 2) * -(np.log(10000.0) / d_model))

        self.PE[:, 0::2] = np.sin(positions * div_term)
        self.PE[:, 1::2] = np.cos(positions * div_term)

        self.PE = self.PE[np.newaxis, :, :] 

    def forward(self, x):
        seq_len = x.shape[1]
        return x + self.PE[:, :seq_len, :]

class FeedForwardNetwork:
    def __init__(self, d_model, d_ff):
        self.linear1 = Linear(d_model, d_ff)
        self.linear2 = Linear(d_ff, d_model)

    def forward(self, x):
        return self.linear2.forward(relu(self.linear1.forward(x)))

# ==========================================
# 3. Jantungnya Transformer: Attention
# ==========================================

class MultiHeadAttention:
    def __init__(self, d_model, num_heads):
        assert d_model % num_heads == 0, "d_model harus habis dibagi num_heads"
        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads

        self.W_q = Linear(d_model, d_model)
        self.W_k = Linear(d_model, d_model)
        self.W_v = Linear(d_model, d_model)
        self.W_o = Linear(d_model, d_model)

    def scaled_dot_product_attention(self, Q, K, V, mask=None):
        matmul_qk = np.matmul(Q, np.swapaxes(K, -1, -2))

        scaled_attention_logits = matmul_qk / np.sqrt(self.d_k)

        if mask is not None:
            scaled_attention_logits += mask

        attention_weights = softmax(scaled_attention_logits, axis=-1)

        output = np.matmul(attention_weights, V)
        return output

    def split_heads(self, x, batch_size):
        x = np.reshape(x, (batch_size, -1, self.num_heads, self.d_k))
        return np.swapaxes(x, 1, 2)

    def concat_heads(self, x, batch_size):
        x = np.swapaxes(x, 1, 2)
        return np.reshape(x, (batch_size, -1, self.d_model))

    def forward(self, query, key, value, mask=None):
        batch_size = query.shape[0]

        Q = self.W_q.forward(query)
        K = self.W_k.forward(key)
        V = self.W_v.forward(value)

        Q = self.split_heads(Q, batch_size)
        K = self.split_heads(K, batch_size)
        V = self.split_heads(V, batch_size)

        attention_output = self.scaled_dot_product_attention(Q, K, V, mask)

        concat_output = self.concat_heads(attention_output, batch_size)

        return self.W_o.forward(concat_output)

# ==========================================
# 4. Encoder & Decoder Blocks (The Layers)
# ==========================================

class EncoderBlock:
    def __init__(self, d_model, num_heads, d_ff):
        self.mha = MultiHeadAttention(d_model, num_heads)
        self.norm1 = LayerNormalization(d_model)
        self.ffn = FeedForwardNetwork(d_model, d_ff)
        self.norm2 = LayerNormalization(d_model)

    def forward(self, x):
        attn_output = self.mha.forward(x, x, x) 
        x = self.norm1.forward(x + attn_output)

        ffn_output = self.ffn.forward(x)
        x = self.norm2.forward(x + ffn_output)
        return x

class DecoderBlock:
    def __init__(self, d_model, num_heads, d_ff):
        self.mha1 = MultiHeadAttention(d_model, num_heads)
        self.norm1 = LayerNormalization(d_model)

        self.mha2 = MultiHeadAttention(d_model, num_heads)
        self.norm2 = LayerNormalization(d_model)

        self.ffn = FeedForwardNetwork(d_model, d_ff)
        self.norm3 = LayerNormalization(d_model)

    def forward(self, x, encoder_output, causal_mask):
        attn1 = self.mha1.forward(x, x, x, mask=causal_mask)
        x = self.norm1.forward(x + attn1)

        attn2 = self.mha2.forward(query=x, key=encoder_output, value=encoder_output)
        x = self.norm2.forward(x + attn2)

        ffn_out = self.ffn.forward(x)
        x = self.norm3.forward(x + ffn_out)
        return x

# ==========================================
# 5. Arsitektur Penuh (The Transformer)
# ==========================================

class Transformer:
    def __init__(self, d_model=512, num_heads=8, N=6, d_ff=2048, 
                 src_vocab_size=1000, tgt_vocab_size=1000, max_seq_len=100):
        
        self.d_model = d_model

        self.src_embedding = Linear(src_vocab_size, d_model)
        self.pos_encoding = PositionalEncoding(d_model, max_seq_len)
        self.encoder_blocks = [EncoderBlock(d_model, num_heads, d_ff) for _ in range(N)]

        self.tgt_embedding = Linear(tgt_vocab_size, d_model)
        self.decoder_blocks = [DecoderBlock(d_model, num_heads, d_ff) for _ in range(N)]

        self.final_linear = Linear(d_model, tgt_vocab_size)

    def encode(self, src_input):
        x = self.src_embedding.forward(src_input) * np.sqrt(self.d_model)
        x = self.pos_encoding.forward(x)

        for block in self.encoder_blocks:
            x = block.forward(x)
        return x

    def decode(self, tgt_input, encoder_output):
        seq_len = tgt_input.shape[1]
        causal_mask = create_causal_mask(seq_len)

        x = self.tgt_embedding.forward(tgt_input) * np.sqrt(self.d_model)
        x = self.pos_encoding.forward(x)

        for block in self.decoder_blocks:
            x = block.forward(x, encoder_output, causal_mask)
        return x

    def forward(self, src_input_one_hot, tgt_input_one_hot):
        encoder_output = self.encode(src_input_one_hot)

        decoder_output = self.decode(tgt_input_one_hot, encoder_output)

        logits = self.final_linear.forward(decoder_output)

        probs = softmax(logits)
        return probs

# ==========================================
# 🚀 DEMO: Menjalankan "Sigma Transformer"
# ==========================================
if __name__ == "__main__":
    print("Menginisialisasi Transformer...")
    d_model = 64
    num_heads = 4
    N_layers = 2
    d_ff = 128
    vocab_size = 50
    seq_len = 10
    batch_size = 2

    transformer = Transformer(d_model=d_model, num_heads=num_heads, N=N_layers, 
                              d_ff=d_ff, src_vocab_size=vocab_size, 
                              tgt_vocab_size=vocab_size, max_seq_len=seq_len)

    print("Arsitektur siap. Membuat data dummy...")

    src_data = np.eye(vocab_size)[np.random.choice(vocab_size, (batch_size, seq_len))]
    tgt_data = np.eye(vocab_size)[np.random.choice(vocab_size, (batch_size, seq_len))]

    print(f"Shape Input Encoder: {src_data.shape}")
    print(f"Shape Input Decoder: {tgt_data.shape}")
    print("\n--- Memulai Forward Pass ---")

    output_probabilities = transformer.forward(src_data, tgt_data)

    print("\n--- Forward Pass Selesai ---")
    print(f"Shape Output Final: {output_probabilities.shape}")
    print("(Batch Size, Sequence Length, Target Vocab Size)")

    print("\nContoh probabilitas output untuk token pertama di batch pertama:")
    print(output_probabilities[0, 0, :10], "... (total sum:", np.sum(output_probabilities[0,0,:]), ")")
    print("\nStatus: Transformer Berhasil Berjalan tanpa Error")