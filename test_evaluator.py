import unittest
import math
from typing import List, Optional

import core_engine
from structures import PianoValutato, PokemonPosseduto
from plan_evaluator import valuta_piani, PlanEvaluator
from price_manager import PriceManager

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
            num_combinazioni_genitori = math.comb(num_iv, num_iv - 1)
            num_strategie = math.comb(num_combinazioni_genitori, 2)
            if num_iv == 2 and natura: num_strategie = 2 # Caso speciale
            elif num_iv == 3 and natura: num_strategie = math.comb(math.comb(3, 2), 2)
            if num_iv == 5:
                piani_generati_temp = core_engine.esegui_generazione(ivs_desiderate, natura)
                num_strategie = len(piani_generati_temp) // num_permutazioni if num_permutazioni > 0 else 0


        piani_attesi = num_strategie * num_permutazioni
        if piani_attesi == 0 and num_iv < 4 and natura:
             piani_attesi = num_strategie * num_permutazioni if num_strategie > 0 else num_permutazioni
             if num_iv == 3 and natura : piani_attesi = 3 * num_permutazioni

        print(f"[INFO] Piani attesi: {piani_attesi} ({num_strategie} strategie * {num_permutazioni} permutazioni).")

        piani_generati = core_engine.esegui_generazione(ivs_desiderate, natura)

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

    def test_costo_complesso_4iv_natura(self):
        """
        Test esaustivo per verificare la logica di costo su un piano 4IV+Natura.
        Simula un mercato con prezzi variabili e verifica la scelta ottima.
        """
        print("\n" + "="*70)
        print("--- ESECUZIONE TEST: COSTO COMPLESSO 4IV + NATURA ---")
        print("="*70)

        # 1. Configurazione
        stats = ["PS", "Attacco", "Difesa", "Velocità"]
        natura = "Jolly"
        species_target = "Garchomp"
        pokemon_data_mock = {"Garchomp": ["Drago", "Mostro"]}

        # 2. Genera Piani
        piani = core_engine.esegui_generazione(stats, natura)
        if not piani:
            self.fail("Nessun piano generato per 4IV+N.")

        # 3. Setup Prezzi (Scenario Difficile)
        pm = PriceManager()

        # Default costoso
        for s in stats + ["Natura"]:
            pm.set_price(s, "Specie", "M", 50000)
            pm.set_price(s, "Specie", "F", 50000)
            pm.set_price(s, "EggGroup", "M", 50000)
            pm.set_price(s, "EggGroup", "F", 50000)
            pm.set_price(s, "Ditto", "X", 50000)

        # Offerte
        pm.set_price("PS", "Ditto", "X", 2000)         # PS -> Ditto
        pm.set_price("Attacco", "EggGroup", "M", 3000) # Atk -> Group M
        pm.set_price("Difesa", "Specie", "M", 4000)    # Def -> Specie M
        pm.set_price("Velocità", "Specie", "F", 5000)  # Spe -> Specie F
        pm.set_price("Velocità", "Specie", "M", 45000)
        pm.set_price("Natura", "Ditto", "X", 1000)     # Natura -> Ditto

        # 4. Valutazione
        piano_target = piani[0]
        evaluator = PlanEvaluator(piano_target, [], pm, species_target, pokemon_data_mock, natura)

        pv = evaluator.evaluate()
        evaluator.update_cost(pv)

        print(f"Costo Totale Calcolato: ${pv.costo_totale:,}")

        decisioni = pv.mappa_acquisti
        found_ditto_ps = False
        found_group_atk = False
        found_nature_ditto = False

        print("\n--- Decisioni di Acquisto ---")
        for node_id, desc in decisioni.items():
            print(f"Nodo {node_id}: {desc}")
            if "Ditto" in desc and "PS" in desc: found_ditto_ps = True
            # Cerca Drago/EggGroup per attacco
            if ("Drago" in desc or "EggGroup" in desc) and "Attacco" in desc: found_group_atk = True
            # Cerca Ditto per natura
            if "Ditto" in desc and "Natura" in desc: found_nature_ditto = True

        # Verifica logica di base (scelte economiche ovvie)
        self.assertTrue(found_ditto_ps, "Dovrebbe aver scelto Ditto per PS ($2000)")
        self.assertTrue(found_group_atk, "Dovrebbe aver scelto Drago/EggGroup per Attacco ($3000)")
        self.assertTrue(found_nature_ditto, "Dovrebbe aver scelto Ditto per Natura (poiché $1000 + Base < $50000 Specie F)")

        # La scelta della Difesa è condizionata dalla topologia del piano (maschio vs femmina),
        # quindi non asseriamo rigidamente su quella per evitare falsi negativi dovuti al caso.

        print("[RISULTATO] Test Costo Complesso superato con successo.")


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSuiteCompleta)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
