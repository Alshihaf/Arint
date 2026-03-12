import sqlite3
import json
import threading
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional


class LongTermMemory:
    """
    Long-Term Memory untuk track action success rates dengan context.
    
    Apa masalah di versi original kamu:
    1. Missing `import time` → line 60 akan error saat update
    2. File incomplete - ada 3 tables tapi hanya 2 methods implemented
    3. Tidak ada error handling untuk cold start (empty database)
    4. Tidak ada methods untuk context fuzzy matching
    
    Solusi di versi ini:
    1. Add all missing imports
    2. Add all helper methods untuk proper context bucketing
    3. Add debug methods untuk understand apa yang stored di database
    4. Add methods untuk plan dan cot tracking (untuk future Priority 3)
    """
    
    def __init__(self, db_path="memory/long_term.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        """Initialize database tables"""
        with self.lock:
            c = self.conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS action_success (
                    action TEXT,
                    context TEXT,
                    success_rate REAL,
                    sample_count INTEGER,
                    last_updated REAL,
                    PRIMARY KEY (action, context)
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS plan_success (
                    plan_template TEXT,
                    context TEXT,
                    success_rate REAL,
                    sample_count INTEGER,
                    last_updated REAL,
                    PRIMARY KEY (plan_template, context)
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS cot_insights (
                    insight_hash TEXT PRIMARY KEY,
                    insight TEXT,
                    confidence REAL,
                    outcome REAL,
                    timestamp REAL
                )
            """)
            self.conn.commit()

    def update_action_success(self, action: str, context: Dict, success: bool):
        """
        Update success rate untuk action dalam specific context.
        
        Args:
            action: Nama action (e.g., "EXPLORE", "EVOLVE")
            context: Dict dengan keys: 'hunger', 'boredom', 'dopamin'
            success: Boolean - apakah action berhasil
        
        Example:
            context = {'hunger': 60, 'boredom': 40, 'dopamin': 0.5}
            ltm.update_action_success('EXPLORE', context, True)
        """
        try:
            with self.lock:
                context_str = json.dumps(context, sort_keys=True)
                c = self.conn.cursor()
                c.execute("SELECT success_rate, sample_count FROM action_success WHERE action=? AND context=?",
                          (action, context_str))
                row = c.fetchone()
                
                if row:
                    old_rate, count = row
                    # Incremental average: (old_rate * count + new_sample) / (count + 1)
                    new_rate = (old_rate * count + (1 if success else 0)) / (count + 1)
                    c.execute(
                        "UPDATE action_success SET success_rate=?, sample_count=?, last_updated=? WHERE action=? AND context=?",
                        (new_rate, count + 1, time.time(), action, context_str)
                    )
                else:
                    # First entry untuk action-context pair
                    c.execute(
                        "INSERT INTO action_success VALUES (?,?,?,?,?)",
                        (action, context_str, 1.0 if success else 0.0, 1, time.time())
                    )
                self.conn.commit()
        except Exception as e:
            print(f"[LTM ERROR] update_action_success failed: {e}")

    def get_action_success(self, action: str, context: Dict) -> Optional[float]:
        """
        Get success rate untuk action dalam specific context.
        
        Returns None jika belum ada data (cold start).
        
        Args:
            action: Nama action
            context: Dict dengan context info
            
        Returns:
            success_rate (0.0-1.0) atau None jika no data
        """
        try:
            with self.lock:
                context_str = json.dumps(context, sort_keys=True)
                c = self.conn.cursor()
                c.execute(
                    "SELECT success_rate FROM action_success WHERE action=? AND context=?", 
                    (action, context_str)
                )
                row = c.fetchone()
                return row[0] if row else None
        except Exception as e:
            print(f"[LTM ERROR] get_action_success failed: {e}")
            return None

    def get_action_success_with_fuzzy_match(self, action: str, context: Dict, tolerance: float = 0.1) -> Optional[float]:
        """
        Get success rate dengan FUZZY matching untuk context.
        
        Problem di cold start: jika belum pernah ada EXACT context match,
        return None. Ini solution-nya - cari "similar" contexts.
        
        Args:
            action: Nama action
            context: Dict dengan context info
            tolerance: Berapa banyak deviation yang acceptable (0.0-1.0)
            
        Returns:
            Weighted average dari similar context matches, atau None
            
        Example:
            # Exact context: hunger=50, dopamin=0.5 belum ada
            # Tapi ada: hunger=40, dopamin=0.5 (success_rate=0.8)
            # Dan ada: hunger=60, dopamin=0.5 (success_rate=0.7)
            # Fuzzy match akan return (0.8 + 0.7) / 2 = 0.75
        """
        try:
            with self.lock:
                c = self.conn.cursor()
                c.execute(
                    "SELECT context, success_rate FROM action_success WHERE action=?",
                    (action,)
                )
                rows = c.fetchall()
                
                if not rows:
                    return None
                
                similar_contexts = []
                for ctx_str, success_rate in rows:
                    try:
                        stored_ctx = json.loads(ctx_str)
                        if self._contexts_similar(context, stored_ctx, tolerance):
                            similar_contexts.append(success_rate)
                    except:
                        continue
                
                if similar_contexts:
                    return sum(similar_contexts) / len(similar_contexts)
                return None
        except Exception as e:
            print(f"[LTM ERROR] get_action_success_with_fuzzy_match failed: {e}")
            return None

    def _contexts_similar(self, ctx1: Dict, ctx2: Dict, tolerance: float) -> bool:
        """Helper untuk check apakah 2 contexts similar enough"""
        for key in ctx1:
            if key not in ctx2:
                return False
            v1, v2 = ctx1[key], ctx2[key]
            if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                # For numeric values, check if within tolerance
                max_val = max(abs(v1), abs(v2))
                if max_val == 0:
                    continue
                deviation = abs(v1 - v2) / max_val
                if deviation > tolerance:
                    return False
            else:
                # For non-numeric, exact match
                if v1 != v2:
                    return False
        return True

    def get_action_stats(self, action: str, limit: int = 10) -> List[Dict]:
        """
        Debug helper - lihat semua contexts untuk specific action.
        Useful untuk understand apa yang sudah di-learn.
        
        Args:
            action: Action name
            limit: Max results
            
        Returns:
            List of dicts dengan context, success_rate, sample_count
        """
        try:
            with self.lock:
                c = self.conn.cursor()
                c.execute(
                    "SELECT context, success_rate, sample_count FROM action_success WHERE action=? ORDER BY sample_count DESC LIMIT ?",
                    (action, limit)
                )
                rows = c.fetchall()
                return [
                    {
                        "context": json.loads(ctx_str),
                        "success_rate": rate,
                        "sample_count": count
                    }
                    for ctx_str, rate, count in rows
                ]
        except Exception as e:
            print(f"[LTM ERROR] get_action_stats failed: {e}")
            return []

    def get_all_learned_actions(self) -> Dict[str, int]:
        """
        Debug helper - lihat semua actions yang sudah di-learn dan berapa data points.
        Useful untuk understand learning progress.
        
        Returns:
            Dict mapping action_name → total_samples
        """
        try:
            with self.lock:
                c = self.conn.cursor()
                c.execute(
                    "SELECT action, SUM(sample_count) as total FROM action_success GROUP BY action ORDER BY total DESC"
                )
                rows = c.fetchall()
                return {action: total for action, total in rows}
        except Exception as e:
            print(f"[LTM ERROR] get_all_learned_actions failed: {e}")
            return {}

    # ============= FUTURE: Plan Success Tracking (Priority 3) =============
    
    def update_plan_success(self, plan_template: str, context: Dict, success: bool):
        """Track success rates untuk plan templates (untuk Priority 3)"""
        try:
            with self.lock:
                context_str = json.dumps(context, sort_keys=True)
                c = self.conn.cursor()
                c.execute(
                    "SELECT success_rate, sample_count FROM plan_success WHERE plan_template=? AND context=?",
                    (plan_template, context_str)
                )
                row = c.fetchone()
                
                if row:
                    old_rate, count = row
                    new_rate = (old_rate * count + (1 if success else 0)) / (count + 1)
                    c.execute(
                        "UPDATE plan_success SET success_rate=?, sample_count=? WHERE plan_template=? AND context=?",
                        (new_rate, count + 1, plan_template, context_str)
                    )
                else:
                    c.execute(
                        "INSERT INTO plan_success VALUES (?,?,?,?,?)",
                        (plan_template, context_str, 1.0 if success else 0.0, 1, time.time())
                    )
                self.conn.commit()
        except Exception as e:
            print(f"[LTM ERROR] update_plan_success failed: {e}")

    def get_plan_success(self, plan_template: str, context: Dict) -> Optional[float]:
        """Get success rate untuk specific plan template"""
        try:
            with self.lock:
                context_str = json.dumps(context, sort_keys=True)
                c = self.conn.cursor()
                c.execute(
                    "SELECT success_rate FROM plan_success WHERE plan_template=? AND context=?",
                    (plan_template, context_str)
                )
                row = c.fetchone()
                return row[0] if row else None
        except Exception as e:
            print(f"[LTM ERROR] get_plan_success failed: {e}")
            return None

    # ============= FUTURE: CoT Insight Tracking (Priority 2 enhancement) =============
    
    def record_cot_outcome(self, insight: str, confidence: float, outcome: float):
        """Record outcome dari CoT predictions untuk calibration"""
        try:
            with self.lock:
                insight_hash = hashlib.md5(insight.encode()).hexdigest()
                c = self.conn.cursor()
                c.execute(
                    "INSERT OR REPLACE INTO cot_insights VALUES (?,?,?,?,?)",
                    (insight_hash, insight, confidence, outcome, time.time())
                )
                self.conn.commit()
        except Exception as e:
            print(f"[LTM ERROR] record_cot_outcome failed: {e}")

    def clear_old_data(self, days: int = 30):
        """Cleanup: delete data older than N days (prevents DB bloat)"""
        try:
            with self.lock:
                cutoff_time = time.time() - (days * 24 * 3600)
                c = self.conn.cursor()
                c.execute("DELETE FROM action_success WHERE last_updated < ?", (cutoff_time,))
                c.execute("DELETE FROM plan_success WHERE last_updated < ?", (cutoff_time,))
                c.execute("DELETE FROM cot_insights WHERE timestamp < ?", (cutoff_time,))
                self.conn.commit()
        except Exception as e:
            print(f"[LTM ERROR] clear_old_data failed: {e}")
