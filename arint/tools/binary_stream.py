# tools/binary_stream
import numpy as np
from collections import Counter
from typing import List, Dict, Tuple


# =============================================================
#  LAYER 0 — RAW PROCESSING & SEGMENTATION
# =============================================================

class Layer0_RawProcessor:

    def __init__(self, chunk_size_bits: int = 128):
        self.chunk_size = chunk_size_bits

    def bytes_to_bits(self, data: bytes) -> np.ndarray:
        byte_array = np.frombuffer(data, dtype=np.uint8)
        bits = np.unpackbits(byte_array)
        return bits

    def bits_to_bytes_value(self, bits: np.ndarray) -> np.ndarray:
        n_bytes = len(bits) // 8
        trimmed = bits[:n_bytes * 8].reshape(-1, 8)
        powers = np.array([128, 64, 32, 16, 8, 4, 2, 1], dtype=np.uint8)
        return trimmed @ powers

    def segment(self, bits: np.ndarray) -> List[np.ndarray]:
        n_full_chunks = len(bits) // self.chunk_size
        chunks = []
        for i in range(n_full_chunks):
            start = i * self.chunk_size
            end = start + self.chunk_size
            chunks.append(bits[start:end])
        return chunks


# =============================================================
#  LAYER 1 — STATISTICAL FEATURE EXTRACTION
# =============================================================

class Layer1_StatisticalAnalyzer:

    FEATURE_NAMES = [
        'bit_entropy', 'balance',
        'run_mean', 'run_std', 'run_max', 'run_count',
        'zero_run_mean', 'one_run_mean',
        'P(0→0)', 'P(0→1)', 'P(1→0)', 'P(1→1)',
        'autocorrelation'
    ]
    N_FEATURES = 13

    @staticmethod
    def entropy(data: np.ndarray) -> float:
        if len(data) == 0:
            return 0.0
        _, counts = np.unique(data, return_counts=True)
        probs = counts / counts.sum()
        return float(-np.sum(probs * np.log2(probs + 1e-12)))

    @staticmethod
    def run_length_stats(bits: np.ndarray) -> Dict[str, float]:
        if len(bits) == 0:
            return dict(mean=0, std=0, max_len=0, count=0,
                        zero_mean=0, one_mean=0)

        changes = np.where(np.diff(bits) != 0)[0] + 1
        segments = np.split(bits, changes)

        lengths = np.array([len(s) for s in segments], dtype=float)
        values = np.array([s[0] for s in segments])

        zero_lengths = lengths[values == 0]
        one_lengths = lengths[values == 1]

        return {
            'mean':      float(lengths.mean()),
            'std':       float(lengths.std()),
            'max_len':   float(lengths.max()),
            'count':     float(len(lengths)),
            'zero_mean': float(zero_lengths.mean()) if len(zero_lengths) > 0 else 0.0,
            'one_mean':  float(one_lengths.mean()) if len(one_lengths) > 0 else 0.0,
        }

    @staticmethod
    def transition_matrix(bits: np.ndarray) -> np.ndarray:
        matrix = np.zeros((2, 2))
        if len(bits) < 2:
            return matrix

        froms = bits[:-1]
        tos = bits[1:]
        for f in range(2):
            for t in range(2):
                matrix[f, t] = np.sum((froms == f) & (tos == t))

        total = matrix.sum()
        if total > 0:
            matrix /= total
        return matrix

    @staticmethod
    def autocorrelation_lag1(bits: np.ndarray) -> float:
        if len(bits) < 2:
            return 0.0
        x = bits.astype(float)
        mu = x.mean()
        var = x.var()
        if var < 1e-12:
            return 0.0
        return float(np.sum((x[:-1] - mu) * (x[1:] - mu)) / (len(x) * var))

    def extract_features(self, chunk: np.ndarray) -> np.ndarray:
        ent = self.entropy(chunk)
        balance = float(chunk.mean())
        rl = self.run_length_stats(chunk)
        tm = self.transition_matrix(chunk)
        ac = self.autocorrelation_lag1(chunk)

        return np.array([
            ent,
            balance,
            rl['mean'],
            rl['std'],
            rl['max_len'],
            rl['count'],
            rl['zero_mean'],
            rl['one_mean'],
            tm[0, 0],
            tm[0, 1],
            tm[1, 0],
            tm[1, 1],
            ac,
        ], dtype=np.float64)

    def extract_batch(self, chunks: List[np.ndarray]) -> np.ndarray:
        return np.array([self.extract_features(c) for c in chunks])


# =============================================================
#  LAYER 2 — LATENT ENCODER (NUMPY AUTOENCODER)
# =============================================================

class Layer2_LatentEncoder:

    def __init__(self,
                 input_dim: int,
                 hidden_dims: List[int] = None,
                 learning_rate: float = 0.005,
                 momentum: float = 0.9):

        if hidden_dims is None:
            hidden_dims = [10, 6, 3]

        self.lr = learning_rate
        self.momentum = momentum
        self.mean = None
        self.std = None
        self.trained = False

        enc_dims = [input_dim] + hidden_dims
        self.enc_W = []
        self.enc_b = []
        self.enc_vW = []
        self.enc_vb = []
        for i in range(len(enc_dims) - 1):
            fan_in, fan_out = enc_dims[i], enc_dims[i + 1]
            w = np.random.randn(fan_in, fan_out) * np.sqrt(2.0 / fan_in)
            self.enc_W.append(w)
            self.enc_b.append(np.zeros(fan_out))
            self.enc_vW.append(np.zeros_like(w))
            self.enc_vb.append(np.zeros(fan_out))

        dec_dims = list(reversed(hidden_dims)) + [input_dim]
        self.dec_W = []
        self.dec_b = []
        self.dec_vW = []
        self.dec_vb = []
        for i in range(len(dec_dims) - 1):
            fan_in, fan_out = dec_dims[i], dec_dims[i + 1]
            w = np.random.randn(fan_in, fan_out) * np.sqrt(2.0 / fan_in)
            self.dec_W.append(w)
            self.dec_b.append(np.zeros(fan_out))
            self.dec_vW.append(np.zeros_like(w))
            self.dec_vb.append(np.zeros(fan_out))

        self.latent_dim = hidden_dims[-1]

    @staticmethod
    def _relu(x):
        return np.maximum(0, x)

    @staticmethod
    def _relu_grad(x):
        return (x > 0).astype(np.float64)

    def _forward(self, x: np.ndarray):
        enc_z = []
        enc_a = [x]
        h = x
        for W, b in zip(self.enc_W, self.enc_b):
            z = h @ W + b
            enc_z.append(z)
            h = self._relu(z)
            enc_a.append(h)
        latent = h

        dec_z = []
        dec_a = [latent]
        h = latent
        for i, (W, b) in enumerate(zip(self.dec_W, self.dec_b)):
            z = h @ W + b
            dec_z.append(z)
            if i < len(self.dec_W) - 1:
                h = self._relu(z)
            else:
                h = z
            dec_a.append(h)

        cache = (enc_z, enc_a, dec_z, dec_a)
        return h, cache, latent

    def _backward(self, x: np.ndarray, reconstruction: np.ndarray, cache):
        enc_z, enc_a, dec_z, dec_a = cache
        batch_size = x.shape[0]

        delta = 2.0 * (reconstruction - x) / batch_size

        dec_gW = []
        dec_gb = []
        for i in reversed(range(len(self.dec_W))):
            if i < len(self.dec_W) - 1:
                delta = delta * self._relu_grad(dec_z[i])

            gW = dec_a[i].T @ delta
            gb = delta.sum(axis=0)
            dec_gW.insert(0, gW)
            dec_gb.insert(0, gb)

            delta = delta @ self.dec_W[i].T

        enc_gW = []
        enc_gb = []
        for i in reversed(range(len(self.enc_W))):
            delta = delta * self._relu_grad(enc_z[i])

            gW = enc_a[i].T @ delta
            gb = delta.sum(axis=0)
            enc_gW.insert(0, gW)
            enc_gb.insert(0, gb)

            delta = delta @ self.enc_W[i].T

        return enc_gW, enc_gb, dec_gW, dec_gb

    def _update(self, enc_gW, enc_gb, dec_gW, dec_gb):
        for i in range(len(self.enc_W)):
            self.enc_vW[i] = self.momentum * self.enc_vW[i] - self.lr * enc_gW[i]
            self.enc_vb[i] = self.momentum * self.enc_vb[i] - self.lr * enc_gb[i]
            self.enc_W[i] += self.enc_vW[i]
            self.enc_b[i] += self.enc_vb[i]

        for i in range(len(self.dec_W)):
            self.dec_vW[i] = self.momentum * self.dec_vW[i] - self.lr * dec_gW[i]
            self.dec_vb[i] = self.momentum * self.dec_vb[i] - self.lr * dec_gb[i]
            self.dec_W[i] += self.dec_vW[i]
            self.dec_b[i] += self.dec_vb[i]

    def fit(self, data: np.ndarray,
            epochs: int = 200,
            batch_size: int = 32) -> List[float]:
        self.mean = data.mean(axis=0)
        self.std = data.std(axis=0) + 1e-8
        X = (data - self.mean) / self.std

        n = len(X)
        losses = []

        for epoch in range(epochs):
            perm = np.random.permutation(n)
            epoch_loss = 0.0
            n_batches = 0

            for start in range(0, n, batch_size):
                batch = X[perm[start:start + batch_size]]
                if len(batch) == 0:
                    continue

                recon, cache, _ = self._forward(batch)
                loss = np.mean((recon - batch) ** 2)

                grads = self._backward(batch, recon, cache)
                self._update(*grads)

                epoch_loss += loss
                n_batches += 1

            avg_loss = epoch_loss / max(n_batches, 1)
            losses.append(avg_loss)

        self.trained = True
        return losses

    def encode(self, data: np.ndarray) -> np.ndarray:
        X = (data - self.mean) / self.std
        h = X
        for W, b in zip(self.enc_W, self.enc_b):
            h = self._relu(h @ W + b)
        return h

    def reconstruction_error(self, data: np.ndarray) -> np.ndarray:
        X = (data - self.mean) / self.std
        recon, _, _ = self._forward(X)
        return np.mean((recon - X) ** 2, axis=1)


# =============================================================
#  LAYER 3 — SYMBOLIC ABSTRACTION
# =============================================================

class Layer3_SymbolicAbstractor:

    GLYPHS = '●◆■▲◀▶★◉⬟⬡⯃⯂⬢⬣'

    def __init__(self, n_symbols: int = 6):
        self.n_symbols = n_symbols
        self.centroids = None
        self.labels = {}

    def _kmeans_pp(self, data: np.ndarray,
                   max_iter: int = 200) -> Tuple[np.ndarray, np.ndarray]:
        n, d = data.shape
        k = min(self.n_symbols, n)

        centroids = np.empty((k, d))
        centroids[0] = data[np.random.randint(n)]

        for c in range(1, k):
            dists = np.min([
                np.sum((data - centroids[j]) ** 2, axis=1)
                for j in range(c)
            ], axis=0)
            probs = dists / (dists.sum() + 1e-12)
            centroids[c] = data[np.random.choice(n, p=probs)]

        for _ in range(max_iter):
            dist_matrix = np.array([
                np.sum((data - c) ** 2, axis=1) for c in centroids
            ]).T  # (n, k)
            assignments = np.argmin(dist_matrix, axis=1)

            new_centroids = np.empty_like(centroids)
            for c in range(k):
                members = data[assignments == c]
                if len(members) > 0:
                    new_centroids[c] = members.mean(axis=0)
                else:
                    new_centroids[c] = centroids[c]

            if np.allclose(centroids, new_centroids, atol=1e-8):
                break
            centroids = new_centroids

        self.centroids = centroids
        self.n_symbols = k
        return assignments, centroids

    def _auto_label(self, cluster_id: int,
                    avg_features: np.ndarray) -> str:
        entropy = avg_features[0]
        balance = avg_features[1]
        run_mean = avg_features[2]

        parts = []

        if entropy < 0.4:
            parts.append("LOW-ENT")
        elif entropy < 0.85:
            parts.append("MID-ENT")
        else:
            parts.append("HI-ENT")

        if balance < 0.2:
            parts.append("ZERO-DOM")
        elif balance > 0.8:
            parts.append("ONE-DOM")
        else:
            parts.append("BALANCED")

        if run_mean > 8:
            parts.append("BLOCK")
        elif run_mean < 1.8:
            parts.append("TOGGLE")
        else:
            parts.append("MIXED")

        return f"{self.GLYPHS[cluster_id % len(self.GLYPHS)]} {'|'.join(parts)}"

    def fit(self, latent: np.ndarray,
            features: np.ndarray) -> np.ndarray:
        assignments, _ = self._kmeans_pp(latent)

        for k in range(self.n_symbols):
            mask = assignments == k
            if mask.sum() > 0:
                avg_feat = features[mask].mean(axis=0)
                self.labels[k] = self._auto_label(k, avg_feat)
            else:
                self.labels[k] = f"SYM_{k}"

        return assignments

    def symbolize(self, latent: np.ndarray) -> List[Dict]:
        results = []
        for vec in latent:
            dists = np.array([np.sum((vec - c) ** 2) for c in self.centroids])
            sym_id = int(np.argmin(dists))
            sorted_d = np.sort(dists)
            if len(sorted_d) > 1 and sorted_d[1] > 1e-12:
                confidence = float(np.clip(
                    1.0 - sorted_d[0] / sorted_d[1], 0, 1
                ))
            else:
                confidence = 1.0

            results.append({
                'id':         sym_id,
                'label':      self.labels.get(sym_id, f'SYM_{sym_id}'),
                'confidence': confidence,
                'glyph':      self.GLYPHS[sym_id % len(self.GLYPHS)],
            })
        return results

    def analyze_sequence(self, assignments: np.ndarray) -> Dict:
        seq = assignments.tolist()

        bigrams = Counter(zip(seq[:-1], seq[1:]))
        trigrams = Counter(zip(seq[:-2], seq[1:-1], seq[2:]))

        if bigrams:
            total = sum(bigrams.values())
            probs = np.array(list(bigrams.values())) / total
            trans_entropy = float(-np.sum(probs * np.log2(probs + 1e-12)))
        else:
            trans_entropy = 0.0

        best_period = None
        best_score = 0.0
        periodicities = {}
        max_period = min(len(seq) // 3, 30)

        for p in range(2, max_period + 1):
            matches = sum(1 for i in range(len(seq) - p) if seq[i] == seq[i + p])
            total = len(seq) - p
            if total > 0:
                score = matches / total
                periodicities[p] = score
                if score > best_score:
                    best_score = score
                    best_period = p

        return {
            'bigrams':           dict(bigrams.most_common(10)),
            'trigrams':          dict(trigrams.most_common(5)),
            'transition_entropy': trans_entropy,
            'best_period':       best_period,
            'best_period_score': best_score,
            'periodicities':     periodicities,
        }


# =============================================================
#  MAIN PIPELINE — AUXILIARY PERCEPTION CHANNEL
# =============================================================

class AuxiliaryPerceptionChannel:

    def __init__(self,
                 chunk_size_bits: int = 128,
                 hidden_dims: List[int] = None,
                 n_symbols: int = 6,
                 anomaly_zscore: float = 2.0):

        if hidden_dims is None:
            hidden_dims = [10, 6, 3]

        self.layer0 = Layer0_RawProcessor(chunk_size_bits)
        self.layer1 = Layer1_StatisticalAnalyzer()
        self.layer2 = Layer2_LatentEncoder(
            input_dim=Layer1_StatisticalAnalyzer.N_FEATURES,
            hidden_dims=hidden_dims,
        )
        self.layer3 = Layer3_SymbolicAbstractor(n_symbols)
        self.anomaly_z = anomaly_zscore

    def _detect_anomalies(self, recon_err: np.ndarray) -> List[Tuple[int, float]]:
        mean_err = recon_err.mean()
        std_err = recon_err.std() + 1e-8
        z_scores = (recon_err - mean_err) / std_err
        anomalies = []
        for i, z in enumerate(z_scores):
            if abs(z) > self.anomaly_z:
                anomalies.append((i, float(z)))
        return anomalies

    def process(self, binary_data: bytes,
                train_epochs: int = 200) -> Dict:
        bits = self.layer0.bytes_to_bits(binary_data)
        chunks = self.layer0.segment(bits)

        if len(chunks) < 3:
            raise ValueError(
                f"Data terlalu kecil. Minimal butuh 3 chunk "
                f"({3 * self.layer0.chunk_size // 8} bytes)."
            )

        features = self.layer1.extract_batch(chunks)

        losses = self.layer2.fit(
            features, epochs=train_epochs,
            batch_size=min(32, len(features))
        )
        latent = self.layer2.encode(features)
        recon_err = self.layer2.reconstruction_error(features)

        anomalies = self._detect_anomalies(recon_err)

        assignments = self.layer3.fit(latent, features)
        symbols = self.layer3.symbolize(latent)

        structure = self.layer3.analyze_sequence(assignments)

        compression_ratio = features.shape[1] / latent.shape[1] if latent.shape[1] > 0 else 0

        return {
            'bits': bits,
            'chunks': chunks,
            'features': features,
            'latent': latent,
            'symbols': symbols,
            'assignments': assignments,
            'anomalies': anomalies,
            'structure': structure,
            'compression_ratio': compression_ratio,
            'losses': losses,
            'reconstruction_error': recon_err,
        }