# core/flock_of_thought.py
"""
╔══════════════════════════════════════════════════════════════╗
║         FLOCK OF THOUGHT (FoT) — Integration Layer           ║
║                                                              ║
║  Bukan modul baru — ini adalah jaringan penghubung antar     ║
║  modul ARINT yang sudah ada. Setiap modul memberikan         ║
║  feedback ke modul lainnya, membentuk sistem yang benar-     ║
║  benar terjalin (interconnected).                            ║
║                                                              ║
║  Aliran feedback:                                            ║
║    CoT → Imagination → Planner (pre-action)                  ║
║    Reflection → LTM → Kesadaran → CoT (post-action)          ║
║    AuditLoop → BrainCore → GoalManager (meta-learning)       ║
║    Semua → saling memperbarui satu sama lain        
╚══════════════════════════════════════════════════════════════╝
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("FlockOfThought")


class FlockOfThought:
    """
    Orkestrator integrasi antar modul ARINT.

    Tidak menggantikan modul manapun. Tugasnya:
    1. Mengarahkan output satu modul menjadi input modul lain.
    2. Menjaga feedback loop tetap aktif setiap siklus.
    3. Mengekspos satu titik masuk (pre_action, post_action, meta_sync)
       yang dipanggil dari run_cycle.
    """

    def __init__(self, arint):
        self.arint = arint
        self._fot_log: List[Dict] = []
        logger.info("[FoT] Flock of Thought initialized — semua modul terhubung.")

    # ══════════════════════════════════════════════════════════════
    # 1. PRE-ACTION PHASE
    #    Dipanggil SEBELUM action dipilih.
    #    Output: konteks pengayaan yang diumpankan ke scoring & executive.
    # ══════════════════════════════════════════════════════════════

    def pre_action(self, candidate_actions: List[str]) -> Dict[str, Any]:
        """
        Jalankan semua modul secara terjalin sebelum action dipilih.
        Returns dict berisi signal dari setiap modul untuk dipakai scoring.
        """
        fot_signals = {}

        # ── Langkah 1: Kesadaran → memberi tahu CoT soal emotional state ──
        emotional_context = self._get_emotional_context()
        fot_signals["emotional_context"] = emotional_context

        # ── Langkah 2: Planner → apakah ada rencana aktif? ──
        plan_signal = self._get_plan_signal()
        fot_signals["plan_signal"] = plan_signal

        # ── Langkah 3: LTM → ambil pattern keberhasilan masa lalu ──
        ltm_signal = self._get_ltm_signal(candidate_actions)
        fot_signals["ltm_signal"] = ltm_signal

        # ── Langkah 4: CoT meranking action dengan input dari semua signal di atas ──
        cot_rankings = self._cot_rank_actions(
            candidate_actions, emotional_context, plan_signal, ltm_signal
        )
        fot_signals["cot_rankings"] = cot_rankings

        # ── Langkah 5: Imagination mensimulasikan 2 kandidat teratas ──
        if cot_rankings:
            top_two = [a for a, _ in cot_rankings[:2]]
            imagination_signals = self._imagine_actions(top_two, emotional_context)
            fot_signals["imagination_signals"] = imagination_signals
        else:
            fot_signals["imagination_signals"] = {}

        # ── Langkah 6: BrainCore memberi konteks terkini ke Planner ──
        self._sync_brain_to_planner()

        self._fot_entry("pre_action", fot_signals)
        return fot_signals

    # ══════════════════════════════════════════════════════════════
    # 2. POST-ACTION PHASE
    #    Dipanggil SETELAH action selesai dieksekusi.
    #    Output: semua modul diperbarui berdasarkan hasil action.
    # ══════════════════════════════════════════════════════════════

    def post_action(self, action: str, result: Any, reward: float, success: bool):
        """
        Setelah action selesai, umpankan hasilnya ke semua modul:
        Reflection → LTM → Kesadaran → CoT → Planner → GoalManager
        """
        context = self.arint._get_decision_context()
        context["cycle"] = self.arint.cycle
        context["result"] = str(result)[:200]

        # ── Langkah 1: Reflection menganalisis apa yang terjadi ──
        reflection_analysis = self._run_reflection(action, result, success, context)

        # ── Langkah 2: Reflection → LTM (simpan pelajaran) ──
        self._reflection_to_ltm(action, context, success, reflection_analysis)

        # ── Langkah 3: LTM → Kesadaran (update emotional state berdasarkan outcome) ──
        self._ltm_to_kesadaran(action, success, reward)

        # ── Langkah 4: Kesadaran → CoT (update confidence multiplier) ──
        self._kesadaran_to_cot()

        # ── Langkah 5: CoT → Planner (apakah perlu revisi rencana?) ──
        self._cot_to_planner(action, success, reflection_analysis)

        # ── Langkah 6: AuditLoop → GoalManager (update progres tujuan) ──
        self._audit_to_goal_manager()

        # ── Langkah 7: BrainCore → Transformer (latih jika ada snippet baru) ──
        self._brain_to_transformer()

        self._fot_entry("post_action", {
            "action": action,
            "success": success,
            "reward": reward,
            "reflection": reflection_analysis[:100] if reflection_analysis else ""
        })

    # ══════════════════════════════════════════════════════════════
    # 3. META-SYNC PHASE
    #    Dipanggil setiap N siklus untuk sinkronisasi menyeluruh.
    # ══════════════════════════════════════════════════════════════

    def meta_sync(self):
        """
        Sinkronisasi mendalam antar modul setiap 10 siklus.
        - BrainCore patterns → GoalManager subgoals
        - AuditLoop wisdom → CoT confidence calibration
        - Imagination history → LTM enrichment
        - Kesadaran metacognisi → Planner template scoring
        """
        # ── BrainCore patterns → GoalManager ──
        self._brain_patterns_to_goals()

        # ── AuditLoop wisdom → CoT calibration ──
        self._audit_wisdom_to_cot()

        # ── Kesadaran metacognisi → Planner template bias ──
        self._kesadaran_to_planner_bias()

        # ── LTM → BrainCore enrichment ──
        self._ltm_to_brain()

        self._fot_entry("meta_sync", {"cycle": self.arint.cycle})
        logger.info(f"[FoT] Meta-sync selesai di siklus {self.arint.cycle}")

    # ══════════════════════════════════════════════════════════════
    # IMPLEMENTASI INTERNAL — Pre-Action
    # ══════════════════════════════════════════════════════════════

    def _get_emotional_context(self) -> Dict[str, Any]:
        """Kesadaran → memberi sinyal emosional ke modul lain."""
        k = self.arint.kesadaran
        return {
            "dopamin": k.tingkat_dopamin,
            "serotonin": k.tingkat_serotonin,
            "kortisol": k.tingkat_kortisol,
            "metakognisi": getattr(k, "status_metakognisi", "Netral"),
            "kondisi": k.evaluasi_kondisi(),
        }

    def _get_plan_signal(self) -> Dict[str, Any]:
        """Planner → apakah ada rencana aktif yang harus diikuti?"""
        try:
            active_plans = self.arint.planner.get_active_plans()
            if active_plans:
                plan = active_plans[0]
                return {
                    "has_plan": True,
                    "goal": plan.goal_description[:80],
                    "next_action": self.arint.planner.get_next_step(plan.id).action
                    if self.arint.planner.get_next_step(plan.id) else None,
                    "plan_id": plan.id,
                }
        except Exception as e:
            logger.debug(f"[FoT] Plan signal error: {e}")
        return {"has_plan": False}

    def _get_ltm_signal(self, actions: List[str]) -> Dict[str, float]:
        """LTM → success rate historis untuk setiap action kandidat."""
        signal = {}
        try:
            ctx = self.arint._get_decision_context()
            for act in actions:
                rate = self.arint.ltm.get_action_success(act, ctx)
                if rate is None and self.arint.cycle > 20:
                    rate = self.arint.ltm.get_action_success_with_fuzzy_match(act, ctx, tolerance=0.15)
                signal[act] = rate if rate is not None else 0.5
        except Exception as e:
            logger.debug(f"[FoT] LTM signal error: {e}")
        return signal

    def _cot_rank_actions(
        self,
        actions: List[str],
        emotional_context: Dict,
        plan_signal: Dict,
        ltm_signal: Dict,
    ) -> List[Tuple[str, float]]:
        """
        CoT meranking actions dengan mempertimbangkan:
        - Emotional state (dari Kesadaran)
        - Rencana aktif (dari Planner)
        - Histori keberhasilan (dari LTM)
        """
        try:
            plan_action = plan_signal.get("next_action")
            goal_desc = plan_signal.get("goal", "")
            emotional_state = emotional_context.get("kondisi", "Netral")
            ltm_summary = ", ".join(
                f"{a}:{v:.2f}" for a, v in list(ltm_signal.items())[:4]
            )

            problem = (
                f"Pilih action terbaik dari {actions} mengingat:\n"
                f"- Emotional state: {emotional_state}\n"
                f"- Goal aktif: {goal_desc or 'tidak ada'}\n"
                f"- LTM success rates: {ltm_summary}\n"
                f"- Action rencana: {plan_action or 'tidak ada'}\n"
                f"Beri prioritas action yang paling masuk akal sekarang."
            )

            chain = self.arint.cot.reason(problem, emotional_context)
            confidence = chain.confidence

            rankings = []
            for act in actions:
                score = ltm_signal.get(act, 0.5)
                if plan_action and act == plan_action:
                    score += 0.4
                if emotional_context.get("dopamin", 0.5) > 0.6 and act in ["EXPLORE", "EVOLVE"]:
                    score += 0.2
                if emotional_context.get("kortisol", 0.0) > 0.6 and act == "REST":
                    score += 0.3
                score *= (0.7 + 0.3 * confidence)
                rankings.append((act, score))

            rankings.sort(key=lambda x: x[1], reverse=True)
            return rankings

        except Exception as e:
            logger.debug(f"[FoT] CoT ranking error: {e}")
            return [(a, 0.5) for a in actions]

    def _imagine_actions(
        self, actions: List[str], emotional_context: Dict
    ) -> Dict[str, Dict]:
        """
        Imagination → simulasikan kemungkinan hasil untuk kandidat teratas.
        Hasil simulasi diumpankan kembali ke scoring sebagai signal risiko.
        """
        signals = {}
        try:
            for action in actions:
                scenario = (
                    f"Mengeksekusi {action} saat dopamin={emotional_context.get('dopamin', 0.5):.2f}, "
                    f"kortisol={emotional_context.get('kortisol', 0.0):.2f}"
                )
                params = {
                    "action": action,
                    "needs": self.arint.needs.copy(),
                    "cycle": self.arint.cycle,
                }
                sim_result = self.arint.imagination.simulate(
                    scenario=scenario,
                    parameters=params,
                    n_layers=2,
                    branch_factor=3,
                )
                risk = sim_result.risk_assessment if sim_result else {}
                signals[action] = {
                    "avg_impact": risk.get("rata_rata", 0.0),
                    "variance": risk.get("variansi", 0.0),
                    "recommended": sim_result.recommended_actions[:1] if sim_result else [],
                }
        except Exception as e:
            logger.debug(f"[FoT] Imagination error: {e}")
        return signals

    def _sync_brain_to_planner(self):
        """BrainCore patterns → Planner mendapat konteks pengetahuan terkini."""
        try:
            if self.arint.brain.insights:
                recent_insight = self.arint.brain.insights[-1]
                active_plans = self.arint.planner.get_active_plans()
                for plan in active_plans:
                    if "metadata" not in plan.__dict__:
                        plan.metadata = {}
                    plan.metadata["last_brain_insight"] = recent_insight[:100]
        except Exception as e:
            logger.debug(f"[FoT] Brain→Planner sync error: {e}")

    # ══════════════════════════════════════════════════════════════
    # IMPLEMENTASI INTERNAL — Post-Action
    # ══════════════════════════════════════════════════════════════

    def _run_reflection(
        self, action: str, result: Any, success: bool, context: Dict
    ) -> str:
        """Reflection menganalisis outcome dan menyimpan analisis ke BrainCore."""
        try:
            outcome_str = str(result) if result else ("berhasil" if success else "gagal")
            analysis = self.arint.audit.reflect(action, outcome_str, context)

            # Reflection → BrainCore (insight dari refleksi masuk ke memori)
            if analysis and len(analysis) > 20:
                self.arint.brain.add_snippet(
                    f"[Reflection] {analysis[:200]}", source="fot:reflection"
                )
            return analysis or ""
        except Exception as e:
            logger.debug(f"[FoT] Reflection error: {e}")
            return ""

    def _reflection_to_ltm(
        self, action: str, context: Dict, success: bool, reflection: str
    ):
        """
        Reflection → LTM
        Simpan bukan hanya success/fail, tapi juga analisis refleksi ke LTM
        sebagai metadata konteks.
        """
        try:
            ctx_enriched = context.copy()
            if reflection:
                ctx_enriched["reflection_snippet"] = reflection[:50]
            self.arint.ltm.update_action_success(action, ctx_enriched, success)
        except Exception as e:
            logger.debug(f"[FoT] Reflection→LTM error: {e}")

    def _ltm_to_kesadaran(self, action: str, success: bool, reward: float):
        """
        LTM → Kesadaran
        Success rate historis mempengaruhi ekspektasi reward di Kesadaran,
        membuat neuromodulator lebih realistis.
        """
        try:
            ctx = self.arint._get_decision_context()
            historical_rate = self.arint.ltm.get_action_success(action, ctx)
            if historical_rate is not None:
                expected_reward = (historical_rate * 2) - 1.0
                adjusted_reward = 0.6 * reward + 0.4 * expected_reward
                stimulus = self.arint._get_stimulus_vector()
                ancaman = action in ["EVOLVE", "WRITE_CODE"] and not success
                self.arint.kesadaran.alami_stimulus(
                    stimulus, reward_aktual=adjusted_reward, ancaman=ancaman
                )
        except Exception as e:
            logger.debug(f"[FoT] LTM→Kesadaran error: {e}")

    def _kesadaran_to_cot(self):
        """
        Kesadaran → CoT
        Status metakognisi dan neuromodulator mempengaruhi confidence multiplier CoT.
        Saat kortisol tinggi: CoT lebih konservatif.
        Saat dopamin tinggi: CoT lebih ekspansif.
        """
        try:
            dopamin = self.arint.kesadaran.tingkat_dopamin
            kortisol = self.arint.kesadaran.tingkat_kortisol
            serotonin = self.arint.kesadaran.tingkat_serotonin

            multiplier = 1.0
            if dopamin > 0.7:
                multiplier += 0.15
            elif dopamin < 0.3:
                multiplier -= 0.1

            if kortisol > 0.7:
                multiplier -= 0.2
            elif kortisol < 0.3:
                multiplier += 0.05

            if serotonin > 0.6:
                multiplier += 0.05

            multiplier = max(0.5, min(1.5, multiplier))

            old = getattr(self.arint.cot, "confidence_multiplier", 1.0)
            self.arint.cot.confidence_multiplier = 0.8 * old + 0.2 * multiplier
        except Exception as e:
            logger.debug(f"[FoT] Kesadaran→CoT error: {e}")

    def _cot_to_planner(self, action: str, success: bool, reflection: str):
        """
        CoT → Planner
        Jika action gagal, CoT merencanakan ulang dengan reasoning.
        Jika sukses dan tidak ada rencana, CoT menyarankan rencana baru.
        """
        try:
            active_plans = self.arint.planner.get_active_plans()
            goals = self.arint.goal_manager.goals
            primary_goal = goals.get("primary", {})
            goal_desc = primary_goal.get("description", "")

            if not success and active_plans:
                plan = active_plans[0]
                problem = (
                    f"Action '{action}' gagal saat mengikuti rencana '{plan.goal_description}'. "
                    f"Hasil refleksi: {reflection[:80]}. "
                    "Apakah perlu merevisi langkah-langkah rencana?"
                )
                chain = self.arint.cot.reason(problem, {"action": action, "success": success})
                if chain.confidence > 0.6 and "revisi" in chain.conclusion.lower():
                    from .planner import PlanStep
                    revised = [
                        PlanStep(action="REASON"),
                        PlanStep(action=action),
                        PlanStep(action="REST"),
                    ]
                    self.arint.planner.update_plan(
                        plan.id, revised, reason=f"FoT revisi: {chain.conclusion[:60]}"
                    )
                    logger.info(f"[FoT] Planner direvisi oleh CoT: {chain.conclusion[:60]}")

            elif not active_plans and goal_desc and self.arint.cycle % 20 == 0:
                problem = (
                    f"Goal: '{goal_desc}'. "
                    f"Action terakhir: '{action}' ({'sukses' if success else 'gagal'}). "
                    "Apakah perlu membuat rencana baru untuk mencapai goal ini?"
                )
                chain = self.arint.cot.reason(problem, {"goal": goal_desc})
                if chain.confidence > 0.55:
                    primary_id = primary_goal.get("id", "default")
                    self.arint.planner.create_plan(primary_id, goal_desc, context={
                        "cot_recommendation": chain.conclusion[:100]
                    })
                    logger.info(f"[FoT] Planner membuat rencana baru dari CoT")
        except Exception as e:
            logger.debug(f"[FoT] CoT→Planner error: {e}")

    def _audit_to_goal_manager(self):
        """
        AuditLoop → GoalManager
        Wisdom dari AuditLoop (success rate keseluruhan) memperbarui
        confidence goal dan mendeteksi stagnasi.
        """
        try:
            wisdom = self.arint.audit.get_wisdom()
            if "Tingkat keberhasilan:" in wisdom:
                parts = wisdom.split("Tingkat keberhasilan:")
                if len(parts) > 1:
                    rate_str = parts[1].split(",")[0].strip().replace("%", "")
                    try:
                        rate = float(rate_str) / 100.0
                        adjustment = (rate - 0.5) * 0.1
                        self.arint.goal_manager.adjust_primary_confidence(adjustment)
                    except ValueError:
                        pass

            recent_50 = self.arint.audit.logbook[-50:]
            if len(recent_50) >= 20:
                rest_count = sum(1 for e in recent_50 if e.get("action") == "REST")
                if rest_count > 30:
                    primary = self.arint.goal_manager.goals.get("primary", {})
                    desc = primary.get("description", "")
                    if desc:
                        from . import sws_logic
                        new_goal = f"Tingkatkan diversitas aksi: eksplorasi lebih dari '{desc[:40]}'"
                        approved, score = sws_logic._goal_firewall(
                            self.arint, new_goal, "AuditLoop mendeteksi REST loop"
                        )
                        if approved:
                            self.arint.goal_manager.update_primary_description(
                                new_goal,
                                f"FoT AuditLoop: REST dominan ({rest_count}/50)",
                                from_ai=True,
                                context={"audit_signal": True}
                            )
                            logger.info("[FoT] GoalManager diperbarui: REST loop terdeteksi")
        except Exception as e:
            logger.debug(f"[FoT] Audit→GoalManager error: {e}")

    def _brain_to_transformer(self):
        """
        BrainCore → Transformer
        Setiap kali BrainCore punya snippet baru, Transformer mendapat
        kesempatan untuk mempelajarinya (bukan hanya saat REST).
        """
        try:
            if (
                hasattr(self.arint, "transformer")
                and len(self.arint.brain.snippets) > 10
                and self.arint.cycle % 5 == 0
            ):
                recent = self.arint.brain.snippets[-5:]
                if not self.arint.transformer.tokenizer:
                    self.arint.transformer.fit_tokenizer(recent)
                else:
                    self.arint.transformer.fit_tokenizer(
                        self.arint.brain.snippets[-20:]
                    )
        except Exception as e:
            logger.debug(f"[FoT] Brain→Transformer error: {e}")

    # ══════════════════════════════════════════════════════════════
    # IMPLEMENTASI INTERNAL — Meta-Sync
    # ══════════════════════════════════════════════════════════════

    def _brain_patterns_to_goals(self):
        """
        BrainCore patterns → GoalManager subgoals
        Pattern yang muncul berulang → dijadikan subgoal otomatis.
        """
        try:
            patterns = self.arint.brain.patterns
            if not patterns:
                return
            top_pattern = patterns[0][0] if patterns else None
            if not top_pattern:
                return

            existing_subgoals = [
                sg.get("description", "")
                for sg in self.arint.goal_manager.goals.get("subgoals", [])
            ]
            new_goal = f"Pahami dan kuasai konsep: '{top_pattern}'"
            if not any(top_pattern in sg for sg in existing_subgoals):
                self.arint.goal_manager.add_subgoal(
                    new_goal, reason=f"FoT: pola '{top_pattern}' sering muncul di BrainCore"
                )
                logger.info(f"[FoT] Subgoal baru dari BrainCore pattern: {top_pattern}")
        except Exception as e:
            logger.debug(f"[FoT] Brain patterns→Goals error: {e}")

    def _audit_wisdom_to_cot(self):
        """
        AuditLoop → CoT confidence calibration
        Jika success rate tinggi, CoT boleh lebih percaya diri.
        Jika rendah, CoT harus lebih konservatif.
        """
        try:
            recent = self.arint.audit.logbook[-100:]
            if len(recent) < 20:
                return
            success_rate = sum(1 for e in recent if e.get("success", False)) / len(recent)
            ideal = 0.65
            calibration = 1.0 + (success_rate - ideal) * 0.3
            calibration = max(0.7, min(1.3, calibration))
            old = getattr(self.arint.cot, "confidence_multiplier", 1.0)
            self.arint.cot.confidence_multiplier = 0.85 * old + 0.15 * calibration
            logger.debug(
                f"[FoT] CoT calibration: success_rate={success_rate:.2f} → multiplier={self.arint.cot.confidence_multiplier:.3f}"
            )
        except Exception as e:
            logger.debug(f"[FoT] Audit→CoT calibration error: {e}")

    def _kesadaran_to_planner_bias(self):
        """
        Kesadaran metakognisi → Planner template bias
        Status 'Ingin Tahu' → Planner pilih template explore-heavy.
        Status 'Kelelahan' → Planner pilih template rest-then-organize.
        """
        try:
            metakognisi = getattr(self.arint.kesadaran, "status_metakognisi", "Netral")
            kondisi = self.arint.kesadaran.evaluasi_kondisi()

            if "Ingin Tahu" in metakognisi or "Termotivasi" in kondisi:
                preferred = ["EXPLORE", "REASON", "EVOLVE"]
            elif "Netral" in metakognisi:
                preferred = ["EXPLORE", "REASON", "ORGANIZE"]
            else:
                preferred = ["REST", "ORGANIZE", "REASON"]

            if not hasattr(self.arint.planner, "plan_success_rates"):
                self.arint.planner.plan_success_rates = {}

            template_key = "_".join(preferred)
            if template_key not in self.arint.planner.plan_success_rates:
                self.arint.planner.plan_success_rates[template_key] = {
                    "success": 1,
                    "total": 2,
                }
        except Exception as e:
            logger.debug(f"[FoT] Kesadaran→Planner bias error: {e}")

    def _ltm_to_brain(self):
        """
        LTM → BrainCore enrichment
        Pola keberhasilan dari LTM dimasukkan sebagai insight di BrainCore
        agar CoT dan Imagination bisa memakai pengetahuan historis ini.
        """
        try:
            if not hasattr(self.arint.ltm, "get_all_learned_actions"):
                return
            learned = self.arint.ltm.get_all_learned_actions()
            if not learned:
                return
            for action in learned[:3]:
                stats = self.arint.ltm.get_action_stats(action, limit=2)
                if stats:
                    for s in stats:
                        rate = s.get("success_rate", 0.5)
                        ctx = s.get("context", {})
                        if rate > 0.7:
                            insight = (
                                f"[LTM] '{action}' berhasil {rate:.0%} dalam konteks {ctx}"
                            )
                            if insight not in self.arint.brain.insights:
                                self.arint.brain.insights.append(insight)
        except Exception as e:
            logger.debug(f"[FoT] LTM→Brain error: {e}")

    # ══════════════════════════════════════════════════════════════
    # UTILITIES
    # ══════════════════════════════════════════════════════════════

    def _fot_entry(self, phase: str, data: Dict):
        """Catat setiap phase FoT untuk audit dan debugging."""
        entry = {
            "timestamp": time.time(),
            "cycle": getattr(self.arint, "cycle", 0),
            "phase": phase,
            "data": {k: str(v)[:120] for k, v in data.items()},
        }
        self._fot_log.append(entry)
        if len(self._fot_log) > 500:
            self._fot_log = self._fot_log[-300:]

    def get_fot_summary(self) -> Dict:
        """Ringkasan status FoT untuk monitoring."""
        recent = self._fot_log[-20:]
        phases = {}
        for e in recent:
            p = e["phase"]
            phases[p] = phases.get(p, 0) + 1
        return {
            "total_entries": len(self._fot_log),
            "recent_phases": phases,
            "last_cycle": recent[-1]["cycle"] if recent else 0,
        }
