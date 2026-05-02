"""
intervention_fsm.py
===================
Automate à États Finis — Processus de validation d'intervention

DIAGRAMME :
    DEMANDE ──demande──► TECH1_ASSIGNE ──validation_tech2──► TECH2_VALIDE
                                                                    │
                                              validation_ia ◄───────┘
                                                    │
                                                    ▼
                                               IA_VALIDE ──terminer──► TERMINE
                                               
    Depuis n'importe quel état : annuler → ANNULE
"""

from transitions import Machine
from datetime import datetime


class InterventionFSM:
    """
    Gère le workflow de validation d'une intervention.
    Implique : Tech1 (demande) → Tech2 (valide) → IA (valide) → Terminé
    """

    STATES = [
        'DEMANDE',          # Intervention demandée, aucun technicien assigné
        'TECH1_ASSIGNE',    # Premier technicien a accepté l'intervention
        'TECH2_VALIDE',     # Deuxième technicien a validé (double vérification)
        'IA_VALIDE',        # L'IA a confirmé que l'intervention est pertinente
        'TERMINE',          # Intervention complétée avec succès
        'ANNULE',           # Intervention annulée à n'importe quelle étape
    ]

    TRANSITIONS = [
        # Flux normal de validation
        {'trigger': 'assigner_tech1',    'source': 'DEMANDE',        'dest': 'TECH1_ASSIGNE'},
        {'trigger': 'valider_tech2',     'source': 'TECH1_ASSIGNE',  'dest': 'TECH2_VALIDE'},
        {'trigger': 'valider_ia',        'source': 'TECH2_VALIDE',   'dest': 'IA_VALIDE'},
        {'trigger': 'terminer',          'source': 'IA_VALIDE',      'dest': 'TERMINE'},

        # Annulation possible depuis toute étape sauf TERMINE
        {'trigger': 'annuler', 'source': ['DEMANDE', 'TECH1_ASSIGNE', 'TECH2_VALIDE', 'IA_VALIDE'], 'dest': 'ANNULE'},
    ]

    def __init__(self, intervention_id: int, capteur_id: str = None):
        self.intervention_id = intervention_id
        self.capteur_id = capteur_id
        self.tech1_id = None
        self.tech2_id = None
        self.ia_confiance = None        # Score de confiance de l'IA (0-1)
        self.timestamps = {}            # Heure de chaque transition
        self.historique = []

        self.machine = Machine(
            model=self,
            states=self.STATES,
            transitions=self.TRANSITIONS,
            initial='DEMANDE',
            auto_transitions=False,
        )
        
        # Enregistrer les callbacks pour chaque état
        self.machine.add_states(
            [
                {'name': 'TECH1_ASSIGNE', 'on_enter': self._log_assignation},
                {'name': 'TECH2_VALIDE', 'on_enter': self._log_validation_tech2},
                {'name': 'IA_VALIDE', 'on_enter': self._log_validation_ia},
                {'name': 'TERMINE', 'on_enter': self._log_fin},
                {'name': 'ANNULE', 'on_enter': self._log_annulation},
            ]
        )

    # ── Callbacks ────────────────────────────────────────────────────

    def _log_assignation(self):
        self.timestamps['tech1_assigne'] = datetime.now().isoformat()
        print(f"👷 Intervention {self.intervention_id} : Tech1 assigné à {self.timestamps['tech1_assigne']}")

    def _log_validation_tech2(self):
        self.timestamps['tech2_valide'] = datetime.now().isoformat()
        print(f"✅ Intervention {self.intervention_id} : Validée par Tech2")

    def _log_validation_ia(self):
        self.timestamps['ia_valide'] = datetime.now().isoformat()
        print(f"🤖 Intervention {self.intervention_id} : Validée par l'IA (confiance: {self.ia_confiance})")

    def _log_fin(self):
        self.timestamps['termine'] = datetime.now().isoformat()
        print(f"🏁 Intervention {self.intervention_id} : TERMINÉE avec succès")

    def _log_annulation(self):
        self.timestamps['annule'] = datetime.now().isoformat()
        print(f"❌ Intervention {self.intervention_id} : ANNULÉE à l'étape '{self.state}'")

    # ── Méthodes métier ──────────────────────────────────────────────

    def assigner_premier_technicien(self, tech_id: int) -> dict:
        """Assigne le premier technicien et déclenche la transition"""
        self.tech1_id = tech_id
        return self.appliquer_evenement("assigner_tech1")

    def valider_par_second_technicien(self, tech_id: int) -> dict:
        """Le deuxième technicien valide l'intervention"""
        if tech_id == self.tech1_id:
            return {"succes": False, "erreur": "Le Tech2 doit être différent du Tech1"}
        self.tech2_id = tech_id
        return self.appliquer_evenement("valider_tech2")

    def valider_par_ia(self, score_confiance: float = 0.85) -> dict:
        """L'IA valide avec un score de confiance (simulé ou réel)"""
        self.ia_confiance = score_confiance
        if score_confiance < 0.5:
            return self.appliquer_evenement("annuler")
        return self.appliquer_evenement("valider_ia")

    def appliquer_evenement(self, evenement: str) -> dict:
        """Même pattern que CapteurFSM — utilisé par l'API"""
        ancien_etat = self.state
        try:
            getattr(self, evenement)()
            self.historique.append({'evenement': evenement, 'de': ancien_etat, 'vers': self.state})
            return {"succes": True, "ancien_etat": ancien_etat, "nouvel_etat": self.state, "erreur": None}
        except Exception:
            return {"succes": False, "ancien_etat": ancien_etat, "nouvel_etat": ancien_etat,
                    "erreur": f"Transition '{evenement}' non autorisée depuis '{ancien_etat}'"}

    def to_dict(self) -> dict:
        return {
            "intervention_id": self.intervention_id,
            "capteur_id": self.capteur_id,
            "etat": self.state,
            "tech1_id": self.tech1_id,
            "tech2_id": self.tech2_id,
            "ia_confiance": self.ia_confiance,
            "timestamps": self.timestamps,
            "transitions_disponibles": self.machine.get_triggers(self.state),
        }


TABLE_TRANSITION_INTERVENTION = """
╔═══════════════════╦════════════════════╦═══════════════════╗
║  État Actuel      ║  Événement         ║  État Suivant     ║
╠═══════════════════╬════════════════════╬═══════════════════╣
║  DEMANDE          ║  assigner_tech1    ║  TECH1_ASSIGNE    ║
║  TECH1_ASSIGNE    ║  valider_tech2     ║  TECH2_VALIDE     ║
║  TECH2_VALIDE     ║  valider_ia        ║  IA_VALIDE        ║
║  IA_VALIDE        ║  terminer          ║  TERMINE          ║
║  * (sauf TERMINE) ║  annuler           ║  ANNULE           ║
╚═══════════════════╩════════════════════╩═══════════════════╝
"""


if __name__ == "__main__":
    print("=== TEST AUTOMATE INTERVENTION ===\n")
    print(TABLE_TRANSITION_INTERVENTION)

    inter = InterventionFSM(intervention_id=1, capteur_id="C-042")

    print("--- Scénario complet de validation ---")
    print(inter.assigner_premier_technicien(tech_id=3))
    print(inter.valider_par_second_technicien(tech_id=7))
    print(inter.valider_par_ia(score_confiance=0.92))
    print(inter.appliquer_evenement("terminer"))

    print(f"\nÉtat final : {inter.state}")
    print(f"Détails : {inter.to_dict()}")