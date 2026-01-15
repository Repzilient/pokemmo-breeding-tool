from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set

# --- Strutture Dati Centralizzate ---

@dataclass(frozen=True, eq=True)
class PokemonRichiesto:
    """Rappresenta un Pokémon richiesto in un punto del piano."""
    ruoli_iv: Tuple[str, ...] = field(default_factory=tuple)
    ruolo_natura: Optional[str] = None

    def __post_init__(self):
        # Assicura che i ruoli siano sempre ordinati per garantire coerenza nell'hashing
        object.__setattr__(self, 'ruoli_iv', tuple(sorted(self.ruoli_iv)))

    @property
    def nome_generico(self) -> str:
        parts = []
        if self.ruolo_natura:
            parts.append(self.ruolo_natura)
        parts.extend(sorted(list(self.ruoli_iv)))
        role_str = "".join(parts)
        iv_count = len(self.ruoli_iv)
        nat_str = "+N" if self.ruolo_natura else ""
        return f"{role_str} [{iv_count}IV{nat_str}]"

@dataclass
class Accoppiamento:
    """Rappresenta un singolo accoppiamento."""
    genitore1: PokemonRichiesto
    genitore2: PokemonRichiesto
    figlio: PokemonRichiesto

@dataclass
class Livello:
    """Raggruppa accoppiamenti allo stesso stadio."""
    livello_id: int
    accoppiamenti: List[Accoppiamento] = field(default_factory=list)

@dataclass
class PianoCompleto:
    """Rappresenta l'intero albero di breeding."""
    id_piano: int
    ivs_target: List[str]
    natura_target: Optional[str]
    legenda_ruoli: Dict[str, str]
    livelli: List[Livello] = field(default_factory=list)

@dataclass
class PokemonPosseduto:
    """Rappresenta un Pokémon che l'utente possiede realmente."""
    id_utente: str
    ivs: List[str] = field(default_factory=list)
    natura: Optional[str] = None
    specie: Optional[str] = None
    sesso: Optional[str] = None

    def __post_init__(self):
        self.ivs.sort()

@dataclass
class PianoValutato:
    """Contiene un piano generato e i risultati della sua valutazione."""
    piano_originale: PianoCompleto
    punteggio: float = 0.0
    costo_totale: int = 0
    pokemon_usati: Set[str] = field(default_factory=set)
    # --- CORREZIONE CHIAVE ---
    # La mappa ora usa l'ID di memoria dell'oggetto PokemonRichiesto come chiave
    # per garantire l'univocità di ogni "slot" genitore nel piano.
    mappa_assegnazioni: Dict[int, str] = field(default_factory=dict)
    # Mappa delle decisioni di acquisto: {id_nodo: "Descrizione acquisto"}
    mappa_acquisti: Dict[int, str] = field(default_factory=dict)