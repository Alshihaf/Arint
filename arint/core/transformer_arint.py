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
        # Token khusus dasar
        self.word2idx = {'<PAD>': 0, '<UNK>': 1, '<BOS>': 2, '<EOS>': 3}
        self.idx2word = {0: '<PAD>', 1: '<UNK>', 2: '<BOS>', 3: '<EOS>'}
        self.fitted = False

    def fit(self, texts):
        """Membangun kosakata dari daftar teks."""
        word_counts = Counter()
        for text in texts:
            words = re.findall(r'\w+', text.lower())
            word_counts.update(words)
        
        # Ambil kata-kata yang paling umum, sisakan ruang untuk token khusus
        most_common = word_counts.most_common(self.vocab_size - len(self.word2idx))
        for i, (word, _) in enumerate(most_common, start=len(self.word2idx)):
            self.word2idx[word] = i
            self.idx2word[i] = word
        self.fitted = True

    def encode(self, text, max_len):
        """Meng-encode satu kalimat menjadi daftar ID dengan padding."""
        words = re.findall(r'\w+', text.lower())
        ids = [self.word2idx.get(w, self.word2idx['<UNK>']) for w in words]
        
        # Tambahkan token BOS dan EOS
        ids = [self.word2idx['<BOS>']] + ids + [self.word2idx['<EOS>']]
        
        # Terapkan padding atau pemotongan
        padded_ids = ids[:max_len] + [self.word2idx['<PAD>']] * (max_len - len(ids))
        return padded_ids

    def decode(self, ids):
        """Mendekode daftar ID kembali menjadi kalimat."""
        special_tokens = {self.word2idx['<PAD>'], self.word2idx['<BOS>'], self.word2idx['<EOS>']}
        words = [self.idx2word.get(i, '<UNK>') for i in ids if i not in special_tokens]
        return ' '.join(words)


class TransformerArint:
    """Kelas pembungkus yang mengelola model Transformer dan tokenisasi."""
    def __init__(self, config=None, model_path="memory/transformer_model.npz", tokenizer_path="memory/tokenizer.json"):
        if config is None:
            # Konfigurasi default jika tidak ada yang disediakan
            config = {
                'num_layers': 2,
                'd_model': 64,
                'num_heads': 4,
                'd_ff': 128,
                'vocab_size': 5000,
                'max_seq_len': 50
            }
        self.config = config
        self.model_path = model_path
        self.tokenizer_path = tokenizer_path

        # Inisialisasi model Transformer dan Tokenizer
        self.transformer = Transformer(
            num_layers=config['num_layers'],
            d_model=config['d_model'],
            num_heads=config['num_heads'],
            d_ff=config['d_ff'],
            input_vocab_size=config['vocab_size'],
            target_vocab_size=config['vocab_size'],
            max_seq_len=config['max_seq_len']
        )
        self.tokenizer = SimpleTokenizer(vocab_size=config['vocab_size'])

        # Coba muat model dan tokenizer yang ada saat inisialisasi
        self.load_tokenizer()
        self.load_model()

    def _create_masks(self, inp, tar):
        # Mask padding Encoder: Mask token <PAD> di input
        enc_padding_mask = (inp == self.tokenizer.word2idx['<PAD>']).astype(np.float32)[:, np.newaxis, np.newaxis, :]

        # Mask look-ahead Decoder: Mencegah posisi memperhatikan posisi berikutnya
        look_ahead_mask = 1 - np.triu(np.ones((tar.shape[1], tar.shape[1])), k=1)
        look_ahead_mask = look_ahead_mask[np.newaxis, np.newaxis, :, :]

        # Mask padding Decoder: Mask token <PAD> di target
        dec_padding_mask = (tar == self.tokenizer.word2idx['<PAD>']).astype(np.float32)[:, np.newaxis, np.newaxis, :]
        
        # Gabungkan mask look-ahead dengan mask padding untuk target
        combined_mask = np.maximum(dec_padding_mask, (1 - look_ahead_mask) * -1e9)

        return enc_padding_mask, combined_mask, dec_padding_mask

    def generate(self, prompt, max_new_tokens=50, temperature=1.0):
        """Menghasilkan teks dari prompt menggunakan model.

        Args:
            prompt (str): Teks input untuk memulai generasi.
            max_new_tokens (int): Jumlah maksimum token baru untuk dihasilkan.
            temperature (float): Mengontrol keacakan. Nilai lebih tinggi berarti lebih acak.
        """
        inp_ids = self.tokenizer.encode(prompt, self.config['max_seq_len'])
        inp_array = np.array(inp_ids)[np.newaxis, :] # Buat dimensi batch

        # Urutan output dimulai dengan token <BOS>
        output_ids = [self.tokenizer.word2idx['<BOS>']]

        for _ in range(max_new_tokens):
            tar_array = np.array(output_ids)[np.newaxis, :] 

            # Buat mask yang sesuai untuk forward pass
            _, combined_mask, _ = self._create_masks(inp_array, tar_array)

            # Dapatkan prediksi dari Transformer
            predictions = self.transformer.forward(inp_array, tar_array, None, combined_mask, None)
            
            # Ambil probabilitas untuk token terakhir dan terapkan suhu
            last_token_logits = predictions[0, -1, :]
            scaled_logits = last_token_logits / temperature
            probabilities = softmax(scaled_logits)

            # Ambil sampel token dari distribusi probabilitas
            next_token_id = np.random.choice(len(probabilities), p=probabilities)

            # Hentikan jika token <EOS> dihasilkan
            if next_token_id == self.tokenizer.word2idx['<EOS>']:
                break

            output_ids.append(next_token_id)

        return self.tokenizer.decode(output_ids)

    def save_model(self):
        """Menyimpan semua bobot model Transformer ke file .npz."""
        # Implementasi ini perlu diperluas untuk menyimpan semua bobot
        # Placeholder untuk menunjukkan fungsionalitas
        np.savez_compressed(self.model_path, final_layer=self.transformer.final_layer)
        print(f"Model (placeholder) saved to {self.model_path}")

    def load_model(self):
        """Memuat bobot model dari file .npz jika ada."""
        if os.path.exists(self.model_path):
            try:
                data = np.load(self.model_path)
                # Contoh memuat satu set bobot
                if 'final_layer' in data and data['final_layer'].shape == self.transformer.final_layer.shape:
                    self.transformer.final_layer = data['final_layer']
                print(f"Model (placeholder) loaded from {self.model_path}")
            except Exception as e:
                print(f"Failed to load model from {self.model_path}: {e}")
        else:
            print("No saved model found. Using new random weights.")

    def save_tokenizer(self):
        """Menyimpan kosakata tokenizer ke file JSON."""
        with open(self.tokenizer_path, 'w') as f:
            json.dump({
                'word2idx': self.tokenizer.word2idx,
                'idx2word': self.tokenizer.idx2word,
                'vocab_size': self.tokenizer.vocab_size
            }, f, indent=4)
        print(f"Tokenizer saved to {self.tokenizer_path}")

    def load_tokenizer(self):
        """Memuat kosakata tokenizer dari file JSON jika ada."""
        if os.path.exists(self.tokenizer_path):
            with open(self.tokenizer_path, 'r') as f:
                data = json.load(f)
                self.tokenizer.word2idx = data['word2idx']
                # Pastikan kunci untuk idx2word adalah integer
                self.tokenizer.idx2word = {int(k): v for k, v in data['idx2word'].items()}
                self.tokenizer.vocab_size = data['vocab_size']
                self.tokenizer.fitted = True
            print(f"Tokenizer loaded from {self.tokenizer_path}")
        else:
            print("No tokenizer file found. A new one will be created if training data is provided.")
