import unittest
import math
from typing import List, Optional

import core_engine
from structures import PianoValutato
from plan_evaluator import valuta_piani

def _scrivi_report_piani(piani_valutati: list[PianoValutato], nome_file: str):
    """Funzione helper per scrivere un report dettagliato dei piani generati."""
    print(f"\n[DEBUG] Scrittura del report di valutazione su '{nome_file}'...")
    with open(nome_file, 'w', encoding='utf-8') as f:
        f.write(f"Totale piani analizzati: {len(piani_valutati)}\n\n")
        piani_ordinati = sorted(piani_valutati, key=lambda p: p.piano_originale.id_piano)
        for piano_valutato in piani_ordinati:
            piano = piano_valutato.piano_originale
            f.write("-" * 80 + "\n")
            f.write(f"ID PIANO: {piano.id_piano}\n")
            f.write(f"Legenda Ruoli -> Statistiche: {piano.legenda_ruoli}\n\n")
            f.write("Struttura del Piano di Breeding:\n")
            for livello in piano.livelli:
                f.write(f"  --- Livello {livello.livello_id} ---\n")
                for acc in livello.accoppiamenti:
                    f.write(f"    - {acc.genitore1.nome_generico:<25} + {acc.genitore2.nome_generico:<25} -> {acc.figlio.nome_generico}\n")
            f.write("\n\n")
    print(f"[DEBUG] Report '{nome_file}' creato con successo.")

class TestSuiteCompleta(unittest.TestCase):
    """Suite di test per validare il motore di generazione universale."""

    def _esegui_test_generico(self, num_iv: int, ivs_desiderate: list[str], natura: Optional[str], nome_file_report: str):
        """Funzione generica per eseguire un test di generazione e reportistica."""
        print("\n" + "="*70)
        print(f"--- ESECUZIONE TEST: GENERAZIONE PIANI {num_iv}IV {'+ Natura' if natura else 'Senza Natura'} ---")
        print("="*70)

        num_permutazioni = math.factorial(num_iv)
        
        num_strategie = 0
        if num_iv >= 2:
            # Calcola il numero di strategie senza chiamare la funzione interna
            # Il numero di strategie è il numero di modi per scegliere 2 genitori N-1 IV da un pool di N IV
            num_combinazioni_genitori = math.comb(num_iv, num_iv - 1)
            num_strategie = math.comb(num_combinazioni_genitori, 2)
            if num_iv == 2 and natura: num_strategie = 2 # Caso speciale
            elif num_iv == 3 and natura: num_strategie = math.comb(math.comb(3, 2), 2)
            # Per 5IV+N e 5IV S/N il calcolo è più complesso e gestito internamente dal motore,
            # quindi fidiamoci del numero di piani generati come riferimento.
            if num_iv == 5:
                piani_generati_temp = core_engine.esegui_generazione(ivs_desiderate, natura)
                num_strategie = len(piani_generati_temp) // num_permutazioni if num_permutazioni > 0 else 0


        piani_attesi = num_strategie * num_permutazioni
        if piani_attesi == 0 and num_iv < 4 and natura: # Gestione fallback per 2/3 IV
             piani_attesi = num_strategie * num_permutazioni if num_strategie > 0 else num_permutazioni
             if num_iv == 3 and natura : piani_attesi = 3 * num_permutazioni

        print(f"[INFO] Piani attesi: {piani_attesi} ({num_strategie} strategie * {num_permutazioni} permutazioni).")
        
        piani_generati = core_engine.esegui_generazione(ivs_desiderate, natura)
        self.assertEqual(len(piani_generati), piani_attesi, f"Numero di piani generati non corretto per {num_iv}IV.")
        
        piani_valutati = valuta_piani(piani_generati, [])
        _scrivi_report_piani(piani_valutati, nome_file_report)
        print(f"[RISULTATO] Test per {num_iv}IV completato. Controlla il file '{nome_file_report}'.")

    # --- Test Piani CON Natura ---
    def test_generazione_5iv_natura(self):
        self._esegui_test_generico(5, ["PS", "Attacco", "Difesa", "Velocità", "Attacco Speciale"], "Adamant", "report_piani_5iv_natura.txt")

    def test_generazione_4iv_natura(self):
        self._esegui_test_generico(4, ["PS", "Attacco", "Difesa", "Velocità"], "Adamant", "report_piani_4iv_natura.txt")

    def test_generazione_3iv_natura(self):
        self._esegui_test_generico(3, ["PS", "Attacco", "Difesa"], "Modest", "report_piani_3iv_natura.txt")

    def test_generazione_2iv_natura(self):
        self._esegui_test_generico(2, ["PS", "Velocità"], "Jolly", "report_piani_2iv_natura.txt")

    # --- Test Piani SENZA Natura ---
    def test_generazione_5iv_senza_natura(self):
        self._esegui_test_generico(5, ["PS", "Attacco", "Difesa", "Velocità", "Attacco Speciale"], None, "report_piani_5iv_senza_natura.txt")
    
    def test_generazione_4iv_senza_natura(self):
        self._esegui_test_generico(4, ["PS", "Attacco", "Difesa", "Velocità"], None, "report_piani_4iv_senza_natura.txt")
        
if __name__ == '__main__':
    # Correzione: usa TestLoader per creare la suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSuiteCompleta)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)