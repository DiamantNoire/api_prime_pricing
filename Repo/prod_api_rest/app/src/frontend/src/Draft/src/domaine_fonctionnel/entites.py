# app/src/domaine_fonctionnel/entites.py

# Importation de librairies
from typing import Dict, Optional, Any
from pydantic import BaseModel


# Modélisation des JDD ODRE:
class JddOdre(BaseModel):
    """
        Catalogue des métadonnées d'un JDD ODRE: 220 caractéristique pour une JDD ODRE " 220 colonnes"
        Ressources associées aux métadonnées: 46 caractéristiques pour un JDD ODRE "46 colonnes"
        Ressources provenant de la PDA opendata: 11 caractéristiques pour un JDD ODRE "11 colonnes"
    """
    id_jdd_odre: Optional[int] = None
    nom_jdd_odre: Optional[str] = ""
    metadonnees: Optional[Dict[str, Any]] = None
    ressources: Optional[Any] = None  # dict ou list
    PDA_opendata: Optional[Any] = None  # dict ou list


