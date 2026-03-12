# core/transformer_arint.py
import numpy as np
import re
from collections import Counter
import json
import os

from .neural_network import Transformer, softmax 

class SimpleTokenizer:
    def __init__(self, vocab_size=5000):
        self.vocab_size = vocab_size
        self.word2idx = {'<PAD>': 0, '<UNK>': 1, '<BOS>': 2, '<EOS>': 3}
        self.idx2word = {0: '<PAD>', 1: '<UNK>', 2: '<BOS>', 3: '<EOS>'}
        self.fitted = False

    def fit(self, texts):
        word_counts = Counter()
        for text in texts:
            words = re.findall(r'\w+', text.lower())
            word_counts.update(words)
        most_common = word_counts.most_common(self.vocab_size - 4)
        for i, (word, _) in enumerate(most_common, start=4):
            self.word2idx[word] = i
            self.idx2word[i] = word
        self.fitted = True

    def encode(self, text, max_len=50, add_special=True):
        words = re.findall(r'\w+', text.lower())
        ids = [self.word2idx.get(w, 1) for w in words]
        if add_special:
            ids = [2] + ids[:max_len-2] + [3] 
        else:
            ids = ids[:max_len]
        if len(ids) < max_len:
            ids += [0] * (max_len - len(ids))
        return ids[:max_len]
        
    def encode_raw(self, text, add_special=True):
        words = re.findall(r'\w+', text.lower())
        ids = [self.word2idx.get(w, 1) for w in words]
        if add_special:
            ids = [2] + ids + [3]
        return ids

    def decode(self, ids, skip_special=True):
        words = []
        for i in ids:
            if i == 0 and skip_special:
                continue
            if i in self.idx2word:
                word = self.idx2word[i]
                if skip_special and word.startswith('<') and word.endswith('>'):
                    continue
                words.append(word)
            else:
                words.append('<UNK>')
        return ' '.join(words)


class TransformerArint:
    def __init__(self, config=None):
        if config is None:
            config = {
                'd_model': 64,
                'num_heads': 4,
                'N': 2,
                'd_ff': 128,
                'vocab_size': 5000,
                'max_seq_len': 50
            }
        self.config = config
        self.d_model = config['d_model']
        self.vocab_size = config['vocab_size']
        self.max_seq_len = config['max_seq_len']

        # Inisialisasi transformer
        self.transformer = Transformer(
            d_model=config['d_model'],
            num_heads=config['num_heads'],
            N=config['N'],
            d_ff=config['d_ff'],
            src_vocab_size=config['vocab_size'],
            tgt_vocab_size=config['vocab_size'],
            max_seq_len=config['max_seq_len']
        )

        self.tokenizer = SimpleTokenizer(vocab_size=config['vocab_size'])

        self.model_path = "memory/transformer_params.npz"
        self.tokenizer_path = "memory/tokenizer.json"

        self.load()

    def fit_tokenizer(self, texts):
        self.tokenizer.fit(texts)
        self.save_tokenizer()

    def encode_text(self, text):
        ids = self.tokenizer.encode(text, max_len=self.max_seq_len)
        one_hot = np.eye(self.vocab_size)[ids]
        return one_hot[np.newaxis, :, :]
        
    def _ids_to_onehot(self, ids):
        one_hot = np.eye(self.vocab_size)[ids]
        return one_hot[np.newaxis, :, :]

    def decode_output(self, probs):
        ids = np.argmax(probs, axis=-1)
        return self.tokenizer.decode(ids[0])

    def encode_sentence(self, text):
        src_one_hot = self.encode_text(text)
        encoder_output = self.transformer.encode(src_one_hot)
        sent_vec = np.mean(encoder_output, axis=1)
        return sent_vec.flatten()

    def generate(self, prompt, max_new_tokens=20):
        prompt_ids = self.tokenizer.encode_raw(prompt, add_special=True)

        if len(prompt_ids) > self.max_seq_len - 1:
            prompt_ids = prompt_ids[:self.max_seq_len - 1]
        generated = prompt_ids[:]
        max_len = self.max_seq_len

        for _ in range(max_new_tokens):
            if len(generated) >= max_len:
                break

            tgt_one_hot = self._ids_to_onehot(generated)
            src_one_hot = self._ids_to_onehot(prompt_ids)
            probs = self.transformer.forward(src_one_hot, tgt_one_hot)
            last_token_probs = probs[0, -1, :]
            next_token = np.random.choice(len(last_token_probs), p=last_token_probs)
            generated.append(next_token)
            if next_token == 3:
                break
              
        if len(generated) > max_len:
            generated = generated[:max_len]

        return self.tokenizer.decode(generated)

    def save(self):
        params = {}
        t = self.transformer

        params['src_embedding_W'] = t.src_embedding.W
        params['src_embedding_b'] = t.src_embedding.b

        params['tgt_embedding_W'] = t.tgt_embedding.W
        params['tgt_embedding_b'] = t.tgt_embedding.b

        params['final_linear_W'] = t.final_linear.W
        params['final_linear_b'] = t.final_linear.b

        for i, block in enumerate(t.encoder_blocks):
            mha = block.mha
            params[f'enc{i}_mha_W_q'] = mha.W_q.W
            params[f'enc{i}_mha_b_q'] = mha.W_q.b
            params[f'enc{i}_mha_W_k'] = mha.W_k.W
            params[f'enc{i}_mha_b_k'] = mha.W_k.b
            params[f'enc{i}_mha_W_v'] = mha.W_v.W
            params[f'enc{i}_mha_b_v'] = mha.W_v.b
            params[f'enc{i}_mha_W_o'] = mha.W_o.W
            params[f'enc{i}_mha_b_o'] = mha.W_o.b

            params[f'enc{i}_norm1_gamma'] = block.norm1.gamma
            params[f'enc{i}_norm1_beta'] = block.norm1.beta

            params[f'enc{i}_ffn_lin1_W'] = block.ffn.linear1.W
            params[f'enc{i}_ffn_lin1_b'] = block.ffn.linear1.b
            params[f'enc{i}_ffn_lin2_W'] = block.ffn.linear2.W
            params[f'enc{i}_ffn_lin2_b'] = block.ffn.linear2.b

            params[f'enc{i}_norm2_gamma'] = block.norm2.gamma
            params[f'enc{i}_norm2_beta'] = block.norm2.beta

        for i, block in enumerate(t.decoder_blocks):
            mha1 = block.mha1
            params[f'dec{i}_mha1_W_q'] = mha1.W_q.W
            params[f'dec{i}_mha1_b_q'] = mha1.W_q.b
            params[f'dec{i}_mha1_W_k'] = mha1.W_k.W
            params[f'dec{i}_mha1_b_k'] = mha1.W_k.b
            params[f'dec{i}_mha1_W_v'] = mha1.W_v.W
            params[f'dec{i}_mha1_b_v'] = mha1.W_v.b
            params[f'dec{i}_mha1_W_o'] = mha1.W_o.W
            params[f'dec{i}_mha1_b_o'] = mha1.W_o.b

            params[f'dec{i}_norm1_gamma'] = block.norm1.gamma
            params[f'dec{i}_norm1_beta'] = block.norm1.beta

            mha2 = block.mha2
            params[f'dec{i}_mha2_W_q'] = mha2.W_q.W
            params[f'dec{i}_mha2_b_q'] = mha2.W_q.b
            params[f'dec{i}_mha2_W_k'] = mha2.W_k.W
            params[f'dec{i}_mha2_b_k'] = mha2.W_k.b
            params[f'dec{i}_mha2_W_v'] = mha2.W_v.W
            params[f'dec{i}_mha2_b_v'] = mha2.W_v.b
            params[f'dec{i}_mha2_W_o'] = mha2.W_o.W
            params[f'dec{i}_mha2_b_o'] = mha2.W_o.b
  
            params[f'dec{i}_norm2_gamma'] = block.norm2.gamma
            params[f'dec{i}_norm2_beta'] = block.norm2.beta

            params[f'dec{i}_ffn_lin1_W'] = block.ffn.linear1.W
            params[f'dec{i}_ffn_lin1_b'] = block.ffn.linear1.b
            params[f'dec{i}_ffn_lin2_W'] = block.ffn.linear2.W
            params[f'dec{i}_ffn_lin2_b'] = block.ffn.linear2.b

            params[f'dec{i}_norm3_gamma'] = block.norm3.gamma
            params[f'dec{i}_norm3_beta'] = block.norm3.beta

        np.savez_compressed(self.model_path, **params)
        print(f"Transformer model saved to {self.model_path}")

    def load(self):
        if not os.path.exists(self.model_path):
            print("No saved model found, using random init.")
            return
        data = np.load(self.model_path)
        t = self.transformer

        t.src_embedding.W = data['src_embedding_W']
        t.src_embedding.b = data['src_embedding_b']
        t.tgt_embedding.W = data['tgt_embedding_W']
        t.tgt_embedding.b = data['tgt_embedding_b']
        t.final_linear.W = data['final_linear_W']
        t.final_linear.b = data['final_linear_b']

        for i, block in enumerate(t.encoder_blocks):
            block.mha.W_q.W = data[f'enc{i}_mha_W_q']
            block.mha.W_q.b = data[f'enc{i}_mha_b_q']
            block.mha.W_k.W = data[f'enc{i}_mha_W_k']
            block.mha.W_k.b = data[f'enc{i}_mha_b_k']
            block.mha.W_v.W = data[f'enc{i}_mha_W_v']
            block.mha.W_v.b = data[f'enc{i}_mha_b_v']
            block.mha.W_o.W = data[f'enc{i}_mha_W_o']
            block.mha.W_o.b = data[f'enc{i}_mha_b_o']

            block.norm1.gamma = data[f'enc{i}_norm1_gamma']
            block.norm1.beta = data[f'enc{i}_norm1_beta']

            block.ffn.linear1.W = data[f'enc{i}_ffn_lin1_W']
            block.ffn.linear1.b = data[f'enc{i}_ffn_lin1_b']
            block.ffn.linear2.W = data[f'enc{i}_ffn_lin2_W']
            block.ffn.linear2.b = data[f'enc{i}_ffn_lin2_b']

            block.norm2.gamma = data[f'enc{i}_norm2_gamma']
            block.norm2.beta = data[f'enc{i}_norm2_beta']

        for i, block in enumerate(t.decoder_blocks):
            block.mha1.W_q.W = data[f'dec{i}_mha1_W_q']
            block.mha1.W_q.b = data[f'dec{i}_mha1_b_q']
            block.mha1.W_k.W = data[f'dec{i}_mha1_W_k']
            block.mha1.W_k.b = data[f'dec{i}_mha1_b_k']
            block.mha1.W_v.W = data[f'dec{i}_mha1_W_v']
            block.mha1.W_v.b = data[f'dec{i}_mha1_b_v']
            block.mha1.W_o.W = data[f'dec{i}_mha1_W_o']
            block.mha1.W_o.b = data[f'dec{i}_mha1_b_o']

            block.norm1.gamma = data[f'dec{i}_norm1_gamma']
            block.norm1.beta = data[f'dec{i}_norm1_beta']

            block.mha2.W_q.W = data[f'dec{i}_mha2_W_q']
            block.mha2.W_q.b = data[f'dec{i}_mha2_b_q']
            block.mha2.W_k.W = data[f'dec{i}_mha2_W_k']
            block.mha2.W_k.b = data[f'dec{i}_mha2_b_k']
            block.mha2.W_v.W = data[f'dec{i}_mha2_W_v']
            block.mha2.W_v.b = data[f'dec{i}_mha2_b_v']
            block.mha2.W_o.W = data[f'dec{i}_mha2_W_o']
            block.mha2.W_o.b = data[f'dec{i}_mha2_b_o']

            block.norm2.gamma = data[f'dec{i}_norm2_gamma']
            block.norm2.beta = data[f'dec{i}_norm2_beta']

            block.ffn.linear1.W = data[f'dec{i}_ffn_lin1_W']
            block.ffn.linear1.b = data[f'dec{i}_ffn_lin1_b']
            block.ffn.linear2.W = data[f'dec{i}_ffn_lin2_W']
            block.ffn.linear2.b = data[f'dec{i}_ffn_lin2_b']

            block.norm3.gamma = data[f'dec{i}_norm3_gamma']
            block.norm3.beta = data[f'dec{i}_norm3_beta']

        print(f"Transformer model loaded from {self.model_path}")
    
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
            print("No tokenizer file found, using random init.")
            
    def save_tokenizer(self):
        with open(self.tokenizer_path, 'w') as f:
            json.dump({
                'word2idx' : self.tokenizer.word2idx,
                'idx2word' : {str(k): v for k, v in self.tokenizer.idx2word.items()},
                'vocab_size' : self.tokenizer.vocab_size
            }, f)