# core/memory_manager.py
import json
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from collections import deque
import threading
import logging

logger = logging.getLogger("MemoryManager")

class EpisodicMemory:
    """
    Memori episodik: menyimpan kejadian-kejadian spesifik (log, aksi, observasi).
    Bersifat sementara, kapasitas terbatas, bisa dipadatkan atau dihapus.
    """
    def __init__(self, storage_path: str = "memory/episodic", max_entries: int = 1000):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.max_entries = max_entries
        self.index_file = self.storage_path / "index.json"
        self.index = self._load_index()
        self.lock = threading.RLock()

    def _load_index(self) -> Dict[str, Dict]:
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_index(self):
        with self.lock:
            with open(self.index_file, 'w') as f:
                json.dump(self.index, f, indent=2)

    def add(self, entry: Dict[str, Any]) -> str:
        """Tambahkan satu entri episodik."""
        with self.lock:
            timestamp = time.time()
            entry_id = hashlib.md5(f"{timestamp}{entry}".encode()).hexdigest()[:16]
            filename = f"ep_{int(timestamp)}_{entry_id}.json"
            filepath = self.storage_path / filename
            data = {
                "id": entry_id,
                "timestamp": timestamp,
                "entry": entry
            }
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            self.index[entry_id] = {
                "timestamp": timestamp,
                "file": filename,
                "type": entry.get("type", "unknown")
            }
            self._prune()
            self._save_index()
            return entry_id

    def _prune(self):
        """Hapus entri tertua jika melebihi kapasitas."""
        if len(self.index) <= self.max_entries:
            return
        sorted_items = sorted(self.index.items(), key=lambda x: x[1]["timestamp"])
        to_delete = sorted_items[:len(self.index) - self.max_entries]
        for entry_id, meta in to_delete:
            filepath = self.storage_path / meta["file"]
            if filepath.exists():
                filepath.unlink()
            del self.index[entry_id]

    def get_recent(self, limit: int = 10) -> List[Dict]:
        """Ambil N entri terbaru."""
        sorted_items = sorted(self.index.items(), key=lambda x: x[1]["timestamp"], reverse=True)
        result = []
        for entry_id, meta in sorted_items[:limit]:
            filepath = self.storage_path / meta["file"]
            if filepath.exists():
                with open(filepath, 'r') as f:
                    result.append(json.load(f))
        return result

    def search_by_type(self, entry_type: str, limit: int = 10) -> List[Dict]:
        """Cari entri berdasarkan tipe (misal: 'explore', 'evolve')."""
        matching = [(eid, meta) for eid, meta in self.index.items() if meta.get("type") == entry_type]
        matching.sort(key=lambda x: x[1]["timestamp"], reverse=True)
        result = []
        for entry_id, meta in matching[:limit]:
            filepath = self.storage_path / meta["file"]
            if filepath.exists():
                with open(filepath, 'r') as f:
                    result.append(json.load(f))
        return result


class SemanticMemory:
    """
    Memori semantik: menyimpan fakta-fakta stabil, pengetahuan umum.
    Setiap entri memiliki bobot dan bisa dirujuk oleh banyak komponen.
    """
    def __init__(self, storage_path: str = "memory/semantic"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.facts_file = self.storage_path / "facts.json"
        self.facts = self._load_facts()
        self.lock = threading.RLock()

    def _load_facts(self) -> Dict[str, Any]:
        if self.facts_file.exists():
            try:
                with open(self.facts_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_facts(self):
        with self.lock:
            with open(self.facts_file, 'w') as f:
                json.dump(self.facts, f, indent=2)

    def add_fact(self, key: str, value: Any, source: str = "", confidence: float = 1.0):
        """Tambahkan atau perbarui fakta."""
        with self.lock:
            self.facts[key] = {
                "value": value,
                "source": source,
                "confidence": confidence,
                "timestamp": time.time(),
                "access_count": 0
            }
            self._save_facts()

    def get_fact(self, key: str) -> Optional[Any]:
        """Ambil fakta berdasarkan kunci."""
        with self.lock:
            if key in self.facts:
                self.facts[key]["access_count"] += 1
                self._save_facts()
                return self.facts[key]["value"]
        return None

    def search(self, query: str) -> List[Dict]:
        """Cari fakta berdasarkan substring pada kunci."""
        results = []
        with self.lock:
            for key, data in self.facts.items():
                if query.lower() in key.lower():
                    results.append({"key": key, **data})
        return results

    def get_all(self) -> Dict[str, Any]:
        with self.lock:
            return self.facts.copy()


class DirectiveMemory:
    """
    Memori direktif: menyimpan keputusan besar, goal, prinsip, aturan main.
    Bersifat immutable untuk AI, hanya bisa diubah oleh creator melalui mekanisme khusus.
    """
    def __init__(self, storage_path: str = "memory/directive"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.directives_file = self.storage_path / "directives.json"
        self.directives = self._load_directives()
        self.lock = threading.RLock()

    def _load_directives(self) -> Dict[str, Any]:
        if self.directives_file.exists():
            try:
                with open(self.directives_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_directives(self):
        with self.lock:
            with open(self.directives_file, 'w') as f:
                json.dump(self.directives, f, indent=2)

    def set_directive(self, key: str, value: Any, immutable: bool = True):
        """Tetapkan direktif. Jika immutable=True, hanya bisa diubah via mekanisme khusus."""
        with self.lock:
            self.directives[key] = {
                "value": value,
                "immutable": immutable,
                "timestamp": time.time(),
                "creator_only": True
            }
            self._save_directives()

    def get_directive(self, key: str) -> Optional[Any]:
        """Ambil direktif."""
        with self.lock:
            if key in self.directives:
                return self.directives[key]["value"]
        return None

    def update_directive(self, key: str, new_value: Any, creator_override: bool = False) -> bool:
        """
        Perbarui direktif. Hanya berhasil jika immutable=False atau creator_override=True.
        Biasanya creator_override hanya dipanggil dari command creator.
        """
        with self.lock:
            if key not in self.directives:
                return False
            if self.directives[key]["immutable"] and not creator_override:
                return False
            self.directives[key]["value"] = new_value
            self.directives[key]["timestamp"] = time.time()
            self._save_directives()
            return True

    def list_all(self) -> Dict[str, Any]:
        with self.lock:
            return {k: v["value"] for k, v in self.directives.items()}


class ReflectiveMemory:
    """
    Memori reflektif: menyimpan hasil evaluasi diri, insight yang gagal/berhasil, metrik internal.
    Digunakan untuk pembelajaran jangka panjang, tidak langsung mempengaruhi aksi.
    """
    def __init__(self, storage_path: str = "memory/reflective"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.reflections_file = self.storage_path / "reflections.json"
        self.reflections = self._load_reflections()
        self.lock = threading.RLock()

    def _load_reflections(self) -> List[Dict]:
        if self.reflections_file.exists():
            try:
                with open(self.reflections_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def _save_reflections(self):
        with self.lock:
            with open(self.reflections_file, 'w') as f:
                json.dump(self.reflections, f, indent=2)

    def add_reflection(self, reflection: Dict[str, Any]):
        """Tambahkan catatan refleksi."""
        with self.lock:
            reflection["timestamp"] = time.time()
            reflection["id"] = hashlib.md5(f"{time.time()}{reflection}".encode()).hexdigest()[:16]
            self.reflections.append(reflection)
            # Batasi jumlah (misal 1000 terbaru)
            if len(self.reflections) > 1000:
                self.reflections = self.reflections[-1000:]
            self._save_reflections()

    def get_recent(self, limit: int = 10) -> List[Dict]:
        with self.lock:
            return self.reflections[-limit:]

    def search_by_type(self, refl_type: str) -> List[Dict]:
        with self.lock:
            return [r for r in self.reflections if r.get("type") == refl_type]


# ------------------------------------------------------------------------------
# Memory Manager Utama (mengintegrasikan keempat jenis memori)
# ------------------------------------------------------------------------------
class MemoryManager:
    """
    Facade untuk mengakses semua jenis memori.
    Digunakan oleh komponen lain seperti Cognition dan Executive.
    """
    def __init__(self):
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self.directive = DirectiveMemory()
        self.reflective = ReflectiveMemory()
        logger.info("MemoryManager initialized with all four memory types.")

    def record_action(self, action: str, details: Dict[str, Any]):
        """Catat aksi ke memori episodik."""
        self.episodic.add({
            "type": "action",
            "action": action,
            "details": details,
            "cycle": details.get("cycle", 0)
        })

    def record_insight(self, insight: str, source: str, success: bool = True):
        """Catat insight ke memori reflektif."""
        self.reflective.add_reflection({
            "type": "insight",
            "content": insight,
            "source": source,
            "success": success
        })

    def store_fact(self, key: str, value: Any, source: str = "", confidence: float = 1.0):
        """Simpan fakta ke memori semantik."""
        self.semantic.add_fact(key, value, source, confidence)

    def get_directive(self, key: str) -> Optional[Any]:
        """Ambil direktif."""
        return self.directive.get_directive(key)

    def set_directive(self, key: str, value: Any, immutable: bool = True):
        """Tetapkan direktif (biasanya dari creator)."""
        self.directive.set_directive(key, value, immutable)

    def update_directive(self, key: str, new_value: Any, creator_override: bool = False) -> bool:
        """Perbarui direktif (creator override)."""
        return self.directive.update_directive(key, new_value, creator_override)