import time
import logging
from enum import Enum, auto
from typing import List, Dict, Any, Optional

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    psutil = None

try:
    import subprocess
    import json
    HAS_TERMUX = True
except ImportError:
    HAS_TERMUX = False

logger = logging.getLogger(__name__)


class Severity(Enum):
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented


class HealthChecker:
    def __init__(self, arint, config: Optional[Dict[str, Any]] = None):
        self.arint = arint
        self.config = {
            'memory_snippet_limit': 5000,
            'executive_block_rate': 70.0,
            'need_threshold': 95,
            'error_count_limit': 5,
            'check_interval': 60,
            'auto_heal': False,
            'cpu_threshold': 90,
            'memory_threshold': 90,
            'disk_threshold': 90,
            'disk_path': '/',
            'battery_threshold': 20,
            'executive_cache_ttl': 10,
            'max_issues_per_cycle': 10,
        }
        if config:
            self.config.update(config)

        self._executive_cache = {'data': None, 'timestamp': 0.0}
        self._last_check_time = 0.0

        # if HAS_PSUTIL:
        #     psutil.cpu_percent(interval=None)

        self._audit_valid = self._validate_audit()

    def _validate_audit(self) -> bool:
        try:
            audit = self.arint.audit
            if not hasattr(audit, 'logbook'):
                logger.error("Audit tidak memiliki atribut 'logbook'")
                return False
            if not isinstance(audit.logbook, list):
                logger.error("Audit.logbook bukan list, melainkan %s", type(audit.logbook).__name__)
                return False
            return True
        except Exception as e:
            logger.error(f"Validasi audit gagal: {e}")
            return False

    def run_check(self, force: bool = False) -> List[Dict[str, Any]]:
        now = time.time()
        if not force and (now - self._last_check_time) < self.config['check_interval']:
            logger.debug("Interval pengecekan belum tercapai, kembalikan [].")
            return []

        issues = []

        issues.extend(self._check_memory())
        issues.extend(self._check_executive())
        issues.extend(self._check_needs())
        issues.extend(self._check_resources())
        issues.extend(self._check_errors())

        self._take_actions(issues)

        self._last_check_time = now
        return issues

    def _check_memory(self) -> List[Dict[str, Any]]:
        issues = []
        try:
            snippets_count = len(self.arint.brain.snippets)
            if snippets_count > self.config['memory_snippet_limit']:
                issues.append({
                    "severity": Severity.MEDIUM,
                    "component": "memory",
                    "message": f"Terlalu banyak snippets ({snippets_count} > {self.config['memory_snippet_limit']})",
                    "suggestion": "Lakukan konsolidasi memori untuk mengurangi jumlah snippets.",
                    "action_key": "consolidate_memory"
                })
        except AttributeError as e:
            logger.error(f"Gagal memeriksa memory: {e}")
        return issues

    def _check_executive(self) -> List[Dict[str, Any]]:
        issues = []
        try:
            now = time.time()
            cache = self._executive_cache
            if cache['data'] is not None and (now - cache['timestamp']) < self.config['executive_cache_ttl']:
                block_rate = cache['data']
            else:
                recent = self.arint.memory.episodic.search_by_type("action", limit=100)
                if not recent:
                    return issues
                total = len(recent)
                blocked = sum(1 for e in recent if not e.get("entry", {}).get("approved", True))
                block_rate = (blocked / total) * 100
                cache['data'] = block_rate
                cache['timestamp'] = now

            if block_rate > self.config['executive_block_rate']:
                issues.append({
                    "severity": Severity.HIGH,
                    "component": "executive",
                    "message": f"Executive terlalu ketat: {block_rate:.1f}% aksi diblokir (threshold {self.config['executive_block_rate']}%)",
                    "suggestion": "Turunkan max_freq di executive.py atau naikkan window.",
                    "action_key": "adjust_executive"
                })
        except Exception as e:
            logger.error(f"Gagal memeriksa executive: {e}")
        return issues

    def _check_needs(self) -> List[Dict[str, Any]]:
        issues = []
        try:
            needs = self.arint.needs
            stuck = [k for k, v in needs.items() if v > self.config['need_threshold']]
            if stuck:
                issues.append({
                    "severity": Severity.HIGH,
                    "component": "needs",
                    "message": f"Kebutuhan macet: {stuck} (nilai > {self.config['need_threshold']})",
                    "suggestion": "Cek apakah ada action yang bisa memenuhi kebutuhan ini.",
                    "action_key": "review_needs"
                })
        except Exception as e:
            logger.error(f"Gagal memeriksa needs: {e}")
        return issues

    def _check_resources(self) -> List[Dict[str, Any]]:
        issues = []
        issues.extend(self._check_cpu())
        issues.extend(self._check_memory_system())
        issues.extend(self._check_disk())
        issues.extend(self._check_battery())
        return issues

    def _check_cpu(self) -> List[Dict[str, Any]]:
        issues = []
        cpu_percent = None

        if HAS_TERMUX:
            try:
               result = subprocess.run(
                   ["termux-cpu-info"],
                   capture_output=True,
                   text=True,
                   timeout=5
               )
               if result.returncode == 0:
                   data = json.loads(result.stdout)
                   if data and isinstance(data, list):
                       total_percent = sum(core.get("percent", 0) for core in data)
                       cpu_percent = total_percent / len(data)
            except Exception as e:
                logger.debug(f"Gagal menggunakan termux-cpu-info: {e}")

        if cpu_percent is None and HAS_PSUTIL:
            try:
               cpu_percent = psutil.cpu_percent(interval=None)
            except Exception as e:
               logger.error(f"Gagal memeriksa CPU via psutil: {e}")

        if cpu_percent is not None and cpu_percent > self.config['cpu_threshold']:
            issues.append({
                "severity": Severity.MEDIUM,
                "component": "cpu",
                "message": f"CPU usage tinggi: {cpu_percent:.1f}% (threshold {self.config['cpu_threshold']}%)",
                "suggestion": "Kurangi beban atau tingkatkan interval tidur.",
                "action_key": "reduce_cpu_load"
             })
        return issues

    def _check_memory_system(self) -> List[Dict[str, Any]]:
        if not HAS_PSUTIL:
            return []
        issues = []
        try:
            mem = psutil.virtual_memory()
            if mem.percent > self.config['memory_threshold']:
                issues.append({
                    "severity": Severity.HIGH,
                    "component": "memory_system",
                    "message": f"Memory usage tinggi: {mem.percent}% (threshold {self.config['memory_threshold']}%)",
                    "suggestion": "Kurangi penggunaan memory atau restart.",
                    "action_key": "free_memory"
                })
        except Exception as e:
            logger.error(f"Gagal memeriksa memory sistem: {e}")
        return issues

    def _check_disk(self) -> List[Dict[str, Any]]:
        if not HAS_PSUTIL:
            return []
        issues = []
        try:
            disk_path = self.config['disk_path']
            disk = psutil.disk_usage(disk_path)
            if disk.percent > self.config['disk_threshold']:
                issues.append({
                    "severity": Severity.HIGH,
                    "component": "disk",
                    "message": f"Disk usage di {disk_path} tinggi: {disk.percent}% (threshold {self.config['disk_threshold']}%)",
                    "suggestion": "Bersihkan file sampah.",
                    "action_key": "clean_disk"
                })
        except Exception as e:
            logger.error(f"Gagal memeriksa disk di {self.config['disk_path']}: {e}")
        return issues

    def _check_battery(self) -> List[Dict[str, Any]]:
        if not HAS_TERMUX:
            return []
        issues = []
        try:
            result = subprocess.run(
                ["termux-battery-status"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                percentage = data.get('percentage', 100)
                if percentage < self.config['battery_threshold']:
                    issues.append({
                        "severity": Severity.MEDIUM,
                        "component": "battery",
                        "message": f"Battery rendah: {percentage}% (threshold {self.config['battery_threshold']}%)",
                        "suggestion": "Segera charge.",
                        "action_key": "charge_battery"
                    })
        except Exception as e:
            logger.debug(f"Gagal memeriksa baterai (mungkin termux-api tidak tersedia): {e}")
        return issues

    def _check_errors(self) -> List[Dict[str, Any]]:
        issues = []
        if not self._audit_valid:
            issues.append({
                "severity": Severity.CRITICAL,
                "component": "audit",
                "message": "Subsistem audit tidak valid atau rusak.",
                "suggestion": "Periksa konfigurasi audit dan inisialisasi.",
                "action_key": "repair_audit"
            })
            return issues

        try:
            logbook = self.arint.audit.logbook
            recent = logbook[-50:] if len(logbook) >= 50 else logbook
            errors = [e for e in recent if e.get('type') == 'error']
            if len(errors) > self.config['error_count_limit']:
                issues.append({
                    "severity": Severity.CRITICAL,
                    "component": "system",
                    "message": f"Terjadi {len(errors)} error dalam 50 siklus terakhir (threshold {self.config['error_count_limit']})",
                    "suggestion": "Cek log, mungkin ada bug.",
                    "action_key": "investigate_errors"
                })
        except Exception as e:
            logger.error(f"Gagal memeriksa error: {e}")
            self._audit_valid = False
            issues.append({
                "severity": Severity.CRITICAL,
                "component": "audit",
                "message": f"Gagal mengakses logbook: {e}",
                "suggestion": "Periksa integritas audit.",
                "action_key": "repair_audit"
            })
        return issues

    def _take_actions(self, issues: List[Dict[str, Any]]):
        sorted_issues = sorted(issues, key=lambda i: i["severity"].value, reverse=True)

        if any(issue["severity"] == Severity.CRITICAL for issue in issues):
            try:
                self.arint.auto_backup()
                logger.critical("CRITICAL issue terdeteksi, backup dibuat.")
            except Exception as e:
                logger.error(f"Gagal auto-backup: {e}")

        max_process = self.config['max_issues_per_cycle']
        for issue in sorted_issues[:max_process]:
            severity = issue["severity"]
            component = issue["component"]
            message = issue["message"]
            suggestion = issue.get("suggestion", "")
            action_key = issue.get("action_key")

            if severity == Severity.CRITICAL:
                logger.critical(f"CRITICAL [{component}]: {message}. Saran: {suggestion}")
                if self.config['auto_heal'] and action_key:
                    self._auto_heal(action_key, issue)
            elif severity == Severity.HIGH:
                logger.warning(f"HIGH [{component}]: {message}. Saran: {suggestion}")
            else:
                logger.info(f"MEDIUM [{component}]: {message}")

        if len(sorted_issues) > max_process:
            logger.warning(f"Terdapat {len(sorted_issues)} isu, hanya {max_process} teratas yang diproses.")

    def _auto_heal(self, action_key: str, issue: Dict[str, Any]):

        handlers = {
            "consolidate_memory": self._heal_consolidate_memory,
            "adjust_executive": self._heal_adjust_executive,
            "clean_disk": self._heal_clean_disk,
        }

        handler = handlers.get(action_key)
        if handler:
            try:
                handler(issue)
                logger.info(f"Auto-heal: {action_key} berhasil dijalankan.")
            except Exception as e:
                logger.error(f"Auto-heal {action_key} gagal: {e}")
        else:
            logger.debug(f"Tidak ada handler untuk action_key: {action_key}")

    def _heal_consolidate_memory(self, issue: Dict[str, Any]):
        if hasattr(self.arint.brain, 'consolidate'):
            self.arint.brain.consolidate()
        else:
            raise AttributeError("brain.consolidate() tidak tersedia")

    def _heal_adjust_executive(self, issue: Dict[str, Any]):
        logger.warning("Auto-heal adjust_executive belum diimplementasikan.")

    def _heal_clean_disk(self, issue: Dict[str, Any]):
        logger.warning("Auto-heal clean_disk tidak diimplementasikan demi keamanan.")
 
    def get_config(self, key: str = None) -> Any:
        if key is None:
            return self.config.copy()
        return self.config.get(key)

    def set_config(self, key: str, value: Any):
        if key in self.config:
            self.config[key] = value
            logger.info(f"Konfigurasi {key} diubah menjadi {value}")
        else:
            logger.warning(f"Kunci konfigurasi {key} tidak dikenal.")