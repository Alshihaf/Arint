import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class Reflection:

    def __init__(self, memory_router=None):
        self.memory_router = memory_router
        self.logbook = []

    def reflect(
        self,
        action: str,
        outcome: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        context = context or {}

        outcome_lower = outcome.lower()
        if "berhasil" in outcome_lower or "sukses" in outcome_lower:
            sentiment = "positif"
            analysis = (
                f"Tindakan '{action}' menghasilkan '{outcome}'. "
                "Ini adalah hasil positif. Pertahankan strategi."
            )
        elif "gagal" in outcome_lower or "error" in outcome_lower:
            sentiment = "negatif"
            analysis = (
                f"Tindakan '{action}' menghasilkan '{outcome}'. "
                "Perlu evaluasi ulang. Mungkin ada pendekatan lain."
            )
        else:
            sentiment = "netral"
            analysis = (
                f"Tindakan '{action}' menghasilkan '{outcome}'. "
                "Hasil tidak jelas, perlu analisis lebih lanjut."
            )

        self._store_reflection(action, outcome, analysis, sentiment, context)

        return analysis

    def record(self, action: str, impact: int = 0, success: bool = True) -> None:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "impact": impact,
            "success": success
        }
        self.logbook.append(entry)
        logger.debug(f"Recorded action: {action}, impact: {impact}, success: {success}")

    def get_wisdom(self) -> str:
        total = len(self.logbook)
        if total == 0:
            return "Belum ada catatan aksi."

        success_count = sum(1 for e in self.logbook if e.get('success', False))
        success_rate = success_count / total

        from collections import Counter
        action_counts = Counter(e['action'] for e in self.logbook)
        most_common = action_counts.most_common(1)[0] if action_counts else ("None", 0)

        return (f"Total aksi: {total}, Tingkat keberhasilan: {success_rate:.2%}, "
                f"Aksi terbanyak: {most_common[0]} ({most_common[1]} kali)")

    def suggest_improvement(
        self,
        decision_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        suggestions = []

        if decision_id and hasattr(self.memory_router, 'retrieve'):
            try:
                memory_data = self.memory_router.retrieve(decision_id)
                if memory_data:
                    recent_outcomes = [
                        m.get("outcome", "") for m in memory_data
                        if m.get("type") == "reflection"
                    ]
                    if recent_outcomes:
                        failure_count = sum(
                            1 for o in recent_outcomes if "gagal" in o.lower()
                        )
                        if failure_count > len(recent_outcomes) // 2:
                            suggestions.append(
                                "Terlalu banyak kegagalan serupa. Pertimbangkan untuk "
                                "mengubah strategi secara fundamental."
                            )
            except Exception as e:
                logger.warning(f"Gagal mengambil memori untuk decision_id {decision_id}: {e}")

        generic_suggestions = [
            "Coba gunakan pendekatan berbeda",
            "Libatkan lebih banyak informasi dari memori jangka panjang",
            "Simulasikan hasil sebelum bertindak",
            "Evaluasi ulang asumsi awal",
            "Minta masukan dari modul lain (misal: reasoning atau planning)"
        ]

        if context and context.get("urgency") == "tinggi":
            suggestions.append("Prioritaskan tindakan cepat dengan risiko minimal.")
        if context and context.get("complexity") == "tinggi":
            suggestions.append("Pecah masalah menjadi langkah-langkah kecil.")

        suggestions.extend(generic_suggestions)

        return list(dict.fromkeys(suggestions))

    def _store_reflection(
        self,
        action: str,
        outcome: str,
        analysis: str,
        sentiment: str,
        context: Dict[str, Any]
    ) -> None:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "reflection",
            "action": action,
            "outcome": outcome,
            "analysis": analysis,
            "sentiment": sentiment,
            "context": context
        }

        if hasattr(self.memory_router, 'store'):
            try:
                self.memory_router.store(entry, namespace="consciousness")
                return
            except Exception as e:
                logger.error(f"Gagal menyimpan refleksi ke memory_router: {e}. Fallback ke file.")

        log_path = "ai_core/memory/consciousness/current.log"
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Gagal menyimpan refleksi ke file: {e}")

    def reflect_on_action(self, action: str, outcome: str, context: Optional[Dict] = None) -> str:
        return self.reflect(action, outcome, context)

    def analyze_decision(self, decision: str, outcome: str, context: Optional[Dict] = None) -> str:
        return self.reflect(decision, outcome, context)


class AuditLoop(Reflection):

    def __init__(self):
        super().__init__(memory_router=None)