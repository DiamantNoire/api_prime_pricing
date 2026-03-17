# srt/style/page_standard.py
# ==== coding: utf-8 ====

# Importation de librairies
from __future__ import annotations


import streamlit as st
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timedelta



# Importation d'autres modules de l'application
from src.config import Config


# Classe pour la page standard: css, barre latérale et bas de page
@dataclass
class Page_standard:
    def __init__(self, titre_page, utilisateur, chemin_css):
        self.titre_page = titre_page
        self.utilisateur = utilisateur
        self.chemin_css = chemin_css

    # Définition de la mise ne page 
    def _mise_en_page(self):
        st.set_page_config(self.titre_page, layout="wide", initial_sidebar_state="expanded")

    # Disposition pour la page 1
    # Disposition pour la page 2
    # Disposition pour la page 3
    # Disposition pour la page 4


    def _disposition_page_actualisations_des_donnees(self, ratios: tuple[int, int] = (2, 3)):
            """
            Crée la disposition (colonnes + séparateurs + conteneurs) pour la page 4.
            ratios: tuple pour le ratio des colonnes (gauche, droite), par défaut (2,3)
            
            Crée la disposition (colonnes + séparateurs + conteneurs) pour la page 4.
            Ne fait aucune opération métier (pas de service, pas de filtre).
            Retourne les conteneurs pour que la page injecte le contenu.
            """
            # Barre de haut de page: 2 colonnes (gauche: Indicateurs/Filtres, droite: Alertes)
            col_gauche, col_droite = st.columns(list(ratios))

            # Conteneur Détails sous les colonnes
            details_container = st.container()

            # Stockage dans la session pour que _ajouter_contenu() puisse y accéder si besoin
            st.session_state["layout_page_4"] = {
                "col_gauche": col_gauche,
                "col_droite": col_droite,
                "details_container": details_container,
            }

            # Retourne aussi pour usage direct
            return st.session_state["layout_page_4"]

    # Disposition pour la page 5
    
    # Chargement du style CSS 
    def _css(self):
        try:
            with open(self.chemin_css, encoding="utf-8") as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"CSS non chargé: {e}")

    # Méthodes de création d'une page standard (barre latérale, bas de page)
    def _barre_laterale(self):
        """
            Effet responsive à l'ouverture et la ferméture de la barre
        """
        st.markdown(
            """
            <script>
                function checkSidebar(){
                    const sidebar = document.querySelector('section[data-testid="stSidebar"]');
                   if (sidebar && sidebar.offsetWidth > 0){
                        document.body.classList.add('sidebar-open');
                    } else {
                        document.body.classList.remove('sidebar-open');
                    }
                }
                setInterval(checkSidebar, 500);
            </script>
            """,
            unsafe_allow_html=True
        )
        
    def _bas_de_page(self):
        """
            Rappel du nom de la page à l'utilisateur
            Rappel de la session de l'utilisateur
            Récupérer le nom de la page via son numéro 
            dans les variables d'environnement
        """    
        # Infos fraîcheur des données (parquet JDD)
        try:
            parquet_path = getattr(Config, "JDD_ODRE_PATH_PARQUET", "src/data/JDD_ODRE.parquet")
            p = Path(parquet_path)
            if p.exists():
                mtime = datetime.fromtimestamp(p.stat().st_mtime)
                now = datetime.now()
                delta = now - mtime
                def _fmt_delta(d: timedelta) -> str:
                    if d.days > 0:
                        hours = d.seconds // 3600
                        return f"{d.days} j {hours} h"
                    hours = d.seconds // 3600
                    minutes = (d.seconds % 3600) // 60
                    if hours > 0:
                        return f"{hours} h {minutes} min"
                    return f"{minutes} min"
                age_txt = _fmt_delta(delta)
                mtime_txt = mtime.strftime("%d/%m/%Y %H:%M")
                planning_txt = "Maj quotidienne prévue à 09:30 (Lun–Ven)"
                freshness_html = f"Données sources du <strong>{mtime_txt}</strong> • âge: <strong>{age_txt}</strong> • {planning_txt}"
            else:
                freshness_html = "Données sources: <strong>cache non initialisé</strong> • Maj quotidienne prévue à 09:30 (Lun–Ven)"
        except Exception:
            freshness_html = "Données sources: <strong>indisponibles</strong>"

        st.markdown(
            f"""
                <footer class="custom-footer">
                    <div class="footer-content">
                        <div class="footer-left"><strong>Outil de Supervision ODRE</strong></div>
                        <div class="footer-center">Page : 📊 <strong>{self.titre_page}</strong><br/><small>{freshness_html}</small></div>
                        <div class="footer-right">Connecté en tant que <strong>{self.utilisateur} | © {datetime.now().year}</strong></div>
                    </div>
                </footer>
            """,
            unsafe_allow_html=True
        )

      
