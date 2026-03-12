import json
import logging
import hashlib
import math
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
#  ENUMERASI & STRUKTUR DATA
# ──────────────────────────────────────────────

class ThinkingLayer(Enum):
    SURFACE      = 0
    ANALYTICAL   = 1
    CRITICAL     = 2
    INFERENTIAL  = 3
    CREATIVE     = 4
    METACOGNITIVE= 5
    SYNTHETIC    = 6


class ReasoningStatus(Enum):
    PENDING    = "pending"
    ACTIVE     = "active"
    RESOLVED   = "resolved"
    DEADLOCKED = "deadlocked"
    REVISED    = "revised"


@dataclass
class Thought:
    layer: ThinkingLayer
    content: str
    confidence: float = 1.0
    supports: List[str] = field(default_factory=list)
    contradicts: List[str] = field(default_factory=list)
    id: str = field(default="")

    def __post_init__(self):
        if not self.id:
            raw = f"{self.layer.name}:{self.content}:{datetime.now().isoformat()}"
            self.id = hashlib.md5(raw.encode()).hexdigest()[:8]


@dataclass
class Hypothesis:
    statement: str
    confidence: float
    evidence_for: List[str]     = field(default_factory=list)
    evidence_against: List[str] = field(default_factory=list)
    status: str = "unverified"

    def net_confidence(self) -> float:
        penalty = len(self.evidence_against) * 0.1
        return max(0.0, min(1.0, self.confidence - penalty))


@dataclass
class ReasoningChain:
    problem: str
    thoughts: List[Thought]         = field(default_factory=list)
    hypotheses: List[Hypothesis]    = field(default_factory=list)
    contradictions: List[str]       = field(default_factory=list)
    backtrack_log: List[str]        = field(default_factory=list)
    conclusion: str                 = ""
    confidence: float               = 0.0
    status: ReasoningStatus         = ReasoningStatus.PENDING
    depth: int                      = 0
    iterations: int                 = 0
    timestamp: str                  = field(default_factory=lambda: datetime.now().isoformat())

    def summary(self) -> Dict[str, Any]:
        by_layer: Dict[str, List[str]] = defaultdict(list)
        for t in self.thoughts:
            by_layer[t.layer.name].append(t.content)
        return {
            "problem": self.problem,
            "depth": self.depth,
            "iterations": self.iterations,
            "layers_activated": list(by_layer.keys()),
            "thoughts_by_layer": dict(by_layer),
            "hypotheses": [
                {"statement": h.statement, "net_confidence": round(h.net_confidence(), 2), "status": h.status}
                for h in self.hypotheses
            ],
            "contradictions_found": self.contradictions,
            "backtrack_log": self.backtrack_log,
            "conclusion": self.conclusion,
            "overall_confidence": round(self.confidence, 2),
            "status": self.status.value,
            "timestamp": self.timestamp,
        }


# ──────────────────────────────────────────────
#  KOMPONEN BERPIKIR MODULAR
# ──────────────────────────────────────────────

class SurfaceAnalyzer:

    def analyze(self, problem: str, context: Dict) -> List[Thought]:
        thoughts = []

        problem_type = self._classify_problem(problem)
        thoughts.append(Thought(
            layer=ThinkingLayer.SURFACE,
            content=f"Jenis masalah terdeteksi: {problem_type}",
            confidence=0.85
        ))

        keywords = self._extract_keywords(problem)
        thoughts.append(Thought(
            layer=ThinkingLayer.SURFACE,
            content=f"Kata kunci utama: {', '.join(keywords)}",
            confidence=0.9
        ))

        if context:
            constraints = [f"{k}={v}" for k, v in context.items()]
            thoughts.append(Thought(
                layer=ThinkingLayer.SURFACE,
                content=f"Konteks/batasan diketahui: {'; '.join(constraints)}",
                confidence=0.95
            ))

        return thoughts

    def _classify_problem(self, problem: str) -> str:
        p = problem.lower()
        if any(w in p for w in ["kenapa", "mengapa", "why"]):
            return "Kausal / Penjelasan"
        if any(w in p for w in ["bagaimana", "how", "cara"]):
            return "Prosedural / Metode"
        if any(w in p for w in ["apa", "what", "siapa"]):
            return "Faktual / Definisi"
        if any(w in p for w in ["haruskah", "should", "pilih"]):
            return "Evaluatif / Keputusan"
        if any(w in p for w in ["prediksi", "akan", "future"]):
            return "Prediktif"
        return "Umum / Tidak terklasifikasi"

    def _extract_keywords(self, problem: str) -> List[str]:
        stop_words = {"dan", "atau", "yang", "di", "ke", "dari", "untuk",
                      "adalah", "dengan", "pada", "itu", "ini", "jika", "maka"}
        words = problem.lower().split()
        return [w.strip("?.!,") for w in words
                if w not in stop_words and len(w) > 3][:6]


class DeepAnalyzer:
    def analyze(self, problem: str, surface_thoughts: List[Thought],
                context: Dict) -> Tuple[List[Thought], List[str]]:
        thoughts = []
        contradictions = []

        sub_problems = self._decompose(problem)
        for sp in sub_problems:
            thoughts.append(Thought(
                layer=ThinkingLayer.ANALYTICAL,
                content=f"Sub-masalah: {sp}",
                confidence=0.8
            ))

        assumptions = self._find_assumptions(problem, context)
        for asm in assumptions:
            thoughts.append(Thought(
                layer=ThinkingLayer.CRITICAL,
                content=f"Asumsi tersembunyi: {asm}",
                confidence=0.7
            ))

        for i, t1 in enumerate(surface_thoughts):
            for t2 in surface_thoughts[i+1:]:
                if self._is_contradictory(t1.content, t2.content):
                    desc = f"Kontradiksi: '{t1.content[:40]}...' vs '{t2.content[:40]}...'"
                    contradictions.append(desc)
                    thoughts.append(Thought(
                        layer=ThinkingLayer.CRITICAL,
                        content=desc,
                        confidence=0.75,
                        contradicts=[t1.id, t2.id]
                    ))

        weaknesses = self._identify_weaknesses(problem)
        for w in weaknesses:
            thoughts.append(Thought(
                layer=ThinkingLayer.CRITICAL,
                content=f"Kelemahan/celah dalam framing masalah: {w}",
                confidence=0.65
            ))

        return thoughts, contradictions

    def _decompose(self, problem: str) -> List[str]:
        parts = problem.replace("?", "").replace(".", "").split(" dan ")
        if len(parts) == 1:
            words = problem.split()
            mid = len(words) // 2
            return [
                f"Aspek pertama: {' '.join(words[:mid])}",
                f"Aspek kedua: {' '.join(words[mid:])}",
                "Hubungan antar aspek"
            ]
        return [f"Komponen: {p.strip()}" for p in parts]

    def _find_assumptions(self, problem: str, context: Dict) -> List[str]:
        assumptions = ["Masalah memiliki solusi yang dapat ditemukan"]
        if not context:
            assumptions.append("Tidak ada konteks tambahan yang mempengaruhi")
        if "tidak" in problem.lower() or "bukan" in problem.lower():
            assumptions.append("Negasi dalam masalah mungkin membalikkan logika utama")
        return assumptions

    def _is_contradictory(self, a: str, b: str) -> bool:
        neg_markers = {"tidak", "bukan", "tanpa", "gagal"}
        a_neg = any(w in a.lower() for w in neg_markers)
        b_neg = any(w in b.lower() for w in neg_markers)
        if a_neg != b_neg and len(set(a.split()) & set(b.split())) > 2:
            return True
        return False

    def _identify_weaknesses(self, problem: str) -> List[str]:
        weaknesses = []
        if len(problem.split()) < 5:
            weaknesses.append("Framing masalah terlalu singkat, mungkin kurang spesifik")
        if "?" not in problem:
            weaknesses.append("Tidak ada pertanyaan eksplisit – tujuan bisa ambigu")
        return weaknesses


class InferenceEngine:
    def infer(self, thoughts: List[Thought], hypotheses: List[Hypothesis]) -> List[Thought]:
        inferences = []

        high_conf = [t for t in thoughts if t.confidence >= 0.8]
        if len(high_conf) >= 2:
            deduction = f"Deduksi dari {len(high_conf)} premis kuat: kemungkinan ada pola konsisten"
            inferences.append(Thought(
                layer=ThinkingLayer.INFERENTIAL,
                content=deduction,
                confidence=min(t.confidence for t in high_conf),
                supports=[t.id for t in high_conf]
            ))

        low_conf = [t for t in thoughts if t.confidence < 0.7]
        if low_conf:
            induction = (
                f"Induksi: {len(low_conf)} elemen berconfidence rendah → "
                "generalisasi perlu kehati-hatian ekstra"
            )
            inferences.append(Thought(
                layer=ThinkingLayer.INFERENTIAL,
                content=induction,
                confidence=0.6
            ))

        if hypotheses:
            best = max(hypotheses, key=lambda h: h.net_confidence())
            inferences.append(Thought(
                layer=ThinkingLayer.INFERENTIAL,
                content=(
                    f"Abduktif: hipotesis terkuat adalah '{best.statement}' "
                    f"(confidence={best.net_confidence():.2f})"
                ),
                confidence=best.net_confidence()
            ))

        return inferences


class HypothesisGenerator:
    def generate(self, problem: str, thoughts: List[Thought]) -> List[Hypothesis]:
        hypotheses: List[Hypothesis] = []

        hypotheses.append(Hypothesis(
            statement=f"Pendekatan langsung terhadap '{problem[:50]}' adalah rute optimal",
            confidence=0.7,
            evidence_for=[t.content for t in thoughts if t.confidence > 0.8][:2]
        ))

        hypotheses.append(Hypothesis(
            statement=f"Masalah '{problem[:50]}' mungkin sebenarnya adalah gejala masalah yang lebih dalam",
            confidence=0.5,
            evidence_for=[t.content for t in thoughts if t.layer == ThinkingLayer.CRITICAL][:2]
        ))

        hypotheses.append(Hypothesis(
            statement=f"Tidak ada solusi tunggal untuk '{problem[:40]}' — butuh solusi hibrida",
            confidence=0.4,
            evidence_for=[],
            evidence_against=[t.content for t in thoughts if t.confidence > 0.85][:1]
        ))

        for h in hypotheses:
            if h.net_confidence() >= 0.65:
                h.status = "supported"
            elif h.net_confidence() <= 0.3:
                h.status = "refuted"
            else:
                h.status = "uncertain"

        return hypotheses


class MetaCognition:
    def reflect(self, chain: "ReasoningChain") -> List[Thought]:
        reflections = []

        confidences = [t.confidence for t in chain.thoughts]
        avg_conf = sum(confidences) / len(confidences) if confidences else 0
        std_conf = math.sqrt(
            sum((c - avg_conf)**2 for c in confidences) / len(confidences)
        ) if confidences else 0

        reflections.append(Thought(
            layer=ThinkingLayer.METACOGNITIVE,
            content=(
                f"Kualitas rantai pikir: rata-rata kepercayaan={avg_conf:.2f}, "
                f"standar deviasi={std_conf:.2f} "
                f"({'terlalu seragam — kurang kritis' if std_conf < 0.05 else 'variasi sehat'})"
            ),
            confidence=0.9
        ))

        layer_counts: Dict[str, int] = defaultdict(int)
        for t in chain.thoughts:
            layer_counts[t.layer.name] += 1

        dominant = max(layer_counts, key=layer_counts.get) if layer_counts else "—"
        if layer_counts.get(dominant, 0) > len(chain.thoughts) * 0.5:
            reflections.append(Thought(
                layer=ThinkingLayer.METACOGNITIVE,
                content=f"Peringatan bias: lapisan '{dominant}' mendominasi (>50%) — perspektif lain mungkin terabaikan",
                confidence=0.85
            ))

        activated = set(layer_counts.keys())
        all_layers = {l.name for l in ThinkingLayer}
        missing = all_layers - activated
        if missing:
            reflections.append(Thought(
                layer=ThinkingLayer.METACOGNITIVE,
                content=f"Lapisan yang belum aktif: {', '.join(missing)} — pertimbangkan eksplorasi lebih lanjut",
                confidence=0.8
            ))

        if chain.iterations < 2:
            reflections.append(Thought(
                layer=ThinkingLayer.METACOGNITIVE,
                content="Iterasi terlalu sedikit — kesimpulan mungkin prematur",
                confidence=0.75
            ))

        return reflections


class Synthesizer:

    def synthesize(self, chain: "ReasoningChain") -> Tuple[str, float]:
        best_hypothesis = max(
            chain.hypotheses,
            key=lambda h: h.net_confidence(),
            default=None
        )

        layer_weights = {
            ThinkingLayer.SURFACE:       0.05,
            ThinkingLayer.ANALYTICAL:    0.15,
            ThinkingLayer.CRITICAL:      0.20,
            ThinkingLayer.INFERENTIAL:   0.20,
            ThinkingLayer.CREATIVE:      0.10,
            ThinkingLayer.METACOGNITIVE: 0.10,
            ThinkingLayer.SYNTHETIC:     0.20,
        }

        weighted_conf = 0.0
        total_weight = 0.0
        for t in chain.thoughts:
            w = layer_weights.get(t.layer, 0.1)
            weighted_conf += t.confidence * w
            total_weight += w

        final_confidence = (weighted_conf / total_weight) if total_weight > 0 else 0.5
        contradiction_penalty = len(chain.contradictions) * 0.05
        final_confidence = max(0.0, final_confidence - contradiction_penalty)

        parts = [f"Analisis terhadap '{chain.problem}'"]

        if best_hypothesis:
            parts.append(
                f"mengarah pada hipotesis utama: {best_hypothesis.statement} "
                f"(status: {best_hypothesis.status}, confidence: {best_hypothesis.net_confidence():.2f})"
            )

        if chain.contradictions:
            parts.append(
                f"Ditemukan {len(chain.contradictions)} kontradiksi yang memerlukan "
                "penyelidikan lebih lanjut"
            )

        if chain.backtrack_log:
            parts.append(
                f"Penalaran di-revisi {len(chain.backtrack_log)}x selama proses "
                "(backtracking aktif)"
            )

        if final_confidence < 0.5:
            parts.append(
                "Kepercayaan rendah — kesimpulan bersifat tentatif, "
                "disarankan input data tambahan"
            )

        conclusion = ". ".join(parts) + "."
        return conclusion, final_confidence


# ──────────────────────────────────────────────
#  CHAIN OF THOUGHT UTAMA
# ──────────────────────────────────────────────

class ChainOfThought:

    def __init__(
        self,
        memory_router=None,
        max_depth: int = 4,
        max_iterations: int = 3,
        confidence_threshold: float = 0.6,
        log_path: str = "arint/memory/consciousness/current.log",
        enable_backtrack: bool = True,
    ):
        self.memory_router = memory_router
        self.max_depth = max_depth
        self.max_iterations = max_iterations
        self.confidence_threshold = confidence_threshold
        self.log_path = log_path
        self.enable_backtrack = enable_backtrack

        self._surface    = SurfaceAnalyzer()
        self._deep       = DeepAnalyzer()
        self._inference  = InferenceEngine()
        self._hypothesis = HypothesisGenerator()
        self._meta       = MetaCognition()
        self._synthesize = Synthesizer()

    # ── API Publik ──────────────────────────────

    def reason(
        self,
        problem: str,
        context: Optional[Dict[str, Any]] = None,
        depth: int = 0,
    ) -> ReasoningChain:
        context = context or {}
        chain = ReasoningChain(problem=problem, depth=depth)
        chain.status = ReasoningStatus.ACTIVE

        try:
            chain = self._run_thinking_cycle(chain, context, depth)
            self._persist(chain)
        except Exception as e:
            logger.error(f"Reasoning gagal: {e}")
            chain.status = ReasoningStatus.DEADLOCKED
            chain.conclusion = f"Penalaran terhenti karena error: {e}"
            
        if hasattr(self, 'confidence_multiplier'):
            chain.confidence *= self.confidence_multiplier
            chain.confidence = max(0.0, min(1.0, chain.confidence))

        if hasattr(self, 'memory_router') and self.memory_router:
            similar = self.memory_router.search_similar(chain.conclusion, limit=3)
            if similar:
                avg_outcome = sum(s.get('outcome', 0.5) for s in similar) / len(similar)
                chain.confidence = (chain.confidence + avg_outcome) / 2

        return chain

    def reason_deep(
        self,
        problem: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[ReasoningChain]:
        context = context or {}
        surface_thoughts = self._surface.analyze(problem, context)
        sub_problems = self._extract_sub_problems(surface_thoughts, problem)

        chains: List[ReasoningChain] = []
        for i, sub in enumerate(sub_problems):
            logger.info(f"[DeepReason] Sub-masalah {i+1}/{len(sub_problems)}: {sub}")
            sub_chain = self.reason(
                problem=sub,
                context={**context, "parent_problem": problem, "sub_index": i},
                depth=1,
            )
            chains.append(sub_chain)

        integrated_context = {
            **context,
            "sub_conclusions": [c.conclusion for c in chains],
            "sub_confidences": [c.confidence for c in chains],
        }
        master_chain = self.reason(problem, context=integrated_context, depth=2)
        chains.append(master_chain)

        return chains

    def get_steps(self, chain: ReasoningChain) -> List[str]:
        steps = []
        for layer in ThinkingLayer:
            layer_thoughts = [t for t in chain.thoughts if t.layer == layer]
            if layer_thoughts:
                steps.append(f"[{layer.name}]")
                steps.extend(f"  → {t.content}" for t in layer_thoughts)
        steps.append(f"\n[KESIMPULAN] {chain.conclusion}")
        steps.append(f"[KEPERCAYAAN] {chain.confidence:.0%}")
        steps.append(f"[STATUS] {chain.status.value}")
        return steps

    # ── Logika Internal ─────────────────────────

    def _run_thinking_cycle(
        self,
        chain: ReasoningChain,
        context: Dict,
        depth: int,
    ) -> ReasoningChain:

        iteration = 0
        while iteration < self.max_iterations:
            chain.iterations = iteration + 1

            chain.thoughts += self._surface.analyze(chain.problem, context)

            deep_thoughts, contradictions = self._deep.analyze(
                chain.problem, chain.thoughts, context
            )
            chain.thoughts += deep_thoughts
            chain.contradictions += contradictions

            if not chain.hypotheses:
                chain.hypotheses = self._hypothesis.generate(chain.problem, chain.thoughts)
            else:
                self._update_hypotheses(chain)

            chain.thoughts += self._inference.infer(chain.thoughts, chain.hypotheses)

            chain.thoughts += self._meta.reflect(chain)

            conclusion, confidence = self._synthesize.synthesize(chain)
            chain.conclusion  = conclusion
            chain.confidence  = confidence

            if confidence >= self.confidence_threshold and not chain.contradictions:
                break

            if self.enable_backtrack and confidence < self.confidence_threshold:
                note = (
                    f"Iterasi {iteration+1}: confidence={confidence:.2f} < "
                    f"threshold={self.confidence_threshold} → backtrack & perluas konteks"
                )
                chain.backtrack_log.append(note)
                logger.info(f"[Backtrack] {note}")
                context = self._expand_context(context, chain)

            iteration += 1

        if chain.confidence >= self.confidence_threshold:
            chain.status = ReasoningStatus.RESOLVED
        elif chain.backtrack_log:
            chain.status = ReasoningStatus.REVISED
        else:
            chain.status = ReasoningStatus.DEADLOCKED

        return chain

    def _update_hypotheses(self, chain: ReasoningChain) -> None:
        for h in chain.hypotheses:
            for t in chain.thoughts:
                if t.layer in (ThinkingLayer.INFERENTIAL, ThinkingLayer.CRITICAL):
                    if any(kw in t.content.lower() for kw in h.statement.lower().split()[:3]):
                        if t.confidence > 0.7:
                            h.evidence_for.append(t.content[:80])
                        else:
                            h.evidence_against.append(t.content[:80])
            if h.net_confidence() >= 0.65:
                h.status = "supported"
            elif h.net_confidence() <= 0.3:
                h.status = "refuted"
            else:
                h.status = "uncertain"

    def _expand_context(self, context: Dict, chain: ReasoningChain) -> Dict:
        critical_thoughts = [
            t.content for t in chain.thoughts
            if t.layer == ThinkingLayer.CRITICAL and t.confidence > 0.6
        ]
        return {
            **context,
            "previous_contradictions": chain.contradictions,
            "critical_insights": critical_thoughts[:3],
            "last_confidence": chain.confidence,
        }

    def _extract_sub_problems(
        self, surface_thoughts: List[Thought], problem: str
    ) -> List[str]:
        keywords = [
            t.content.replace("Kata kunci utama: ", "").split(", ")
            for t in surface_thoughts
            if "Kata kunci utama" in t.content
        ]
        flat_kw = [k for group in keywords for k in group]

        if not flat_kw:
            words = problem.split()
            return [
                f"Aspek: {' '.join(words[:len(words)//2])}",
                f"Aspek: {' '.join(words[len(words)//2:])}",
            ]

        return [f"Apa implikasi dari '{kw}' dalam konteks: {problem}?" for kw in flat_kw[:3]]

    def _persist(self, chain: ReasoningChain) -> None:
        entry = {
            "timestamp": chain.timestamp,
            "type": "chain_of_thought_v2",
            "summary": chain.summary(),
        }
        try:
            import os
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Gagal menyimpan chain-of-thought: {e}")

        if self.memory_router and hasattr(self.memory_router, "store"):
            try:
                self.memory_router.store(entry)
            except Exception as e:
                logger.warning(f"memory_router.store() gagal: {e}")