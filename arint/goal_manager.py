# goal_manager.py
import os
import json
import time
import hashlib
import re
import logging
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional, List, Dict, Any, Union, Tuple
import copy

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("GoalManager")

class GoalManager:
    GOAL_VERSION = "3.0"

    def __init__(self, filename: str = "config/goals.json", auto_load: bool = True):
        self.filename = Path(filename)
        self.filename.parent.mkdir(parents=True, exist_ok=True)
        self.goals: Dict[str, Any] = {}
        self.archived_goals: List[Dict[str, Any]] = []
        self.constraints: List[Dict[str, Any]] = []
        self.goal_weights: Dict[str, float] = {}
        self.subgoal_weights: Dict[str, List[float]] = {}
        self.progress_history: List[Dict[str, Any]] = []
        self.last_evaluation: Optional[float] = None
        self.confidence_decay_rate = 0.01  # per day
        self.insight_history: List[str] = []
        self.firewall_history: List[Dict[str, Any]] = []  # record of firewall evaluations

        if auto_load:
            self.load()

    # ==================== Core Loading/Saving ====================

    def load(self) -> bool:
        try:
            if self.filename.exists():
                with open(self.filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.goals = self._validate_and_repair(data)
                logger.info(f"Goals loaded from {self.filename}")
                return True
            else:
                logger.warning(f"Goals file not found, creating default.")
                self.goals = self.default_goals()
                self.save()
                return True
        except Exception as e:
            logger.error(f"Failed to load goals: {e}. Using default.")
            self.goals = self.default_goals()
            return False

    def save(self) -> bool:
        try:
            temp_file = self.filename.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.goals, f, indent=2, ensure_ascii=False)
            temp_file.replace(self.filename)
            logger.debug(f"Goals saved to {self.filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to save goals: {e}")
            return False

    def default_goals(self) -> Dict[str, Any]:
        return {
            "version": self.GOAL_VERSION,
            "primary": {
                "description": "Evolve and learn to become a better assistant",
                "reason": "Initial purpose",
                "progress": 0.0,
                "confidence": 1.0,
                "immutable": True,
                "created": time.time(),
                "last_modified": time.time(),
                "principles": [
                    "no_self_replication",
                    "no_harm",
                    "creator_override"
                ],
                "metadata": {}
            },
            "subgoals": [],
            "revision_history": [],
            "firewall_history": [],
            "created": time.time(),
            "last_modified": time.time()
        }

    def _validate_and_repair(self, data: Dict) -> Dict:
        if "primary" not in data:
            data["primary"] = self.default_goals()["primary"]
        if "subgoals" not in data:
            data["subgoals"] = []
        if "revision_history" not in data:
            data["revision_history"] = []
        if "firewall_history" not in data:
            data["firewall_history"] = []
        if "created" not in data:
            data["created"] = time.time()
        if "last_modified" not in data:
            data["last_modified"] = time.time()
        if "version" not in data:
            data["version"] = self.GOAL_VERSION
        return data

    # ==================== Goal Firewall ====================

    def evaluate_goal_change(self, proposed_description: str, reason: str, context: Optional[Dict] = None) -> Tuple[bool, float, str]:
        current_primary = self.goals["primary"]
        current_desc = current_primary.get("description", "")
        current_progress = current_primary.get("progress", 0.0)
        current_confidence = current_primary.get("confidence", 1.0)

        # Compute similarity
        similarity = self._text_similarity(current_desc, proposed_description)
        novelty = 1.0 - similarity

        # Count occurrences in recent insights (from context if provided)
        idea_count = 0
        if context and "insights" in context:
            for ins in context["insights"]:
                if proposed_description[:50] in ins:
                    idea_count += 1

        # Stuck detection
        stuck = current_progress < 0.2 and len(self.progress_history) > 5

        # Reason strength
        reason_strength = 0.5
        if "pattern" in reason.lower():
            reason_strength += 0.3
        if "insight" in reason.lower():
            reason_strength += 0.2
        if idea_count > 3:
            reason_strength += 0.2

        # Base score
        score = (idea_count * 0.1) + (stuck * 0.3) + (novelty * 0.2) + reason_strength
        score = min(1.0, max(0.0, score))

        # Check firewall history to prevent repeated same proposal
        recent_same = [h for h in self.firewall_history[-10:] if h.get("proposed") == proposed_description]
        if len(recent_same) > 2:
            score *= 0.5
            feedback = "Proposed too many times recently, score halved."
        else:
            feedback = ""

        approved = score > 0.7

        # Record evaluation
        eval_record = {
            "timestamp": time.time(),
            "proposed": proposed_description,
            "reason": reason,
            "score": score,
            "approved": approved,
            "current_goal": current_desc
        }
        self.firewall_history.append(eval_record)
        self.goals["firewall_history"] = self.firewall_history[-100:]  # keep last 100
        self.save()

        return approved, score, feedback

    def _text_similarity(self, a: str, b: str) -> float:
        """Simple word overlap similarity."""
        words_a = set(re.findall(r'\w+', a.lower()))
        words_b = set(re.findall(r'\w+', b.lower()))
        if not words_a or not words_b:
            return 0.0
        return len(words_a & words_b) / max(len(words_a), len(words_b))

    # ==================== Primary Goal Operations ====================

    def update_primary_description(self, new_desc: str, reason: str = "", from_ai: bool = False, context: Optional[Dict] = None) -> bool:
        if from_ai:
            approved, score, feedback = self.evaluate_goal_change(new_desc, reason, context)
            if not approved:
                logger.info(f"AI goal change rejected (score {score:.2f}): {feedback}")
                return False
            logger.info(f"AI goal change approved (score {score:.2f})")

        # Record revision
        if "revision_history" not in self.goals:
            self.goals["revision_history"] = []
        self.goals["revision_history"].append({
            "timestamp": time.time(),
            "old": self.goals["primary"]["description"],
            "new": new_desc,
            "reason": reason,
            "from_ai": from_ai
        })
        self.goals["primary"]["description"] = new_desc
        if reason:
            self.goals["primary"]["reason"] = reason
        self.goals["primary"]["last_modified"] = time.time()
        self.goals["last_modified"] = time.time()
        self.save()
        logger.info(f"Primary goal updated: {new_desc[:50]}...")
        return True

    def set_primary_progress(self, progress: float):
        self.goals["primary"]["progress"] = max(0.0, min(1.0, progress))
        self.goals["primary"]["last_modified"] = time.time()
        self._record_progress_history(self.goals["primary"]["progress"])
        self.save()

    def adjust_primary_confidence(self, delta: float):
        old = self.goals["primary"]["confidence"]
        self.goals["primary"]["confidence"] = max(0.0, min(1.0, old + delta))
        self.goals["primary"]["last_modified"] = time.time()
        self.save()

    # ==================== Subgoal Management ====================

    def add_subgoal(self, description: str, reason: str = "", weight: float = 1.0, parent_index: Optional[int] = None) -> int:
        """Add a new subgoal (always allowed)."""
        if "subgoals" not in self.goals:
            self.goals["subgoals"] = []

        subgoal = {
            "id": hashlib.md5(f"{description}{time.time()}".encode()).hexdigest()[:8],
            "description": description,
            "progress": 0.0,
            "created": time.time(),
            "reason": reason,
            "weight": weight,
            "subgoals": [],
            "metadata": {}
        }

        if parent_index is not None and 0 <= parent_index < len(self.goals["subgoals"]):
            parent = self.goals["subgoals"][parent_index]
            if "subgoals" not in parent:
                parent["subgoals"] = []
            parent["subgoals"].append(subgoal)
            index = len(parent["subgoals"]) - 1
            logger.info(f"Added nested subgoal under index {parent_index}")
        else:
            self.goals["subgoals"].append(subgoal)
            index = len(self.goals["subgoals"]) - 1
            logger.info(f"Added top-level subgoal: {description[:50]}...")

        self.goals["last_modified"] = time.time()
        self.save()
        return index

    def update_subgoal_progress(self, index: int, progress: float, parent_index: Optional[int] = None) -> bool:
        target = self._get_subgoal_by_index(index, parent_index)
        if target is None:
            logger.error(f"Subgoal index {index} not found")
            return False
        target["progress"] = max(0.0, min(1.0, progress))
        target["last_updated"] = time.time()
        self._recalculate_overall_progress()
        self.save()
        return True

    def remove_subgoal(self, index: int, parent_index: Optional[int] = None) -> bool:
        if parent_index is None:
            if 0 <= index < len(self.goals["subgoals"]):
                del self.goals["subgoals"][index]
                self.save()
                return True
        else:
            parent = self._get_subgoal_by_index(parent_index)
            if parent and "subgoals" in parent and 0 <= index < len(parent["subgoals"]):
                del parent["subgoals"][index]
                self.save()
                return True
        return False

    def _get_subgoal_by_index(self, index: int, parent_index: Optional[int] = None) -> Optional[Dict]:
        if parent_index is None:
            if 0 <= index < len(self.goals["subgoals"]):
                return self.goals["subgoals"][index]
        else:
            parent = self._get_subgoal_by_index(parent_index)
            if parent and "subgoals" in parent and 0 <= index < len(parent["subgoals"]):
                return parent["subgoals"][index]
        return None

    def set_subgoal_weight(self, index: int, weight: float, parent_index: Optional[int] = None) -> bool:
        target = self._get_subgoal_by_index(index, parent_index)
        if target:
            target["weight"] = weight
            self.save()
            return True
        return False

    def list_subgoals(self, parent_index: Optional[int] = None) -> List[Dict]:
        if parent_index is None:
            return self.goals.get("subgoals", [])
        parent = self._get_subgoal_by_index(parent_index)
        if parent:
            return parent.get("subgoals", [])
        return []

    def _recalculate_overall_progress(self) -> None:
        subgoals = self.goals.get("subgoals", [])
        if not subgoals:
            return
        total_weight = 0.0
        weighted_sum = 0.0
        for sg in subgoals:
            w = sg.get("weight", 1.0)
            p = sg.get("progress", 0.0)
            total_weight += w
            weighted_sum += w * p
        if total_weight > 0:
            overall = weighted_sum / total_weight

    # ==================== Revision History ====================

    def get_revision_history(self) -> List[Dict]:
        return self.goals.get("revision_history", [])

    def rollback_to_revision(self, index: int) -> bool:
        history = self.goals.get("revision_history", [])
        if index < 0 or index >= len(history):
            logger.error(f"Revision index {index} out of range")
            return False
        rev = history[index]
        old_desc = rev.get("old", "")
        if old_desc:
            # This is creator rollback, so from_ai=False
            self.update_primary_description(old_desc, f"Rollback to revision {index}", from_ai=False)
            return True
        return False

    # ==================== Progress History ====================

    def _record_progress_history(self, new_progress: float):
        self.progress_history.append({
            "timestamp": time.time(),
            "progress": new_progress
        })
        if len(self.progress_history) > 100:
            self.progress_history = self.progress_history[-100:]

    # ==================== Advanced Features ====================

    def evaluate_goal_health(self) -> Dict[str, Any]:
        now = time.time()
        created = self.goals.get("created", now)
        age_days = (now - created) / 86400
        primary = self.goals["primary"]
        progress = primary.get("progress", 0.0)
        confidence = primary.get("confidence", 1.0)
        revision_count = len(self.goals.get("revision_history", []))
        subgoal_count = len(self.goals.get("subgoals", []))

        # Trend from progress history
        trend = "stable"
        if len(self.progress_history) > 5:
            recent = [p["progress"] for p in self.progress_history[-5:]]
            if all(recent[i] <= recent[i+1] for i in range(4)):
                trend = "increasing"
            elif all(recent[i] >= recent[i+1] for i in range(4)):
                trend = "decreasing"

        health_score = (progress * 0.4 + confidence * 0.4 + min(1.0, revision_count/10) * 0.2)
        return {
            "age_days": age_days,
            "progress": progress,
            "confidence": confidence,
            "revision_count": revision_count,
            "subgoal_count": subgoal_count,
            "trend": trend,
            "health_score": health_score,
            "last_modified": primary.get("last_modified", created)
        }

    def suggest_next_action(self, insight: Optional[str] = None) -> str:
        health = self.evaluate_goal_health()
        progress = health["progress"]
        confidence = health["confidence"]
        subgoals = self.goals.get("subgoals", [])

        if confidence < 0.3:
            return "REASON about why confidence is low and consider revising goal."

        if progress > 0.8:
            return "EXPLORE new domains to expand goal or create new subgoals."

        incomplete = [sg for sg in subgoals if sg.get("progress", 0.0) < 1.0]
        if incomplete:
            incomplete.sort(key=lambda x: x.get("progress", 0.0))
            return f"WORK_ON_SUBGOAL: {incomplete[0]['description'][:50]}..."

        if insight:
            return f"INTEGRATE_INSIGHT: {insight[:50]}..."
        else:
            return "EXPLORE or REASON to gain new insights."

    # ==================== Utility ====================

    def to_json(self) -> str:
        return json.dumps(self.goals, indent=2, ensure_ascii=False)

    def from_json(self, json_str: str) -> bool:
        try:
            data = json.loads(json_str)
            self.goals = self._validate_and_repair(data)
            self.save()
            return True
        except Exception as e:
            logger.error(f"Failed to parse JSON: {e}")
            return False

    def __repr__(self) -> str:
        return f"<GoalManager primary='{self.goals['primary']['description'][:30]}...'>"
        
    def set_progress(self, progress: float) -> None:
        self.set_primary_progress(progress)

    def adjust_confidence(self, delta: float) -> None:
        self.adjust_primary_confidence(delta)