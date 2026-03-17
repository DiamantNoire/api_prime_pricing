# /scripts/rafraichir_cache_sources.py

# Importation des librairies
from __future__ import annotations
import time
from datetime import datetime

# Importation des modules
from src.config import Config
from src.infrastructure_technique.correspondances import(
    ConnecteurInspectionSources,
    ConnecteurSourcesExternes
)
from src.cas_d_usages_applicatifs.services import CasActuatlisationsDonnees

def rafraichir_sources_une_seule_fois() -> None:
    t0 = time.time()
    insp = ConnecteurInspectionSources()
    status, items = "ok", 0
    try:
        # Extraction des sources (forcée)
        connecter = ConnecteurSourcesExternes(
            use_cache=False,
            cache_ttl_minutes=None,
            force_read_parquet=True,
        )
        service = CasActuatlisationsDonnees(data=connecter,
                                            regles_frequences=Config.REGLES_FREQUENCES,
                                            seuils_alerte=Config.SEUILS_ALERTE
                )
        jdds = connecter.brancher_le_port()
        items = len(jdds or [])
    except Exception as e:
        status = f"[Module script| fonction rafraichir_sourcces_une_seule_fois a une erreur: {e}"
        raise
    finally:
        duree = time.time() - t0
        insp.enregistrer_rafraichissement(status=status,
                                          duration_sec=duree,
                                          items=items
            )
        
if __name__ == "__main__":
    if Config.AUTO_REFRESH_CRON_ENABLED:
        dow = datetime.now(Config.TIME_ZONE).weekday() # 0=lundi ... 6=dimanche
        # Lancement du script du luni au vendredi à partir de 09h pour la récupértion des sources
        if dow < 5:
            rafraichir_sources_une_seule_fois()