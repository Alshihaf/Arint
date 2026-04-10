# core/sws_logic.py
import time
import re
import numpy as np
import random
from typing import List, Dict, Any, Tuple
from neural import MathOps
from collections import defaultdict

def foresight_simulation(self, actions: List[str]) -> List[Tuple[str, float]]:
    scores = {}

    action_stats = defaultdict(lambda: {"total": 0, "success": 0})
    for entry in self.audit.logbook[-100:]:
        act = entry.get('action')
        if act in actions:
            action_stats[act]["total"] += 1
            if entry.get('success', False):
                action_stats[act]["success"] += 1

    primary_goal = self.goal_manager.goals.get("primary", {})
    goal_desc = primary_goal.get("description", "")
    goal_confidence = primary_goal.get("confidence", 1.0)
    desc_lower = goal_desc.lower()

    dopamin = self.kesadaran.tingkat_dopamin
    kortisol = self.kesadaran.tingkat_kortisol
    serotonin = self.kesadaran.tingkat_serotonin
    metakognisi = self.kesadaran.status_metakognisi

    intention_action = None
    action_names = actions
    if hasattr(self, 'intention') and self.intention is not None:
        try:
            if hasattr(self, '_get_intention_input'):
               input_vec = self._get_intention_input()
               action_index = self.intention.step(input_vec)
               if isinstance(action_index, int) and 0 <= action_index < len(action_names):
                intention_action = action_names[action_index]
            else:
                self.log("Warning: _get_intention_input not defined")
        except Exception as e:
            self.log(f"Intention error: {e}")

    for act in actions:
        score = random.random()
        self.log(f"[SWS_DEBUG] Processing action: {act}")

        context = self._get_decision_context()

        recent_success_rate = self.ltm.get_action_success(act, context)
        if recent_success_rate is None:
            exploration_bonus = 0.2
        else:
            exploration_bonus = (1.0 - recent_success_rate) * 0.1

        score += exploration_bonus

        if action_stats[act]["total"] >= 3:
            success_rate = action_stats[act]["success"] / action_stats[act]["total"]
            score += success_rate * 0.4

        if act == intention_action:
            score += 0.5

        if act == "EXPLORE":
            score += (self.needs["hunger_data"] / 100)
            if dopamin < 0.3:
                score += 0.3
            if kortisol > 0.7:
                score -= 0.5
            if metakognisi == "Ingin Tahu":
                score += 0.4
        elif act == "EVOLVE":
            score += (self.needs["boredom"] / 100)
            if dopamin < 0.3:
                score += 0.3
            if kortisol > 0.7:
                score -= 0.5
            if metakognisi == "Ingin Tahu":
                score += 0.4
        elif act == "ORGANIZE":
            score += (self.needs["messiness"] / 100)
            if dopamin < 0.3:
                score += 0.3
            if kortisol > 0.7:
                score -= 0.5
            if metakognisi == "Ingin Tahu":
                score += 0.4
        elif act == "WRITE_CODE":
            if hasattr(self, 'coder') and self.coder.can_write():
                score += (self.needs["boredom"] / 100) * 1.5
            if dopamin < 0.3:
                score += 0.3
            if kortisol > 0.7:
                score -= 0.5
            if metakognisi == "Ingin Tahu":
                score += 0.4
            else:
                score = -999
        elif act == "EXPLORE_FS":
            score += (self.needs["hunger_data"] / 100) * 0.8
            if "file" in desc_lower or "system" in desc_lower or "explore" in desc_lower:
                score += 0.2 * goal_confidence
            if self.brain.snippets and any("fs" in s.lower() for s in self.brain.snippets[-5:]):
                score += 0.1
            if dopamin < 0.3:
                score += 0.3
            if kortisol > 0.7:
                score -= 0.5
            if metakognisi == "Ingin Tahu":
                score += 0.4
        elif act == "EXPLORE_GITHUB":
            score += (self.needs["hunger_data"] / 100) * 0.9
            if "github" in desc_lower or "code" in desc_lower or "repository" in desc_lower:
                score += 0.3 * goal_confidence
            if dopamin < 0.3:
                score += 0.3
            if kortisol > 0.7:
                score -= 0.5
            if metakognisi == "Ingin Tahu":
                score += 0.4
        elif act == "EXPLORE_HF":
            score += (self.needs["hunger_data"] / 100) * 0.8
            if "huggingface" in desc_lower or "model" in desc_lower or "ai" in desc_lower:
                score += 0.3 * goal_confidence
            if dopamin < 0.3:
                score += 0.3
            if kortisol > 0.7:
                score -= 0.5
            if metakognisi == "Ingin Tahu":
                score += 0.4
        elif act == "REASON":
            if len(self.brain.snippets) >= 10:
                score += (self.needs["boredom"] / 100) * 0.8 + (self.needs["hunger_data"] / 100) * 0.2
                if "reason" in desc_lower or "think" in desc_lower or "understand" in desc_lower:
                    score += 0.3 * goal_confidence
            if dopamin < 0.3:
                score += 0.3
            if kortisol > 0.7:
                score -= 0.5
            if metakognisi == "Ingin Tahu":
                score += 0.4
            else:
                score = -999
        elif act == "GENERATE_BINARY_OUTPUT":
           recent_actions = [e.get('actions') for e in self.audit.logbook[-10:] if e.get('actions')]
           if act in recent_actions:
               score -= 0.5
           else:
               score = 0.2
           score += (self.needs["boredom"] / 100) * 1.2
           if len(self.brain.insights) > 3:
               score += 0.2
           if "write" in desc_lower or "create" in desc_lower or "generate" in desc_lower:
                 score += 0.1 * goal_confidence
           if dopamin < 0.3:
                score += 0.3
           if kortisol > 0.7:
                score -= 0.5
           if metakognisi == "Ingin Tahu":
                score += 0.4

        elif act == "WRITE_BINARY":
           score += (self.needs["boredom"] / 100) * 1.2
           if any("pola" in ins or "binary" in ins for ins in self.brain.insights[-10:]):
                score += 0.3
           if "create" in desc_lower or "generate" in desc_lower:
                score += 0.2 * goal_confidence
           if dopamin < 0.3:
                score += 0.3
           if kortisol > 0.7:
                score -= 0.5
           if metakognisi == "Ingin Tahu":
                score += 0.4

        if "knowledge" in desc_lower or "learn" in desc_lower or "explore" in desc_lower:
            if act == "EXPLORE":
                score += 0.2 * goal_confidence
        if "evolution" in desc_lower or "develop" in desc_lower or "strong" in desc_lower:
            if act == "EVOLVE":
                score += 0.2 * goal_confidence
        if "organize" in desc_lower or "clean" in desc_lower:
            if act == "ORGANIZE":
                score += 0.2 * goal_confidence
        if "rest" in desc_lower or "reflect" in desc_lower:
            if act == "REST":
                score += 0.2 * goal_confidence
        if "code" in desc_lower or "program" in desc_lower or "coding" in desc_lower:
            if act == "WRITE_CODE":
                score += 0.2 * goal_confidence

        if hasattr(self, 'neuromodulator_best_actions'):
            state = (round(self.kesadaran.tingkat_dopamin * 2) / 2,
                     round(self.kesadaran.tingkat_kortisol * 2) / 2,
                     round(self.kesadaran.tingkat_serotonin * 2) / 2)
            if state in self.neuromodulator_best_actions and self.neuromodulator_best_actions[state] == act:
                score += 0.3

        # ✅ FIX: LTM bonus DALAM LOOP (bukan di luar)
        try:
            context = self._get_decision_context()
            ltm_rate = self.ltm.get_action_success(act, context)

            if ltm_rate is None and self.cycle > 20:
                ltm_rate = self.ltm.get_action_success_with_fuzzy_match(act, context, tolerance=0.15)

            ltm_weight = 0.3
            if hasattr(self, 'drift_detected') and self.drift_detected:
                ltm_weight *= 0.5
            
            if ltm_rate is not None:
                score += ltm_rate * ltm_weight

        except Exception as e:
            self.log(f"[ERROR] LTM query for {act} failed: {e}")

        # ✅ FIX: scores[act] assignment DALAM LOOP (bukan di luar)
        scores[act] = score

    # ✅ SETELAH LOOP SELESAI: sort dan return semua actions
    sorted_actions = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_actions


def _goal_firewall(self, proposed_description: str, reason: str) -> Tuple[bool, float]:
    current_primary = self.goal_manager.goals.get("primary", {})
    current_goal = current_primary.get("description", "")
    current_progress = current_primary.get("progress", 0.0)

    recent_insights = self.memory.reflective.get_recent(10)

    idea_count = 0
    for ins in recent_insights:
        if proposed_description[:50] in ins.get("insight", ""):
            idea_count += 1

    stuck = current_progress < 0.2 and len(self.goal_manager.progress_history) > 5

    similarity = _text_similarity(current_goal, proposed_description)
    novelty = 1.0 - similarity

    reason_strength = 0.5
    if "pattern" in reason.lower():
        reason_strength += 0.3
    if idea_count > 3:
        reason_strength += 0.2

    score = (idea_count * 0.1) + (stuck * 0.3) + (novelty * 0.2) + reason_strength
    score = min(1.0, max(0.0, score))

    self.memory.reflective.add_reflection({
        "type": "goal_firewall",
        "proposed": proposed_description,
        "reason": reason,
        "score": score,
        "timestamp": time.time()
    })
    return score > 0.7, score


def _text_similarity(a: str, b: str) -> float:
    words_a = set(re.findall(r'\w+', a.lower()))
    words_b = set(re.findall(r'\w+', b.lower()))
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / max(len(words_a), len(words_b))


def _reason(self):
    self.log("> Reasoning...")
    insights_generated = []

    if self.brain.patterns:
        top_pattern = self.brain.patterns[0][0]
        count = self.brain.patterns[0][1]
        insights_generated.append(f"Pattern '{top_pattern}' appears {count} times, suggesting it's important.")
        self.memory.semantic.add_fact(
            f"pattern_{top_pattern}",
            {"pattern": top_pattern, "count": count},
            source="reasoning", confidence=0.7
        )

    if hasattr(self, 'rnn') and len(self.brain.snippets) >= 3:
        try:
            recent = self.brain.snippets[-3:]
            vocab = set()
            for s in recent:
                words = re.findall(r'\w+', s.lower())
                vocab.update(words)
            if vocab:
                word_to_idx = {w: i for i, w in enumerate(vocab)}
                vocab_size = len(vocab)
                if self.rnn.input_dim == vocab_size:
                    inputs = []
                    for s in recent:
                        words = re.findall(r'\w+', s.lower())
                        if words:
                            vec = [0.0] * vocab_size
                            vec[word_to_idx[words[0]]] = 1.0
                            inputs.append(vec)
                    if inputs:
                        outputs, _, _ = self.rnn.forward_sequence(inputs)
                        last_output = outputs[-1]
                        probs = MathOps.softmax(last_output)
                        max_idx = probs.index(max(probs))
                        insights_generated.append(f"RNN last timestep predicted class index {max_idx}.")
        except Exception as e:
            self.log(f"RNN reasoning error: {e}")

    if hasattr(self, 'cot') and self.cot:
        try:
            problem = "Apa insight penting dari informasi yang baru dipelajari?"
            context = {
                "snippets": self.brain.snippets[-10:],
                "needs": self.needs,
                "recent_actions": [e.get('action') for e in self.audit.logbook[-5:]]
            }
            chain = self.cot.reason(problem, context)
            if chain.conclusion and chain.confidence > 0.5:
                self.brain.insights.append(chain.conclusion)
                self.memory.reflective.add_reflection({
                    "type": "chain_of_thought",
                    "insight": chain.conclusion,
                    "confidence": chain.confidence,
                    "timestamp": time.time()
                })
                self.log(f"🧠 Chain of Thought: {chain.conclusion[:100]}...")

            if chain.conclusion:
                self.memory.reflective.add_reflection({
                    "type": "cot_prediction",
                    "conclusion": chain.conclusion,
                    "predicted_confidence": chain.confidence,
                    "timestamp": time.time()
                })

                return chain.conclusion
        except Exception as e:
            self.log(f"Chain of Thought error: {e}")

    if insights_generated:
        final_insight = " | ".join(insights_generated)
        self.brain.insights.append(final_insight)
        self.memory.reflective.add_reflection({
            "type": "insights",
            "content": final_insight,
            "timestamp": time.time()
        })
        self.log(f"New insight: {final_insight}")
        return final_insight
    else:
        self.log("No new insights from reasoning.")
        return None
