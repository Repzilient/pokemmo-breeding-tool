import unittest
import os
from typing import List, Dict, Any # PianoCompleto will be used in the new function

import core_engine
from structures import PokemonPosseduto, PianoValutato, PokemonRichiesto, PianoCompleto # Added PianoCompleto
from plan_evaluator import valuta_piani

def _scrivi_report_piani_generati(piani: List[PianoCompleto], nome_file: str):
    """
    Scrive un file di testo dettagliato per i piani generati (non valutati).
    """
    print(f"\n[DEBUG] Scrittura del report dei piani generati su '{nome_file}'...")
    with open(nome_file, 'w', encoding='utf-8') as f:
        f.write("Report Piani Generati\n")
        f.write(f"Totale piani generati: {len(piani)}\n\n")

        for i, piano_completo in enumerate(piani):
            f.write("-" * 80 + "\n")
            f.write(f"POSIZIONE: {i+1} | ID PIANO: {piano_completo.id_piano}\n")
            f.write(f"TARGET: {piano_completo.ivs_target} - Natura: {piano_completo.natura_target}\n")
            f.write(f"Legenda Ruoli -> Statistiche: {piano_completo.legenda_ruoli}\n\n")

            f.write("Struttura del Piano di Breeding:\n")
            for livello in piano_completo.livelli:
                f.write(f"  --- Livello {livello.livello_id} ---\n")
                for accoppiamento in livello.accoppiamenti:
                    genitore1_str = accoppiamento.genitore1.nome_generico
                    genitore2_str = accoppiamento.genitore2.nome_generico
                    figlio_str = accoppiamento.figlio.nome_generico
                    f.write(f"    - {genitore1_str:<25} + {genitore2_str:<25} -> {figlio_str}\n")
                f.write("\n") # Newline after each level's accoppiamenti
            f.write("\n") # Two newlines after each plan
    print(f"[DEBUG] Report generati '{nome_file}' creato con successo.")


def _scrivi_report_piani_valutati(piani: List[PianoValutato], nome_file: str):
    """
    Scrive un file di testo dettagliato usando la mappa di assegnazioni per slot.
    """
    print(f"\n[DEBUG] Scrittura del report di valutazione completo su '{nome_file}'...")
    with open(nome_file, 'w', encoding='utf-8') as f:
        f.write(f"Totale piani analizzati: {len(piani)}\n\n")

        for i, piano_valutato in enumerate(piani):
            piano = piano_valutato.piano_originale
            f.write("-" * 80 + "\n")
            f.write(f"POSIZIONE: {i+1} | ID PIANO: {piano.id_piano} | PUNTEGGIO: {piano_valutato.punteggio:.2f}\n")
            f.write("-" * 80 + "\n")

            f.write(f"Legenda Ruoli -> Statistiche: {piano.legenda_ruoli}\n")
            f.write(f"Pokémon Posseduti Usati: {', '.join(sorted(list(piano_valutato.pokemon_usati))) or 'Nessuno'}\n\n")

            f.write("Assegnazioni (Requisito -> Posseduto):\n")
            if piano_valutato.mappa_assegnazioni:
                # Ordina gli slot per un report consistente
                sorted_slots = sorted(piano_valutato.mappa_assegnazioni.keys())
                for slot_key in sorted_slots:
                    l_idx, a_idx, p_num = slot_key
                    # Recupera l'oggetto PokemonRichiesto corretto usando lo slot
                    genitore_obj = piano.livelli[l_idx].accoppiamenti[a_idx].genitore1 if p_num == 1 else piano.livelli[l_idx].accoppiamenti[a_idx].genitore2
                    posseduto_id = piano_valutato.mappa_assegnazioni[slot_key]
                    f.write(f"  - {genitore_obj.nome_generico:<15} -> {posseduto_id}\n")
            else:
                f.write("  - Nessuna assegnazione possibile.\n")

            f.write("\nStruttura del Piano di Breeding:\n")
            for l_idx, livello in enumerate(piano.livelli):
                f.write(f"  --- Livello {livello.livello_id} ---\n")
                for a_idx, acc in enumerate(livello.accoppiamenti):
                    # Genitore 1
                    slot_key1 = (l_idx, a_idx, 1)
                    genitore1_str = acc.genitore1.nome_generico
                    if slot_key1 in piano_valutato.mappa_assegnazioni:
                        genitore1_str = f"*{piano_valutato.mappa_assegnazioni[slot_key1]}*"

                    # Genitore 2
                    slot_key2 = (l_idx, a_idx, 2)
                    genitore2_str = acc.genitore2.nome_generico
                    if slot_key2 in piano_valutato.mappa_assegnazioni:
                        genitore2_str = f"*{piano_valutato.mappa_assegnazioni[slot_key2]}*"

                    figlio_str = acc.figlio.nome_generico
                    f.write(f"    - {genitore1_str:<25} + {genitore2_str:<25} -> {figlio_str}\n")
            f.write("\n\n")
    print(f"[DEBUG] Report '{nome_file}' creato con successo.")


class TestPlanEvaluator(unittest.TestCase):
    def test_manual_charizard_scenario(self):
        print("\n" + "="*70)
        print("--- ESECUZIONE TEST: SCENARIO CHARIZARD 4IV+N (MANUALE) ---")
        print("="*70)

        pokemon_target_ivs = ["Attacco Speciale", "Difesa", "Difesa Speciale", "Velocità"]
        pokemon_target_natura = "Adamant"
        num_target_ivs = len(pokemon_target_ivs)

        print(f"\n[FASE 1] Target: Charizard con {num_target_ivs} IVs {pokemon_target_ivs} e Natura {pokemon_target_natura}")

        piani_generati = core_engine.esegui_generazione(
            num_iv=num_target_ivs,
            ivs_desiderate=pokemon_target_ivs,
            natura_desiderata=pokemon_target_natura
        )

        if piani_generati:
             _scrivi_report_piani_generati(piani_generati, "report_piani_generati_charizard.txt")

        self.assertTrue(len(piani_generati) > 0, "Il core_engine non ha generato piani per 4IV+Natura.")

        pokemon_posseduti = [
            PokemonPosseduto(id_utente="P1_M_Ada_AS_V", specie="Charizard", ivs=["Attacco Speciale", "Velocità"], natura="Adamant", sesso="M"),
            PokemonPosseduto(id_utente="P2_M_Quiet_AS_V", specie="Charizard", ivs=["Attacco Speciale", "Velocità"], natura="Quiet", sesso="M"),
            PokemonPosseduto(id_utente="P3_F_Quiet_DS_D", specie="Charizard", ivs=["Difesa Speciale", "Difesa"], natura="Quiet", sesso="F"),
            PokemonPosseduto(id_utente="P4_F_Quiet_V", specie="Charizard", ivs=["Velocità"], natura="Quiet", sesso="F")
        ]
        print("\n[FASE 2] Pokémon Posseduti per la valutazione (scenario Charizard):")
        for p in pokemon_posseduti:
            print(f"  - {p.id_utente}: IVs={sorted(p.ivs) or 'N/A'}, Natura={p.natura or 'N/A'}")

        piani_valutati = valuta_piani(piani_generati, pokemon_posseduti)

        _scrivi_report_piani_valutati(piani_valutati, "report_piani_valutati_charizard.txt")

        self.assertTrue(len(piani_valutati) > 0, "Il plan_evaluator non ha restituito piani valutati.")

        miglior_piano = piani_valutati[0]
        self.assertTrue(miglior_piano.punteggio > 0, "Il piano migliore deve avere un punteggio positivo.")

        print("\n" + "-"*70)
        print("--- RISULTATO: DETTAGLIO DEL PIANO MIGLIORE (SCENARIO CHARIZARD) ---")
        print(f"Punteggio ottenuto: {miglior_piano.punteggio:.2f}")
        print(f"Pokémon Posseduti utilizzati: {', '.join(sorted(list(miglior_piano.pokemon_usati))) or 'Nessuno'}")
        print("-" * 70)

if __name__ == '__main__':
    # Esecuzione del test scenario Charizard (come prima)
    suite = unittest.TestSuite()
    suite.addTest(TestPlanEvaluator('test_manual_charizard_scenario'))
    runner = unittest.TextTestRunner(verbosity=2)
    print("Running Charizard scenario test...")
    runner.run(suite)
    print("\nFinished Charizard scenario test.\n")

    # Nuove attività di generazione piani campione
    print("--- Avvio Generazione Piani Campione ---")
    ALL_IVS = ["HP", "Attack", "Defense", "Sp. Atk", "Sp. Def", "Speed"]
    SAMPLE_NATURE = "Adamant"

    # Generazione Piani 3IV+N
    ivs_3 = ALL_IVS[:3]
    print(f"\n--- Generazione Piani 3IV+N ({ivs_3}, Natura: {SAMPLE_NATURE}) ---")
    piani_3iv = core_engine.esegui_generazione(num_iv=3, ivs_desiderate=ivs_3, natura_desiderata=SAMPLE_NATURE)
    if piani_3iv:
        _scrivi_report_piani_generati(piani_3iv, "report_piani_generati_3IV.txt")
    else:
        print("Nessun piano generato per 3IV+N.")

    # Generazione Piani 4IV+N
    ivs_4 = ALL_IVS[:4]
    print(f"\n--- Generazione Piani 4IV+N ({ivs_4}, Natura: {SAMPLE_NATURE}) ---")
    piani_4iv = core_engine.esegui_generazione(num_iv=4, ivs_desiderate=ivs_4, natura_desiderata=SAMPLE_NATURE)
    if piani_4iv:
        _scrivi_report_piani_generati(piani_4iv, "report_piani_generati_4IV.txt")
    else:
        print("Nessun piano generato per 4IV+N.")

    # Generazione Piani 5IV+N
    ivs_5 = ALL_IVS[:5]
    print(f"\n--- Generazione Piani 5IV+N ({ivs_5}, Natura: {SAMPLE_NATURE}) ---")
    piani_5iv = core_engine.esegui_generazione(num_iv=5, ivs_desiderate=ivs_5, natura_desiderata=SAMPLE_NATURE)
    if piani_5iv:
        _scrivi_report_piani_generati(piani_5iv, "report_piani_generati_5IV.txt")
    else:
        print("Nessun piano generato per 5IV+N.")

    print("\n--- Generazione Piani Campione Completata ---")
