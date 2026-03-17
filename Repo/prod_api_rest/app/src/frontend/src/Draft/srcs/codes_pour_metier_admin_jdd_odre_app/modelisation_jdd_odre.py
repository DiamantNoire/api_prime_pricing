# --- Application de supervision des jeux de données ODRE | chemin: srcs/codes_pour_metier_admin_jdd_odre_app/modelisation_jdd_odre.py

# === Importation des librairies ===
from typing import Dict, Optional, Any, List
from pydantic import BaseModel

# === Importatation des modules ===


# === Codes de modélisation ===
class JddOdre(BaseModel):
    """
        Catalogue des métadonnées d'un JDD ODRE: 220 caractéristique pour une JDD ODRE " 220 colonnes"
        Ressources associées aux métadonnées: 46 caractéristiques pour un JDD ODRE "46 colonnes"
        Ressources provenant de la PDA opendata: 11 caractéristiques pour un JDD ODRE "11 colonnes"

    """
    id_jdd_odre: Optional[int] = None
    nom_jdd_odre: Optional[str] = ""
    metadonnees: Optional[Dict[str, Any]] = None
    ressources: Optional[List[Dict[str, Any]]] = None
    pda_opendata: Optional[Dict[str, Any]] = None

