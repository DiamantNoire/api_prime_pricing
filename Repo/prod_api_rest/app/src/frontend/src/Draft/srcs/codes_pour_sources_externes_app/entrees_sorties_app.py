
# === Importation librairies ===
import json
import pandas as pd
import pyarrow.parquet as pq
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any

# === Importation de modules ===
from srcs.configs import Configurations
from srcs.codes_pour_metier_admin_jdd_odre_app.modelisation_jdd_odre import(
    JddOdre
)
from srcs.codes_pour_metier_admin_jdd_odre_app.ports_abstraits_connexions_aux_sources_externes import(
    PortAbstraitRecupererJdd0dre
)
from srcs.codes_pour_sources_externes_app.outils_pour_sources_externes import(
    alimenter_app_en_data,
    alimenter_app_en_data_test
)

# === Code d'implémentation concrèrete des ports de connexion aux sources externes à l'application ===
@dataclass
class AdaptateurSourcesExternes(PortAbstraitRecupererJdd0dre):
    """
        Docstring for AdaptateurSourcesExternes:
            Implémentation concrète du port PortAbstraitRecupererJdd0dre.
        Avantage:
            Séparation claire entre le code technique et les besoins fonctionnels de l'application

    """
    
    
    def brancher_le_port(self) -> bool:
        """
        Docstring for brancher_le_port:
            récupère les trois types de sources
            catalogue des métadata pour les jeux de données odre
            sources assoicées aux catalogue
            sources pointant vers le blob opendata (pda)

        :rtype: bool (Avec une sauvegarde dans l'application : True)
        """
        les_connecteurs = Configurations.CONNECTEURS
        try:
            _, _, _ = alimenter_app_en_data_test(connecteurs=les_connecteurs)
            return True
        except Exception as e: 
            return False

    