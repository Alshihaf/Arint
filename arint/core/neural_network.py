# core/neural_network.py
# Berisi implementasi komponen Jaringan Saraf berbasis NumPy, termasuk arsitektur Transformer.

import numpy as np

def softmax(x):
    """Menghitung fungsi softmax untuk baris terakhir dari skor input."""
    # Ambil baris terakhir jika x adalah matriks (untuk efisiensi selama generasi)
    if x.ndim > 1:
        x = x[-1, :]
    
    # Stabilitas numerik dengan mengurangi nilai maksimum
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0)

class LayerNormalization:
    """Implementasi Layer Normalization."""
    def __init__(self, d_model, epsilon=1e-6):
        self.gamma = np.ones(d_model)
        self.beta = np.zeros(d_model)
        self.epsilon = epsilon

    def forward(self, x):
        mean = x.mean(axis=-1, keepdims=True)
        std = x.std(axis=-1, keepdims=True)
        return self.gamma * (x - mean) / (std + self.epsilon) + self.beta

class MultiHeadAttention:
    """Implementasi Multi-Head Attention berbasis NumPy."""
    def __init__(self, d_model, num_heads):
        self.num_heads = num_heads
        self.d_model = d_model
        assert d_model % self.num_heads == 0
        self.depth = d_model // self.num_heads

        # Inisialisasi bobot tunggal untuk Q, K, V untuk efisiensi
        self.wq = np.random.randn(d_model, d_model) * 0.01
        self.wk = np.random.randn(d_model, d_model) * 0.01
        self.wv = np.random.randn(d_model, d_model) * 0.01
        self.dense = np.random.randn(d_model, d_model) * 0.01

    def scaled_dot_product_attention(self, q, k, v, mask):
        matmul_qk = np.matmul(q, k.transpose(0, 1, 3, 2))
        dk = k.shape[-1]
        scaled_attention_logits = matmul_qk / np.sqrt(dk)

        if mask is not None:
            scaled_attention_logits += (mask * -1e9)

        attention_weights = softmax(scaled_attention_logits)
        output = np.matmul(attention_weights, v)
        return output

    def split_heads(self, x, batch_size):
        x = x.reshape(batch_size, -1, self.num_heads, self.depth)
        return x.transpose(0, 2, 1, 3)

    def forward(self, v, k, q, mask):
        batch_size = q.shape[0]

        q = np.dot(q, self.wq)
        k = np.dot(k, self.wk)
        v = np.dot(v, self.wv)

        q = self.split_heads(q, batch_size)
        k = self.split_heads(k, batch_size)
        v = self.split_heads(v, batch_size)

        scaled_attention = self.scaled_dot_product_attention(q, k, v, mask)
        scaled_attention = scaled_attention.transpose(0, 2, 1, 3)
        
        concat_attention = scaled_attention.reshape(batch_size, -1, self.d_model)
        output = np.dot(concat_attention, self.dense)
        return output

class PositionwiseFeedForward:
    """Implementasi Jaringan Feed-Forward Position-wise."""
    def __init__(self, d_model, d_ff):
        self.w1 = np.random.randn(d_model, d_ff) * 0.01
        self.b1 = np.zeros(d_ff)
        self.w2 = np.random.randn(d_ff, d_model) * 0.01
        self.b2 = np.zeros(d_model)

    def forward(self, x):
        x = np.maximum(0, np.dot(x, self.w1) + self.b1) # ReLU
        return np.dot(x, self.w2) + self.b2

class EncoderLayer:
    """Satu lapisan Encoder tunggal."""
    def __init__(self, d_model, num_heads, d_ff):
        self.mha = MultiHeadAttention(d_model, num_heads)
        self.ffn = PositionwiseFeedForward(d_model, d_ff)
        self.layernorm1 = LayerNormalization(d_model)
        self.layernorm2 = LayerNormalization(d_model)

    def forward(self, x, mask):
        attn_output = self.mha.forward(x, x, x, mask)
        out1 = self.layernorm1.forward(x + attn_output)
        ffn_output = self.ffn.forward(out1)
        out2 = self.layernorm2.forward(out1 + ffn_output)
        return out2

class DecoderLayer:
    """Satu lapisan Decoder tunggal."""
    def __init__(self, d_model, num_heads, d_ff):
        self.mha1 = MultiHeadAttention(d_model, num_heads)
        self.mha2 = MultiHeadAttention(d_model, num_heads)
        self.ffn = PositionwiseFeedForward(d_model, d_ff)
        self.layernorm1 = LayerNormalization(d_model)
        self.layernorm2 = LayerNormalization(d_model)
        self.layernorm3 = LayerNormalization(d_model)

    def forward(self, x, enc_output, look_ahead_mask, padding_mask):
        attn1 = self.mha1.forward(x, x, x, look_ahead_mask)
        out1 = self.layernorm1.forward(x + attn1)

        attn2 = self.mha2.forward(enc_output, enc_output, out1, padding_mask)
        out2 = self.layernorm2.forward(out1 + attn2)

        ffn_output = self.ffn.forward(out2)
        out3 = self.layernorm3.forward(out2 + ffn_output)
        return out3

class Transformer:
    """Arsitektur Transformer lengkap berbasis NumPy."""
    def __init__(self, num_layers, d_model, num_heads, d_ff, input_vocab_size, target_vocab_size, max_seq_len):
        self.num_layers = num_layers
        self.d_model = d_model
        
        self.encoder_embedding = np.random.randn(input_vocab_size, d_model) * 0.01
        self.decoder_embedding = np.random.randn(target_vocab_size, d_model) * 0.01
        self.pos_encoding = self.positional_encoding(max_seq_len, d_model)

        self.encoder_layers = [EncoderLayer(d_model, num_heads, d_ff) for _ in range(num_layers)]
        self.decoder_layers = [DecoderLayer(d_model, num_heads, d_ff) for _ in range(num_layers)]

        self.final_layer = np.random.randn(d_model, target_vocab_size) * 0.01

    def positional_encoding(self, position, d_model):
        angle_rads = self.get_angles(np.arange(position)[:, np.newaxis],
                                     np.arange(d_model)[np.newaxis, :],
                                     d_model)
        angle_rads[:, 0::2] = np.sin(angle_rads[:, 0::2])
        angle_rads[:, 1::2] = np.cos(angle_rads[:, 1::2])
        pos_encoding = angle_rads[np.newaxis, ...]
        return pos_encoding.astype(np.float32)

    def get_angles(self, pos, i, d_model):
        angle_rates = 1 / np.power(10000, (2 * (i // 2)) / np.float32(d_model))
        return pos * angle_rates

    def encode(self, x, mask):
        seq_len = x.shape[1]
        x_emb = self.encoder_embedding[x]
        x_emb *= np.sqrt(self.d_model)
        x_emb += self.pos_encoding[:, :seq_len, :]
        
        for i in range(self.num_layers):
            x_emb = self.encoder_layers[i].forward(x_emb, mask)
        return x_emb

    def decode(self, x, enc_output, look_ahead_mask, padding_mask):
        seq_len = x.shape[1]
        x_emb = self.decoder_embedding[x]
        x_emb *= np.sqrt(self.d_model)
        x_emb += self.pos_encoding[:, :seq_len, :]
        
        for i in range(self.num_layers):
            x_emb = self.decoder_layers[i].forward(x_emb, enc_output, look_ahead_mask, padding_mask)
        return x_emb

    def forward(self, inp, tar, enc_padding_mask, look_ahead_mask, dec_padding_mask):
        enc_output = self.encode(inp, enc_padding_mask)
        dec_output = self.decode(tar, enc_output, look_ahead_mask, dec_padding_mask)
        final_output = np.dot(dec_output, self.final_layer)
        return final_output
