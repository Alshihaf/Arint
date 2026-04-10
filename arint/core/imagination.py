
# core/imagination.py
# (Konten yang sama persis seperti sebelumnya, dengan perubahan di bawah)
# ... (semua kode sampai ke @dataclass SimulationOutcome)

@dataclass
class SimulationOutcome:
    """
    Satu cabang/node dalam pohon simulasi.
    Sekarang mencakup representasi vektor dari deskripsi.
    """
    outcome_id: str
    description: str
    probability: float
    impact_score: float
    confidence: float
    layer: int
    parent_id: Optional[str] = None
    
    # PERUBAHAN UTAMA: Representasi Vektor
    outcome_vector: Optional[np.ndarray] = field(default=None, repr=False)

    conditions: Dict[str, Any] = field(default_factory=dict)
    children: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # ... (sisa metode seperti weighted_score, to_dict, dll. tetap sama)
    # Kita perlu menambahkan serialisasi/deserialisasi untuk np.ndarray jika diperlukan
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.outcome_vector is not None:
            d["outcome_vector"] = self.outcome_vector.tolist() # Serialisasi NumPy array ke list
        d["weighted_score"] = round(self.weighted_score, 6)
        return d
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimulationOutcome":
        if "outcome_vector" in data and data["outcome_vector"] is not None:
            data["outcome_vector"] = np.array(data["outcome_vector"])
        return cls(**data)


# ... (semua kode sampai ke class SimulationEngine)

class SimulationEngine:
    # ... (semua kode sampai ke _expand_layer)

    def _expand_layer(
        self,
        scenario: str,
        layer: int,
        parents: List[SimulationOutcome],
        branch_factor: int,
        parameters: Dict[str, Any],
        rng: random.Random,
        vectorizer: Optional[Callable[[str], np.ndarray]] = None, # Tambahkan vectorizer
    ) -> Generator[SimulationOutcome, None, None]:
        # ... (logika yang ada untuk child_prob, impact, confidence)
        
        for parent in parents:
            # ... (loop internal yang ada)
            for i in range(branch_factor):
                # ... (semua kalkulasi yang ada)
                child_id = self._make_id(scenario, layer, i, parent.outcome_id)
                child_desc = self._generate_description(scenario, layer, i, parameters, rng)
                
                # PERUBAHAN UTAMA: Vektorisasi saat pembuatan
                child_vector = vectorizer(child_desc) if vectorizer else None
                
                child = SimulationOutcome(
                    outcome_id=child_id,
                    description=child_desc,
                    probability=round(child_prob, 6),
                    impact_score=round(impact, 6),
                    confidence=round(confidence, 6),
                    layer=layer,
                    parent_id=parent.outcome_id,
                    outcome_vector=child_vector, # Simpan vektor
                    conditions=self._sample_conditions(parameters, rng),
                    metadata={
                        "branch_index": i,
                        "depth_decay": round(1.0 / (layer + 1), 4),
                    },
                )
                
                # ... (sisa logika)
                yield child
    
    def simulate_layered(
        self,
        scenario: str,
        parameters: Dict[str, Any],
        n_layers: int,
        branch_factor: int,
        vectorizer: Optional[Callable[[str], np.ndarray]] = None, # Terima vectorizer
        seed: Optional[int] = None,
    ) -> Tuple[List[SimulationOutcome], Dict[str, Any]]:
        # ... (logika yang ada)
        
        # PERUBAHAN UTAMA: Vektorisasi root
        root_desc = f"[ROOT] {scenario[:80]}"
        root_vector = vectorizer(root_desc) if vectorizer else None
        
        root = SimulationOutcome(
            outcome_id=root_id,
            description=root_desc,
            probability=1.0,
            impact_score=0.0,
            confidence=1.0,
            layer=0,
            outcome_vector=root_vector, # Simpan vektor root
            conditions=parameters,
        )
        
        # ... (logika yang ada)
        
        for layer in range(1, n_layers + 1):
            # ... (logika yang ada)
            layer_outcomes: List[SimulationOutcome] = list(
                self._expand_layer(
                    scenario, layer, current_layer, adaptive_bf, parameters, rng, vectorizer=vectorizer # Teruskan vectorizer
                )
            )
            # ... (sisa logika)
            
        return all_outcomes, stats
        
# ... (semua kode sampai ke class Imagination)

class Imagination:
    # ... (semua kode sampai ke __init__)
    def __init__(
        self,
        dream_module: Any = None,
        vectorizer: Optional[Callable[[str], np.ndarray]] = None, # Terima vectorizer
        storage_path: str = "ai_core/memory/dreams",
        max_layers: Optional[int] = None,
        branch_factor: int = 5,
        seed: Optional[int] = None,
    ) -> None:
        # ... (logika yang ada)
        self.vectorizer = vectorizer # Simpan vectorizer
        logger.info("Imagination siap — profil: %s", self.rm.get_profile())

    # ... (semua kode sampai ke simulate)
    
    def simulate(
        self,
        scenario: str,
        parameters: Dict[str, Any] = None,
        layers: Optional[int] = None,
        branch_factor: Optional[int] = None,
        use_cache: bool = True,
        persist: bool = True,
    ) -> SimulationResult:
        # ... (logika yang ada)
        
        t0 = time.perf_counter()
        outcomes, stats = self.engine.simulate_layered(
            scenario, params, n_layers, bf, vectorizer=self.vectorizer, seed=self.seed # Teruskan vectorizer
        )
        
        # ... (sisa logika)
        
        return result
        
    # ... (sisa kelas)
