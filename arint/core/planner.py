# core/planner.py
import logging
import re
import json
import time
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("Planner")

@dataclass
class PlanStep:
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    expected_outcome: str = ""
    completed: bool = False
    result: Any = None
    timestamp: float = 0.0

@dataclass
class Plan:
    id: str
    goal_id: str
    goal_description: str
    steps: List[PlanStep]
    created: float
    last_updated: float
    status: str = "active"  
    parent_plan_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class Planner:
    def __init__(self, memory_manager, goal_manager, executive):
        self.memory = memory_manager
        self.gm = goal_manager
        self.executive = executive
        self.active_plans: Dict[str, Plan] = {}
        self.plan_history: List[Plan] = []
        self.plans_dir = Path("memory/plans")
        self.plans_dir.mkdir(parents=True, exist_ok=True)
        self._load_plans()
        self.plan_success_rates = {}

    def _load_plans(self):
        for f in self.plans_dir.glob("plan_*.json"):
            try:
                with open(f, 'r') as fp:
                    data = json.load(fp)
                plan = self._dict_to_plan(data)
                if plan.status == "active":
                    self.active_plans[plan.id] = plan
                else:
                    self.plan_history.append(plan)
            except Exception as e:
                logger.error(f"Failed to load plan {f}: {e}")

    def _save_plan(self, plan: Plan):
        path = self.plans_dir / f"plan_{plan.id}.json"
        data = {
            "id": plan.id,
            "goal_id": plan.goal_id,
            "goal_description": plan.goal_description,
            "steps": [{"action": s.action, "params": s.params, "expected_outcome": s.expected_outcome,
                       "completed": s.completed, "result": s.result, "timestamp": s.timestamp} for s in plan.steps],
            "created": plan.created,
            "last_updated": plan.last_updated,
            "status": plan.status,
            "parent_plan_id": plan.parent_plan_id,
            "metadata": plan.metadata
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def _dict_to_plan(self, data: Dict) -> Plan:
        steps = [PlanStep(**s) for s in data.get("steps", [])]
        return Plan(
            id=data["id"],
            goal_id=data["goal_id"],
            goal_description=data["goal_description"],
            steps=steps,
            created=data["created"],
            last_updated=data["last_updated"],
            status=data["status"],
            parent_plan_id=data.get("parent_plan_id"),
            metadata=data.get("metadata", {})
        )

    def create_plan(self, goal_id: str, goal_description: str, context: Optional[Dict] = None) -> Plan:
        logger.info(f"Creating plan for goal: {goal_description[:50]}...")
        plan_id = hashlib.md5(f"{goal_id}{time.time()}".encode()).hexdigest()[:16]

        similar_plans = self._find_similar_plans(goal_description)
        if similar_plans:
            steps = self._adapt_plan_from_history(similar_plans[0], context)
        else:
            steps = self._generate_generic_plan(goal_description, context)

        plan = Plan(
            id=plan_id,
            goal_id=goal_id,
            goal_description=goal_description,
            steps=steps,
            created=time.time(),
            last_updated=time.time(),
            status="active"
        )
        self.active_plans[plan_id] = plan
        self._save_plan(plan)
        return plan

    def _find_similar_plans(self, goal_description: str) -> List[Plan]:
        words = set(re.findall(r'\w+', goal_description.lower()))
        similar = []
        for plan in self.plan_history:
            if plan.status == "completed":
                plan_words = set(re.findall(r'\w+', plan.goal_description.lower()))
                overlap = len(words & plan_words)
                if overlap > 2:  # threshold sederhana
                    similar.append(plan)
        similar.sort(key=lambda p: -len(set(re.findall(r'\w+', p.goal_description.lower())) & words))
        return similar

    def _adapt_plan_from_history(self, past_plan: Plan, context: Optional[Dict]) -> List[PlanStep]:
        steps = []
        for step in past_plan.steps:
            new_step = PlanStep(
                action=step.action,
                params=step.params.copy(),
                expected_outcome=step.expected_outcome
            )
            steps.append(new_step)
        return steps

    def _generate_generic_plan(self, goal_description: str, context: Optional[Dict]) -> List[PlanStep]:
        templates = [
             (['EXPLORE', 'REASON', 'ORGANIZE'], 0.0),
             (['EXPLORE', 'REASON', 'WRITE_CODE'], 0.0),
             (['EXPLORE_FS', 'REASON', 'ORGANIZE'], 0.0),
             (['EVOLVE', 'WRITE_CODE', 'REST'], 0.0),
        ]
        best_template = None
        best_score = -1.0
        for template, _ in templates:
            key = '_'.join(template)
            stats = self.plan_success_rates.get(key, {'success': 0, 'total': 1})
            score = stats['success'] / stats['total'] if stats['total'] > 0 else 0.0
            if score > best_score:
                best_score = score
                best_template = template
        if best_template is None:
            best_template = templates[0][0]
        return [PlanStep(action=a) for a in best_template]

        return steps

    def get_next_step(self, plan_id: str) -> Optional[PlanStep]:
        plan = self.active_plans.get(plan_id)
        if not plan:
            return None
        for step in plan.steps:
            if not step.completed:
                return step
        return None

    def mark_step_completed(self, plan_id: str, step_index: int, result: Any = None):
        plan = self.active_plans.get(plan_id)
        if not plan:
            return
        if 0 <= step_index < len(plan.steps):
            plan.steps[step_index].completed = True
            plan.steps[step_index].result = result
            plan.steps[step_index].timestamp = time.time()
            plan.last_updated = time.time()
            self._save_plan(plan)

            if all(s.completed for s in plan.steps):
                plan.status = "completed"
                self.plan_history.append(plan)
                del self.active_plans[plan_id]
                self._save_plan(plan)
                logger.info(f"Plan {plan_id} completed successfully.")
                plan_template = '_'.join([step.action for step in plan.steps])
                outcome_quality = 1.0 if result and 'Failed' not in result else 0.0
                if plan_template not in self.plan_success_rates:
                    self.plan_success_rates[plan_template] = {'success': 0, 'total': 0}
                self.plan_success_rates[plan_template]['total'] += 1
                if outcome_quality > 0.5:
                    self.plan_success_rates[plan_template]['success'] += 1

    def update_plan(self, plan_id: str, new_steps: List[PlanStep], reason: str = ""):
        plan = self.active_plans.get(plan_id)
        if not plan:
            return
        plan.steps = new_steps
        plan.last_updated = time.time()
        plan.metadata["last_update_reason"] = reason
        self._save_plan(plan)
        logger.info(f"Plan {plan_id} updated: {reason}")

    def get_active_plans(self) -> List[Plan]:
        return list(self.active_plans.values())

    def suggest_action_from_plans(self) -> Optional[Tuple[str, Dict]]:
        for plan in self.active_plans.values():
            for idx, step in enumerate(plan.steps):
                if not step.completed:
                    return (step.action, {"plan_id": plan.id, "step": step, "step_index": idx})
        return None