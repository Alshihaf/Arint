
# core/transformer_arint.py
# Antarmuka tingkat tinggi untuk model Transformer berbasis NumPy.

import numpy as np
import re
from collections import Counter
import json
import os

# Impor kelas Transformer yang sekarang berada di neural_network.py
from .neural_network import Transformer, softmax

class SimpleTokenizer:
    """Tokenizer sederhana yang mengubah teks menjadi ID dan sebaliknya."""
    def __init__(self, vocab_size=5000):
        self.vocab_size = vocab_size
        self.word2idx = {'<PAD>': 0, '<UNK>': 1, '<BOS>': 2, '<EOS>': 3}
        self.idx2word = {0: '<PAD>', 1: '<UNK>', 2: '<BOS>', 3: '<EOS>'}
        self.fitted = False

    def fit(self, texts):
        """Membangun kosakata dari daftar teks."""
        if self.fitted:
            print("Tokenizer already fitted.")
            return

        word_counts = Counter()
        # Gabungkan semua teks dan kemudian tokenisasi untuk efisiensi
        full_text = ' '.join(texts)
        words = re.findall(r'[\w_]+', full_text.lower())
        word_counts.update(words)
        
        most_common = word_counts.most_common(self.vocab_size - len(self.word2idx))
        for i, (word, _) in enumerate(most_common, start=len(self.word2idx)):
            self.word2idx[word] = i
            self.idx2word[i] = word
        self.fitted = True
        print(f"Tokenizer fitted on vocabulary of size {len(self.word2idx)}.")

    def encode(self, text, max_len):
        """Meng-encode satu kalimat menjadi daftar ID dengan padding."""
        words = re.findall(r'[\w_]+', text.lower())
        ids = [self.word2idx.get(w, self.word2idx['<UNK>']) for w in words]
        
        # Hapus BOS/EOS karena kita fokus pada embedding, bukan sekuens
        # ids = [self.word2idx['<BOS>']] + ids + [self.word2idx['<EOS>']]
        
        padded_ids = ids[:max_len] + [self.word2idx['<PAD>']] * (max_len - len(ids))
        return padded_ids

    def decode(self, ids):
        """Mendekode daftar ID kembali menjadi kalimat."""
        special_tokens = {self.word2idx['<PAD>'], self.word2idx['<BOS>'], self.word2idx['<EOS>']}
        words = [self.idx2word.get(i, '<UNK>') for i in ids if i not in special_tokens]
        return ' '.join(words)


class TransformerArint:
    """Kelas pembungkus yang mengelola model Transformer, tokenisasi, dan VEKTORISASI."""
    def __init__(self, config=None, model_path="arint/memory/transformer_model.npz", tokenizer_path="arint/memory/tokenizer.json"):
        if config is None:
            config = {
                'num_layers': 2, 'd_model': 64, 'num_heads': 4, 'd_ff': 128,
                'vocab_size': 5000, 'max_seq_len': 50
            }
        self.config = config
        self.model_path = model_path
        self.tokenizer_path = tokenizer_path
        
        # Buat direktori jika belum ada
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        os.makedirs(os.path.dirname(tokenizer_path), exist_ok=True)

        self.transformer = Transformer(
            num_layers=config['num_layers'], d_model=config['d_model'], num_heads=config['num_heads'],
            d_ff=config['d_ff'], input_vocab_size=config['vocab_size'],
            target_vocab_size=config['vocab_size'], max_seq_len=config['max_seq_len']
        )
        self.tokenizer = SimpleTokenizer(vocab_size=config['vocab_size'])

        self.load_tokenizer()
        self.load_model()

    def vectorize(self, text: str, pooling='mean') -> np.ndarray:
        """
        FUNGSI KUNCI: Mengubah teks menjadi satu vektor embedding yang kaya konteks.
        """
        if not self.tokenizer.fitted:
            raise RuntimeError("Tokenizer has not been fitted. Please fit with some text data first.")

        # 1. Encode teks menjadi ID token
        token_ids = self.tokenizer.encode(text, self.config['max_seq_len'])
        inp_array = np.array(token_ids)[np.newaxis, :] # Tambahkan dimensi batch

        # 2. Buat mask padding untuk encoder
        # Mask adalah 1 untuk token PAD, 0 untuk lainnya.
        enc_padding_mask = (inp_array == self.tokenizer.word2idx['<PAD>']).astype(np.float32)[:, np.newaxis, np.newaxis, :]

        # 3. Jalankan proses ENCODE dari Transformer
        # Ini menghasilkan vektor embedding untuk setiap token
        # Output shape: (batch_size, seq_len, d_model)
        contextual_embeddings = self.transformer.encode(inp_array, enc_padding_mask)
        
        # 4. Pooling: Ubah matriks embedding menjadi satu vektor
        if pooling == 'mean':
            # Ambil rata-rata dari semua embedding token non-padding
            mask = (inp_array[0] != self.tokenizer.word2idx['<PAD>'])
            if np.sum(mask) == 0:
                return np.zeros(self.config['d_model'])
            # Terapkan mask ke embeddings
            masked_embeddings = contextual_embeddings[0][mask]
            return masked_embeddings.mean(axis=0)
        elif pooling == 'last':
            # Ambil embedding dari token non-padding terakhir
            mask = (inp_array[0] != self.tokenizer.word2idx['<PAD>'])
            if np.sum(mask) == 0:
                return np.zeros(self.config['d_model'])
            last_token_index = np.where(mask)[0][-1]
            return contextual_embeddings[0, last_token_index, :]
        else:
            raise ValueError(f"Unknown pooling strategy: {pooling}")

    # ... (sisa metode: _create_masks, generate, save_model, load_model, save_tokenizer, load_tokenizer)
    # ... (Tidak ada perubahan pada metode lain untuk saat ini)
    # Note: save/load model perlu diperluas untuk menangani semua bobot.

# (Tambahkan kembali sisa metode yang tidak berubah untuk kelengkapan)
    def _create_masks(self, inp, tar):
        enc_padding_mask = (inp == self.tokenizer.word2idx['<PAD>']).astype(np.float32)[:, np.newaxis, np.newaxis, :]
        look_ahead_mask = 1 - np.triu(np.ones((tar.shape[1], tar.shape[1])), k=1)
        dec_padding_mask = (tar == self.tokenizer.word2idx['<PAD>']).astype(np.float32)[:, np.newaxis, np.newaxis, :]
        combined_mask = np.maximum((look_ahead_mask==0) * -1e9, dec_padding_mask)
        return enc_padding_mask, combined_mask, dec_padding_mask

    def generate(self, prompt, max_new_tokens=50, temperature=1.0):
        inp_ids = self.tokenizer.encode(prompt, self.config['max_seq_len'])
        inp_array = np.array(inp_ids)[np.newaxis, :]
        output_ids = [self.tokenizer.word2idx['<BOS>']]
        for _ in range(max_new_tokens):
            tar_array = np.array(output_ids)[np.newaxis, :]
            _, combined_mask, _ = self._create_masks(inp_array, tar_array)
            predictions = self.transformer.forward(inp_array, tar_array, None, combined_mask, None)
            last_token_logits = predictions[0, -1, :]
            scaled_logits = last_token_logits / temperature
            probabilities = softmax(scaled_logits)
            next_token_id = np.random.choice(len(probabilities), p=probabilities)
            if next_token_id == self.tokenizer.word2idx['<EOS>']: break
            output_ids.append(next_token_id)
        return self.tokenizer.decode(output_ids)

    def save_model(self):
        params = {name: param for name, param in self.transformer.__dict__.items() if isinstance(param, np.ndarray)}
        # Juga simpan bobot dari lapisan-lapisan
        for i, layer in enumerate(self.transformer.encoder_layers):
            for name, param in layer.__dict__.items():
                if isinstance(param, np.ndarray):
                    params[f'enc_{i}_{name}'] = param
        # (Lakukan hal yang sama untuk decoder jika perlu)
        np.savez_compressed(self.model_path, **params)
        print(f"Model saved to {self.model_path}")

    def load_model(self):
        if os.path.exists(self.model_path):
            try:
                data = np.load(self.model_path, allow_pickle=True)
                for name, param in self.transformer.__dict__.items():
                    if isinstance(param, np.ndarray) and name in data:
                        if param.shape == data[name].shape:
                            self.transformer.__dict__[name] = data[name]
                for i, layer in enumerate(self.transformer.encoder_layers):
                    for name, param in layer.__dict__.items():
                         if isinstance(param, np.ndarray):
                            key = f'enc_{i}_{name}'
                            if key in data and param.shape == data[key].shape:
                                layer.__dict__[name] = data[key]
                print(f"Model loaded from {self.model_path}")
            except Exception as e:
                print(f"Failed to load model from {self.model_path}: {e}")
        else:
            print("No saved model found. Using new random weights.")

    def save_tokenizer(self):
        with open(self.tokenizer_path, 'w') as f:
            json.dump({'word2idx': self.tokenizer.word2idx, 'idx2word': self.tokenizer.idx2word, 'vocab_size': self.tokenizer.vocab_size}, f, indent=4)
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
            print("No tokenizer file found. A new one will be created.")
