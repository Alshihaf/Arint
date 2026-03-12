# core/run_cycle.py
import random
import hashlib
import numpy as np
import traceback
import time
import shutil
from pathlib import Path
from . import sws_logic
from tools.health import Severity
from .cot_executive import CoTExecutive

def run_cycle(self):
    self.cycle += 1
    for k in ["hunger_data", "boredom", "messiness", "fatigue"]:
        self.needs[k] += random.randint(1, 5)  # ← Slower increase
        self.needs[k] = max(0, min(100, self.needs[k]))

    plan_action, plan_context = self._get_plan_action()
    if plan_action:
        action = plan_action
        self.current_plan_context = plan_context
        self.log(f"Following plan: {action}")
    else:
        actions_list = [
            "EXPLORE", "EVOLVE", "ORGANIZE", "REST", "WRITE_CODE",
            "EXPLORE_FS", "EXPLORE_GITHUB", "EXPLORE_HF", "REASON", "GENERATE_BINARY_OUTPUT"
        ]
        action_scores = sws_logic.foresight_simulation(self, actions_list)

        self.log(f"[DEBUG] action_scores type: {type(action_scores)}")
        self.log(f"[DEBUG] action_scores length: {len(action_scores) if action_scores else 'None'}")
        if action_scores:
            self.log(f"[DEBUG] First 3 scores: {action_scores[:3]}")
        else:
            self.log(f"[DEBUG] action_scores is EMPTY or None!")

        self.log(f"[DEBUG] Has cot_executive? {hasattr(self, 'cot_executive')}")
        if hasattr(self, 'cot_executive'):
            self.log(f"[DEBUG] cot_executive type: {type(self.cot_executive)}")
            self.log(f"[DEBUG] Has evaluate_action method? {hasattr(self.cot_executive, 'evaluate_action')}")


        chosen_action = None
        self.log("[DEBUG] Starting action evaluation loop")

        for act, score in action_scores:
            self.log(f"[DEBUG] Evaluating action: {act}")
    
            try:
                self.log(f"[DEBUG] Calling cot_executive.evaluate_action for {act}")
                approved, reason, eval_confidence = self.cot_executive.evaluate_action(
                    act, 
                    self.needs, 
                    {"cycle": self.cycle}
                )
                self.log(f"[DEBUG] Result for {act}: approved={approved}, confidence={eval_confidence}")
        
                if approved:
                    boosted_score = score * (0.7 + 0.3 * eval_confidence)
                    chosen_action = act
                    chosen_eval_confidence = eval_confidence
                    self.log(f"[DEBUG] Action {act} APPROVED, breaking loop")
                    break
                else:
                    self.log(f"[DEBUG] Action {act} REJECTED by CoT")
    
            except Exception as e:
                self.log(f"[ERROR] Exception evaluating {act}: {e}")
                self.log(f"[ERROR] Traceback: {traceback.format_exc()}")

        if chosen_action is None:
            action = "REST"
            self.log("All action blocked by executive, so i chose REST")
        else:
            self.log(f"[DEBUG] Final chosen action: {chosen_action}")
            action = chosen_action

    self.log(f"Decided Action: {action} | Needs: {self.needs}")

    result = None
    if action == "EXPLORE":
        new_data = self._perceive()
        if new_data:
            for item in new_data:
                self.brain.add_snippet(item, source="internet:strategic")
            self.brain.consolidate()
            self.needs["hunger_data"] = max(0, self.needs["hunger_data"] - 60)
            self.audit.record(action, impact=len(new_data))
            result = f"Found {len(new_data)} items"
        else:
            self.needs["hunger_data"] = min(100, self.needs["hunger_data"] + 10)
            result = "No new data"

    elif action == "EVOLVE":
        self.needs["fatigue"] = min(100, self.needs["fatigue"] + 10)
        self.log("Activating Unified Evolution Engine...")
        if self.brain.insights:
            insight_id = hashlib.md5(self.brain.insights[0].encode()).hexdigest()[:6]
            task_id = f"evolve_{insight_id}"
            inputs = [(2, 3), (5, 7), (0, 0), (-1, 1)]
            outputs = [5, 12, 0, 0]
            code = self.evolver.evolve_external(
                task_id=task_id,
                inputs=inputs,
                outputs=outputs,
                generations=25
            )
            if code:
                self.log(f"Evolution successful! Generated code:\n{code}")
                self.brain.add_snippet(f"Evolved code for {task_id}: {code[:100]}...", source="evolution")
                result = "Evolution successful"
                self.needs["boredom"] = max(0, self.needs["boredom"] - 50)
            else:
                self.log("Evolution failed to produce valid code.")
                self.needs["boredom"] += 5
                result = "Evolution failed"
        else:
            self.needs["boredom"] += 5
            result = "No insight to evolve"

    elif action == "ORGANIZE":
        self.log("Consolidating Brain Core and cleaning files...")
        self.brain.consolidate()
        raw_dir = Path("memory/knowledge/raw")
        clean_dir = Path("memory/knowledge/clean")
        for f in raw_dir.glob("*"):
            if f.is_file() and random.random() < 0.3:
                shutil.move(str(f), str(clean_dir / f.name))
        self.needs["messiness"] = 0
        if random.random() < 0.1:
            self.mischief()
        result = "Organized"

    elif action == "REST":
        self.kesadaran.tidur()
        self.log("Awareness: sleep for memory consolidation.")
        self.log("Resting (Self-Reflection Mode)...")
        self.log(f"Audit Status: {self.audit.get_wisdom()}")
        self.dreamer.dream(self.brain.snippets)
        self.self_reflect()
        self.reflect_on_goals()
        if random.random() < 0.5:
            self._train_rnn_on_snippets()
        time.sleep(3)
        self.needs["fatigue"] = 0
        result = "Rested"

    elif action == "WRITE_CODE":
        self.needs["fatigue"] = min(100, self.needs["fatigue"] + 10)
        self.log("Writing new code...")
        new_func = self.coder.write_function()
        if new_func:
            self.memory.semantic.add_fact(f"generated_code_{int(time.time())}", new_func, source="coder", confidence=1.0)
            self.needs["boredom"] = max(0, self.needs["boredom"] - 70)
            self.audit.record(action, impact=1)
            self.evolution_success_count += 1
            result = "Code written"
        else:
            self.log("Failed to write code, insufficient knowledge.")
            self.needs["boredom"] += 10
            result = "Failed to write code"

    elif action == "EXPLORE_FS":
        result = self._explore_fs()
    elif action == "EXPLORE_GITHUB":
        result = self._explore_github()
    elif action == "EXPLORE_HF":
        result = self._explore_hf()
    elif action == "REASON":
        self.log("Reasoning about accumulated knowledge...")
        new_insight = sws_logic._reason(self)
        if new_insight:
            self.needs["boredom"] = max(0, self.needs["boredom"] - 30)
            self.needs["hunger_data"] = max(0, self.needs["hunger_data"] - 20)
            self.audit.record(action, impact=1)
            result = new_insight
        else:
            self.needs["boredom"] += 5
            self.needs["hunger_data"] += 5
            result = "No insight"
            
    elif action == "GENERATE_BINARY_OUTPUT":
        result = self._execute_generate_binary_output()
            
    else:
        self.log(f"Unknown action: {action}")
        result = None

    reward = 0.0
    if result is not None:
        if "Failed" not in result and "No" not in result and "error" not in result.lower():
            reward = 1.0
        else:
            reward = -0.5
    else:
        reward = -0.5

    ancaman = True
    if action in ["EVOLVE", "EXPLORE_FS", "WRITE_CODE", "EXPLORE_GITHUB", "EXPLORE_HF"]:
        if result and "Failed" in result:
            ancaman = True

    if hasattr(self, 'intention'):
        action_names = ["EXPLORE", "EVOLVE", "ORGANIZE", "REST", "WRITE_CODE",
                    "EXPLORE_FS", "EXPLORE_GITHUB", "EXPLORE_HF", "REASON",
                    "GENERATE_BINARY_OUTPUT"]
        try:
            action_index = action_names.index(action)
            self.intention.receive_reward(action_index, reward)
        except ValueError:
            pass

    stimulus = self._get_stimulus_vector()
    self.kesadaran.alami_stimulus(stimulus, reward_aktual=reward, ancaman=ancaman)

    try:
        context = self._get_decision_context()
        success = reward > 0
        self.ltm.update_action_success(action, context, success)
    except Exception as e:
        self.log(f"[ERROR] LTM update failed: {e}")
    
    if self.cycle % 500 == 0:
        recent = self.audit.logbook[-200:]
        old = self.audit.logbook[-400:-200]
        if len(recent) > 50 and len(old) > 50:
            recent_success = sum(1 for e in recent if e.get('success', False)) / len(recent)
            old_success = sum(1 for e in old if e.get('success', False)) / len(old)
            if abs(recent_success - old_success) > 0.2:
                self.log(f"Concept drift detected! Success rate changed from {old_success:.2f} to {recent_success:.2f}")
                self.drift_detected = True

    if hasattr(self, 'neuromodulator_log') is False:
        self.neuromodulator_log = []
    self.neuromodulator_log.append({
        'dopamin': self.kesadaran.tingkat_dopamin,
        'kortisol': self.kesadaran.tingkat_kortisol,
        'serotonin': self.kesadaran.tingkat_serotonin,
        'action': action,
        'reward': reward,
        'cycle': self.cycle
    })
    if len(self.neuromodulator_log) > 1000:
        self.neuromodulator_log = self.neuromodulator_log[-500:]

    if self.current_plan_context:
        plan_id = self.current_plan_context.get('plan_id')
        step_index = self.current_plan_context.get('step_index')
        if plan_id is not None and step_index is not None:
            self.planner.mark_step_completed(plan_id, step_index, result)
        self.current_plan_context = None

    if self.cycle % 50 == 0:
        kondisi = self.kesadaran.evaluasi_kondisi()
        self.log(f"Awareness: {kondisi}")

    if self.cycle % 100 == 0 and hasattr(self, 'cot'):
        predictions = self.memory.reflective.get_recent(limit=100)
        cot_preds = [p for p in predictions if p.get('type') == 'cot_prediction']
        if len(cot_preds) >= 10:
            high_conf = [p for p in cot_preds if p['predicted_confidence'] > 0.75]
            if high_conf:
                correct = 0
                for p in high_conf:
                    conclusion = p['conclusion']
                    relevant_entries = [e for e in self.audit.logbook[-50:] if e.get('action') == 'REASON' and e.get('result') == conclusion]
                    if relevant_entries and relevant_entries[-1].get('success', False):
                        correct += 1
                actual_success = correct / len(high_conf)
                expected_success = 0.75
                calibration = actual_success / expected_success
                self.cot.confidence_multiplier = getattr(self.cot, 'confidence_multiplier', 1.0) * 0.9 + calibration * 0.1

    if self.cycle % 200 == 0 and hasattr(self, 'neuromodulator_log') and len(self.neuromodulator_log) >= 50:
        stats = {}
        for entry in self.neuromodulator_log[-200:]:
            d = round(entry['dopamin'] * 2) / 2
            c = round(entry['kortisol'] * 2) / 2
            s = round(entry['serotonin'] * 2) / 2
            key = (d, c, s)
            if key not in stats:
               stats[key] = {}
            act = entry['action']
            if act not in stats[key]:
                stats[key][act] = {'total': 0, 'reward_sum': 0.0}
            stats[key][act]['total'] += 1
            stats[key][act]['reward_sum'] += entry['reward']
        best_actions = {}
        for state, actions in stats.items():
            best = max(actions.items(), key=lambda x: x[1]['reward_sum'] / x[1]['total'] if x[1]['total'] > 3 else -999)
            if best[1]['total'] > 3:
                best_actions[state] = best[0]
        self.neuromodulator_best_actions = best_actions

    if hasattr(self, 'evolver') and self.evolver:
        subgoals = self.goal_manager.goals.get("subgoals", [])
        for i, sg in enumerate(subgoals):
            metadata = sg.get("metadata", {})
            if metadata.get("needs_code") and sg.get("progress", 0) < 1.0:
                self._process_evolution_goal(i)
                break 

    if time.time() - self._last_health_check > 300:
        issues = self.health_checker.run_check(force=True)
        self._last_health_check = time.time()
        if issues:
            critical = sum(1 for i in issues if i['severity'] == Severity.CRITICAL)
            high = sum(1 for i in issues if i['severity'] == Severity.HIGH)
            if critical > 0 or high > 0:
                self.log(f"Health: {critical} CRITICAL, {high} HIGH issues")
        else:
            self.log("Health: Semua sehat.")

    if self.cycle % 50 == 0:
        self._ltm_debug()