# core/cot_executive.py
import logging

logger = logging.getLogger("CoTExecutive")
class CoTExecutive:
    
    def __init__(self, cot, arint_system):
        try:
            self.cot = cot
            self.arint = arint_system
            self.decision_history = []
            logger.info("CoTExecutive.__init__ called")
            logger.info(f"[DEBUG] self.cot is: {type(self.cot)}")
            logger.info(f"[DEBUG] self.cot.reason exists? {hasattr(self.cot, 'reason')}")
        except Exception as e:
            logger.error(f"[ERROR] CoTExecutive.__init__ failed: {e}", exc_info=True)
            raise
    
    def evaluate_action(self, action: str, needs: dict, context: dict) -> tuple:
        logger.info(f"[CoTExec] Evaluating {action}")

        try:
            problem = self._construct_problem(action, needs, context)
            logger.info(f"[CoTExec] Problem constructed for {action}")

            chain = self.cot.reason(problem, context)
            logger.info(f"[CoTExec] CoT returned for {action}, confidence={chain.confidence}")

            confidence = chain.confidence
            threshold = 0.4
            approved = confidence > threshold

            logger.info(f"[CoTExec] {action} → approved={approved}")

            self.decision_history.append({
                'action': action,
                'approved': approved,
                'confidence': confidence,
                'reasoning': chain.conclusion,
                'cycle': context.get('cycle', 0)
            })
        
            return approved, chain.conclusion, confidence

        except Exception as e:
            logger.info(f"[CoTExec] Error evaluating {action}: {e}", exc_info=True)
            return False, f"Error: {e}", 0.0

    def _construct_problem(self, action: str, needs: dict, context: dict) -> str:
        max_need = max(needs.values())
        urgent = "URGENT: " if max_need > 80 else ""
        
        problem = f"""
{urgent}Evaluate apakah action '{action}' reasonable sekarang.

Current state:
- Boredom: {needs.get('boredom', 0)}/100
- Hunger: {needs.get('hunger_data', 0)}/100
- Fatigue: {needs.get('fatigue', 0)}/100
- Messiness: {needs.get('messiness', 0)}/100

Action properties:
- Type: {self._get_action_type(action)}
- Addresses needs: {self._get_action_target(action)}
- Recent success rate: {self._get_recent_success(action):.2f}

Question: Apakah action ini masuk akal diberikan kondisi sekarang?
Pertimbangkan:
1. Apakah action relevan dengan needs yang urgent?
2. Apakah action memiliki track record bagus?
3. Apakah ada alternative yang lebih baik?
4. Kapan terakhir kali action ini dijalankan?

Berikan confidence 0.0-1.0 dalam keputusan Anda.
"""
        return problem.strip()
    
    def _get_action_type(self, action: str) -> str:
        """Kategorisasi action type."""
        if "EXPLORE" in action:
            return "Exploration"
        elif action == "EVOLVE":
            return "Learning/Generation"
        elif action == "ORGANIZE":
            return "Maintenance"
        elif action == "REST":
            return "Recovery"
        elif action == "REASON":
            return "Cognitive"
        else:
            return "Other"
    
    def _get_action_target(self, action: str) -> str:
        targets = {
            "EXPLORE": "hunger_data (knowledge seeking)",
            "EXPLORE_FS": "hunger_data (local knowledge)",
            "EXPLORE_GITHUB": "hunger_data (code knowledge)",
            "EXPLORE_HF": "hunger_data (ML knowledge)",
            "EVOLVE": "boredom (creative satisfaction)",
            "WRITE_CODE": "boredom (creative expression)",
            "ORGANIZE": "messiness (order)",
            "REST": "fatigue (recovery)",
            "REASON": "boredom (cognitive engagement)",
            "GENERATE_BINARY_OUTPUT": "boredom (creative output)"
        }
        return targets.get(action, "unknown")
    
    def _get_recent_success(self, action: str) -> float:
        if not self.decision_history:
            return 0.5
        
        recent = self.decision_history[-20:]
        successes = sum(1 for d in recent if d['action'] == action and d['approved'])
        attempts = sum(1 for d in recent if d['action'] == action)
        
        if attempts == 0:
            return 0.5
        return successes / attempts
    
    def get_statistics(self):
        if not self.decision_history:
            return "No decisions yet"
        
        total = len(self.decision_history)
        approved = sum(1 for d in self.decision_history if d['approved'])
        avg_confidence = sum(d['confidence'] for d in self.decision_history) / total
        
        return f"""
CoT Executive Statistics:
- Total decisions: {total}
- Approved: {approved} ({100*approved/total:.1f}%)
- Rejected: {total-approved} ({100*(total-approved)/total:.1f}%)
- Avg confidence: {avg_confidence:.2f}
"""