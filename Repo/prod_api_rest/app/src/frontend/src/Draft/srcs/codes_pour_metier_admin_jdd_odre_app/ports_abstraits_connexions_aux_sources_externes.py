# --- Application de supervision des jeux de données ODRE | chemin: srcs/codes_pour_metier_admin_jdd_odre_app/ports_abstsraits_connexions_aux_sources_externes.py

# === Importation des librairies ===
import json
import pandas as pd
import pyarrow.parquet as pq

from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any


# === Importation de modules ===
from srcs.codes_pour_metier_admin_jdd_odre_app.modelisation_jdd_odre import JddOdre

@dataclass
class PortAbstraitRecupererJdd0dre(ABC):
    """
    Docstring for PortAbstraitRecupererJdd0dre:
        Port abstrait de récupération des jdds ODRE
    Avantage:
        Sépartion nette entre les types de sources et l'application
        Il est possible de changer de port de connexion aux sources.
    
    """ 
    @abstractmethod
    def brancher_le_port(self) -> bool:
        """
        Docstring for brancher_le_port:
            Permet de brancher l'adapteur pour se connecter aux sources externes
        
        :param self: Description
        :return: Sauvegarde des sources externes dans l'applicaiton
        :rtype: bool (True pour unesauvegarde des sources dans l'application)
        """
        pass
    