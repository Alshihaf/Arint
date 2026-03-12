import numpy as np

class KesadaranBerbasisReward:
    def __init__(self, dimensi=64):
        self.dimensi = dimensi
        self.state_internal = np.random.randn(dimensi) * 0.1
        self.memori_jangka_pendek = np.zeros(dimensi)
        self.memori_jangka_panjang = np.random.randn(dimensi) * 0.1
        self.W_perhatian = np.random.randn(dimensi, dimensi) * np.sqrt(2. / dimensi)
        self.W_asosiasi = np.random.randn(dimensi, dimensi) * np.sqrt(2. / dimensi)
        self.W_ruang_kerja = np.random.randn(dimensi, dimensi) * np.sqrt(2. / dimensi)
        self.tingkat_dopamin = 0.5
        self.ekspektasi_reward = 0.0
        self.ambang_toleransi = 0.0

    def _relu(self, x):
        return np.maximum(0, x)

    def _softmax(self, x):
        e_x = np.exp(x - np.max(x))
        return e_x / (e_x.sum(axis=0) + 1e-9)

    def alami_stimulus(self, stimulus_sensorik, reward_aktual=0.0):
        rpe = reward_aktual - self.ekspektasi_reward
        ledakan_dopamin = rpe - self.ambang_toleransi
        self.tingkat_dopamin = np.clip(0.5 + ledakan_dopamin, 0.0, 1.0)
        self.ekspektasi_reward += 0.2 * rpe
        if self.tingkat_dopamin > 0.7:
            self.ambang_toleransi += 0.05
        else:
            self.ambang_toleransi = max(0.0, self.ambang_toleransi - 0.01)
        pengali_fokus = 1.0 + self.tingkat_dopamin
        skor_perhatian = np.dot(stimulus_sensorik, np.dot(self.W_perhatian, self.state_internal)) * pengali_fokus
        stimulus_fokus = stimulus_sensorik * self._softmax(skor_perhatian)
        aktivasi_memori = np.dot(stimulus_fokus, np.dot(self.W_asosiasi, self.memori_jangka_panjang))
        self.memori_jangka_pendek = 0.7 * self.memori_jangka_pendek + 0.3 * (stimulus_fokus + (aktivasi_memori * self.memori_jangka_panjang))
        sintesis = stimulus_fokus + self.memori_jangka_pendek + self.state_internal
        pikiran_sadar = self._relu(np.dot(self.W_ruang_kerja, sintesis))
        pikiran_sadar = np.clip(pikiran_sadar, -1e6, 1e6)
        self.state_internal = 0.85 * self.state_internal + 0.15 * pikiran_sadar
        laju_belajar = 0.01 + (self.tingkat_dopamin * 0.09)
        self.memori_jangka_panjang += laju_belajar * pikiran_sadar
        return pikiran_sadar

    def evaluasi_kondisi(self):
        if self.tingkat_dopamin >= 0.8:
            return "Euforia / Sangat Termotivasi"
        elif self.tingkat_dopamin <= 0.2:
            return "Anhedonia / Sakaw (Withdrawal) / Kecewa"
        elif self.ambang_toleransi > 0.3 and self.tingkat_dopamin < 0.6:
            return "Craving (Menginginkan stimulasi lebih)"
        else:
            return "Netral / Stabil"


class KesadaranLengkap(KesadaranBerbasisReward):
    def __init__(self, dimensi=64, buffer_size=100, k_svd=10):
        super().__init__(dimensi)
        self.tingkat_serotonin = 0.5
        self.tingkat_kortisol = 0.0
        self.decay_kortisol = 0.95
        self.decay_serotonin = 0.99
        self.W_prediksi = np.random.randn(dimensi, dimensi) * np.sqrt(2./dimensi)
        self.prediksi_sebelumnya = np.zeros(dimensi)
        self.status_metakognisi = "Netral"
        self.ambang_bingung = 1.0
        self.ambang_ingin_tahu = 0.5
        self.riwayat_error = np.zeros(10)
        self.identitas = np.random.randn(dimensi)
        self.identitas = self.identitas / np.linalg.norm(self.identitas)
        self.buffer_size = buffer_size
        self.buffer_pengalaman = []
        self.k_svd = k_svd

    def _update_neuromodulator(self, reward_aktual, prediction_error_magnitude):
        rpe = reward_aktual - self.ekspektasi_reward
        if rpe < -0.3:
            self.tingkat_kortisol += 0.1
        if prediction_error_magnitude > 0.5:
            self.tingkat_kortisol += 0.05 * prediction_error_magnitude
        self.tingkat_kortisol *= self.decay_kortisol
        self.tingkat_kortisol = np.clip(self.tingkat_kortisol, 0.0, 1.0)
        if abs(rpe) < 0.1 and prediction_error_magnitude < 0.2:
            self.tingkat_serotonin += 0.01
        else:
            self.tingkat_serotonin -= 0.005
        self.tingkat_serotonin = np.clip(self.tingkat_serotonin, 0.0, 1.0)

    def _hitung_prediction_error(self, stimulus):
        prediksi = np.dot(self.W_prediksi, self.state_internal)
        error = stimulus - prediksi
        magnitude = np.linalg.norm(error)
        laju_belajar_prediksi = 0.01
        self.W_prediksi += laju_belajar_prediksi * np.outer(error, self.state_internal)
        return error, magnitude

    def _metakognisi(self, error_magnitude):
        self.riwayat_error = np.roll(self.riwayat_error, -1)
        self.riwayat_error[-1] = error_magnitude
        rata_error = np.mean(self.riwayat_error)
        if error_magnitude > self.ambang_bingung:
            self.status_metakognisi = "Bingung"
        elif error_magnitude > self.ambang_ingin_tahu and rata_error > 0.3:
            self.status_metakognisi = "Ingin Tahu"
        else:
            self.status_metakognisi = "Netral"

    def alami_stimulus(self, stimulus_sensorik, reward_aktual=0.0, ancaman=False):
        error, error_magnitude = self._hitung_prediction_error(stimulus_sensorik)
        if ancaman:
            self.tingkat_kortisol += 0.2
        self._update_neuromodulator(reward_aktual, error_magnitude)
        rpe = reward_aktual - self.ekspektasi_reward
        ledakan_dopamin = rpe - self.ambang_toleransi
        self.tingkat_dopamin = np.clip(0.5 + ledakan_dopamin, 0.0, 1.0)
        self.ekspektasi_reward += 0.2 * rpe
        if self.tingkat_dopamin > 0.7:
            self.ambang_toleransi += 0.05
        else:
            self.ambang_toleransi = max(0.0, self.ambang_toleransi - 0.01)
        pengali_fokus = 1.0 + self.tingkat_dopamin + self.tingkat_kortisol
        laju_belajar = 0.01 + (self.tingkat_dopamin * 0.09) + (self.tingkat_kortisol * 0.05) - (self.tingkat_serotonin * 0.02)
        laju_belajar = np.clip(laju_belajar, 0.0, 0.2)
        skor_perhatian = np.dot(stimulus_sensorik, np.dot(self.W_perhatian, self.state_internal)) * pengali_fokus
        stimulus_fokus = stimulus_sensorik * self._softmax(skor_perhatian)
        aktivasi_memori = np.dot(stimulus_fokus, np.dot(self.W_asosiasi, self.memori_jangka_panjang))
        self.memori_jangka_pendek = 0.7 * self.memori_jangka_pendek + 0.3 * (stimulus_fokus + (aktivasi_memori * self.memori_jangka_panjang))
        sintesis = stimulus_fokus + self.memori_jangka_pendek + self.state_internal + 0.1 * self.identitas
        pikiran_sadar = self._relu(np.dot(self.W_ruang_kerja, sintesis))
        proyeksi_identitas = np.dot(pikiran_sadar, self.identitas) * self.identitas
        self.memori_jangka_panjang += laju_belajar * (pikiran_sadar + 0.5 * proyeksi_identitas)
        self.state_internal = 0.85 * self.state_internal + 0.15 * pikiran_sadar
        if len(self.buffer_pengalaman) >= self.buffer_size:
            self.buffer_pengalaman.pop(0)
        self.buffer_pengalaman.append(pikiran_sadar.copy())
        self._metakognisi(error_magnitude)
        return pikiran_sadar

    def tidur(self):
        if len(self.buffer_pengalaman) < 5:
            return

        try:
            matriks = np.vstack(self.buffer_pengalaman)

            if np.any(np.isnan(matriks)) or np.any(np.isinf(matriks)):
                print("[tidur] Buffer mengandung NaN/Inf, buffer dikosongkan")
                self.buffer_pengalaman = []
                return

            if matriks.shape[0] < 2 or matriks.shape[1] == 0:
                print("[tidur] Matriks terlalu kecil untuk SVD")
                self.buffer_pengalaman = []
                return
  
            matriks = np.clip(matriks, -1e6, 1e6)

            U, s, Vt = np.linalg.svd(matriks, full_matrices=False)

            k = min(self.k_svd, len(s))
            komponen_utama = Vt[:k]
            bobot = s[:k] / (np.sum(s[:k]) + 1e-12)  # tambah epsilon
            pola_baru = np.sum(bobot[:, np.newaxis] * komponen_utama, axis=0)

            alpha = 0.3
            self.memori_jangka_panjang = (1 - alpha) * self.memori_jangka_panjang + alpha * pola_baru

            self.buffer_pengalaman = []
            self.tingkat_serotonin = min(1.0, self.tingkat_serotonin + 0.2)
            self.tingkat_kortisol = max(0.0, self.tingkat_kortisol - 0.3)
            self.status_metakognisi = "Netral"
            self.riwayat_error = np.zeros_like(self.riwayat_error)

        except np.linalg.LinAlgError as e:
                print(f"[tidur] SVD error: {e}, buffer dikosongkan")
                self.buffer_pengalaman = []
        except Exception as e:
                print(f"[tidur] Error lain: {e}")
                self.buffer_pengalaman = []