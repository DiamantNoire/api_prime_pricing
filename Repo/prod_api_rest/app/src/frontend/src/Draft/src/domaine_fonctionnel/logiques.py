# app/src/domaine_fonctionnel/logiques.py

# Importation de librairies
from __future__ import annotations

import json
from typing import Dict, List, Any, Set, Optional, Tuple, Iterable
from datetime import datetime, timedelta, timezone


# Importation de modules
from src.config import Config
from src.domaine_fonctionnel.entites import JddOdre



# --- Par sections thématiques métiers -----#

# --- Fonctions utiles ---#

def temps_actuel_uct() -> datetime:
    """Retourne l'heure actuelle en UTC."""
    return datetime.now(timezone.utc)

def valeur_en_temps(valeur: Optional[str]) -> Optional[datetime]:
    """
    Convertit une chaîne ISO 8601 en datetime UTC.
    Accepte les suffixes 'Z' et les offsets (+/-HH:MM). Retourne None si invalide.
    """
    if not valeur:
        return None
    try:
        v = valeur.strip()
        # Support des formats se terminant par 'Z'
        if v.endswith("Z"):
            # Remplacer Z par +00:00 pour fromisoformat
            v = v[:-1] + "+00:00"
        dt = datetime.fromisoformat(v)
        # Forcer en UTC si timezone absente
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


#======: VALIDATION DES JDDS
def valider_presence_champs_obligatoires(jdd: JddOdre) -> Tuple[bool, List[str], List[str]]:
    """
        Description: Vérifier que les métadonnées essentielles sont présentes et non vides
        :param jdd: JddOdre
        : retour 
            est_valide: bool
            champs_maquants: List[str]
            commentaires: List[str]
    """
    manquants: List[str] = []
    commentaires: List[str] = []
    meta = jdd.metadonnees or {}
    # Champs obligatoires de métadonnées
    for champ in getattr(Config, "CHAMPS_OBLIGATOIRE_META", []):
        val = meta.get(champ)
        if val is None or (isinstance(val, str) and val.strip() == ""):
            manquants.append(champ)
    est_valide = len(manquants) == 0
    if not est_valide:
        commentaires.append("Métadonnées incomplètes")
    return est_valide, manquants, commentaires

def valider_coherence_metadonnees(jdd: JddOdre) -> Tuple[List[Dict], str]:
    """
        Description: Détecter les incohérences sémantiques (licence, fréquence, thématiques…).
        :param jdd: JddOdre
        : retour 
            anomalies: List[Dict] ex: (typ, champ concerné, message)
            niveau_global: srt ex: (OK, A_SERVEILLER, KO)

    """
    anomalies: List[Dict] = []
    meta = jdd.metadonnees or {}
    # Fréquence déclarée connue ?
    freq = meta.get("metadata_custom_pas_temporel_value")
    if freq not in Config.TYPE_FREQUENCE:
        anomalies.append({
            "type": "attention",
            "champ": "metadata_custom_pas_temporel_value",
            "message": "Fréquence inconnue ou non déclarée"
        })
    # Licence présente ? (si champ connu dans la source)
    if meta.get("metadata_default_license_value") in (None, "") and meta.get("metadata_internal_license_id_value") in (None, ""):
        anomalies.append({
            "type": "attention",
            "champ": "license",
            "message": "Licence non renseignée"
        })
    # Détermination du niveau global
    niveau_global = "OK"
    if any(a.get("type") == "critique" for a in anomalies):
        niveau_global = "KO"
    elif any(a.get("type") == "attention" for a in anomalies):
        niveau_global = "A_SURVEILLER"
    return anomalies, niveau_global

def valider_existence_ressources_exploitables(jdd: JddOdre) -> Tuple[List[Dict], bool, List[str]]:
    """
        Description: S'assurer qu'un certains nombres de ressources sont exploitables
        :param jdd: JddOdre
        : retour 
            ressources_exploitables: List[Dict]
            est_exploitable: bool
            motif_non_exploitable: List[str]

    """
    ressources_exploitables: List[Dict] = []
    motifs_non_exploitable: List[str] = []
    # Les ressources peuvent être soit dans jdd.ressources (dict) soit en JSON dans metadonnees['ressources_json']
    ressources_raw = jdd.ressources
    if not ressources_raw:
        # Essai via ressources_json (string ou dict/list)
        meta = jdd.metadonnees or {}
        rj = meta.get("ressources_json")
        if isinstance(rj, str):
            try:
                ressources_raw = json.loads(rj)
            except Exception:
                ressources_raw = None
        else:
            ressources_raw = rj
    # Normaliser en liste de dicts
    ressources_list: List[Dict] = []
    if isinstance(ressources_raw, list):
        ressources_list = [r for r in ressources_raw if isinstance(r, dict)]
    elif isinstance(ressources_raw, dict):
        # une seule ressource
        ressources_list = [ressources_raw]
    else:
        motifs_non_exploitable.append("Aucune ressource détectée")
    # Critères d'exploitabilité: enabled=True et présence d'une URL ou d'un identifiant datasource
    for r in ressources_list:
        enabled = str(r.get("enabled", "")).lower() in ("true", "1", "yes")
        has_url = bool(r.get("url") or r.get("datasource_relative_url"))
        if enabled and has_url:
            ressources_exploitables.append(r)
    est_exploitable = len(ressources_exploitables) > 0
    if not est_exploitable and not motifs_non_exploitable:
        motifs_non_exploitable.append("Aucune ressource exploitable (enabled+url)")
    return ressources_exploitables, est_exploitable, motifs_non_exploitable
    
def valider_existence_pda_exploitablesjdd(jdd: JddOdre) -> Tuple[List[Dict], bool, List[str]]:
    """
        Description: S'assurer qu'un certains nombres de ressources sont exploitables
        :param jdd: JddOdre
        : retour 
            pda_exploitables: List[Dict]
            est_exploitable: bool
            motif_non_exploitable: List[str]

    """
    pda_exploitables: List[Dict] = []
    motifs: List[str] = []
    pda = jdd.PDA_opendata
    if isinstance(pda, list):
        candidats = [x for x in pda if isinstance(x, dict)]
    elif isinstance(pda, dict):
        candidats = [pda]
    else:
        candidats = []
    for b in candidats:
        # Critères: non supprimé et fullname présent
        supprime = str(b.get("boolisdeleted", "")).lower() in ("true", "1", "yes")
        if not supprime and b.get("fullname"):
            pda_exploitables.append(b)
    est_exploitable = len(pda_exploitables) > 0
    if not est_exploitable:
        motifs.append("Aucun blob exploitable (non supprimé + fullname)")
    return pda_exploitables, est_exploitable, motifs



#======: ACTUALISATION DES JDDS

def _applatir_cles(obj: Any, prefix: str = "") -> List[str]:
    keys: Set[str] = set()

    def _rec(x: Any, p: str):
        if isinstance(x, dict):
            if p:
                keys.add(p)
            for k, v in x.items():
                np = f"{p}.{k}" if p else str(k)
                keys.add(np)
                _rec(v, np)
        elif isinstance(x, list):
            if p:
                keys.add(p)
            for i, v in enumerate(x):
                np = f"{p}[{i}]" if p else f"[{i}]"
                keys.add(np)
                _rec(v, np)
        else:
            # scalaire -> rien à ajouter
            pass

    _rec(obj, prefix)
    # ordre stable: trie par longueur puis lexicographique (ou retire le tri si tu veux l'ordre découverte)
    return sorted(keys)



def mise_a_dispo_cols_utiles_du_jdds(jdds: Iterable["JddOdre"]) -> List[str]:
    """Union ordonnée: clés méta + clés aplaties des ressources et de la PDA."""
    seen = set()
    out: List[str] = []

    for jdd in jdds or []:
        # Méta à plat
        for k in (jdd.metadonnees or {}).keys():
            if k not in seen:
                seen.add(k)
                out.append(k)

        # Ressources JSON
        if jdd.ressources is not None:
            for k in _applatir_cles(jdd.ressources, prefix="ressources"):
                if k not in seen:
                    seen.add(k)
                    out.append(k)

        # PDA/Blobs JSON
        if jdd.PDA_opendata is not None:
            for k in _applatir_cles(jdd.PDA_opendata, prefix="PDA"):
                if k not in seen:
                    seen.add(k)
                    out.append(k)

    return out


def calculer_age_jdd(jdd: JddOdre) -> Tuple[str, str]:
    """
        Description: Détermine l'âge d'un jdd 
        entée: Jdd
        sorties: 
            age: str à convertir par la couche cas d'usage
            commentaire: str

    """
    meta = jdd.metadonnees or {}
    # Choix de la date la plus pertinente: updated_at puis created_at
    dt_last = valeur_en_temps(meta.get("updated_at")) or valeur_en_temps(meta.get("metadata_default_modified_value"))
    if dt_last is None:
        dt_last = valeur_en_temps(meta.get("created_at"))
    if dt_last is None:
        return "", "absence de date exploitable"
    delta = temps_actuel_uct() - dt_last
    # Retourner l'âge en secondes sous forme de chaîne
    age_seconds = int(delta.total_seconds())
    return str(age_seconds), "age_en_secondes"


def mise_a_dispo_cols_utiles_du_jdds(jdds: Iterable["JddOdre"]) -> List[str]:
    seen = set()
    out: List[str] = []

    for jdd in jdds or []:
        # 1) Clés des métadonnées à plat
        meta = jdd.metadonnees or {}
        for k in meta.keys():
            if k not in seen:
                seen.add(k)
                out.append(k)

        # 2) Clés dynamiques des ressources
        if jdd.ressources is not None:
            for k in _applatir_cles(jdd.ressources, prefix="ressources"):
                if k not in seen:
                    seen.add(k)
                    out.append(k)

        # 3) Clés dynamiques de la PDA
        if jdd.PDA_opendata is not None:
            for k in _applatir_cles(jdd.PDA_opendata, prefix="PDA"):
                if k not in seen:
                    seen.add(k)
                    out.append(k)

    return out


def evaluer_confirmite_frequence(jdd: JddOdre, 
                                regle_frequence: Dict
    ) -> Tuple[str, int, str]:
    """
        Description: Evalue si la mise à jour respecte la fréquence déclarée
        Entrées: 
            jdd: JddOdre
            regle_frequence: Dict (mapping fréquence -> seuils point à définir avec le métier dans Config)
        Sorties:
            statut: str ex (A_JOUR, EN_RETARD, CRITIQUEs, INDETERMINE)
            ecart: int
            frequance_normee: str
    """
    meta = jdd.metadonnees or {}
    freq_label = meta.get("metadata_custom_pas_temporel_value")

    # 1) Récupération de la durée (timedelta)
    freq_td: Optional[timedelta] = regle_frequence.get(freq_label)
    if freq_label not in regle_frequence or freq_td is None:
        return "INDETERMINE", 0, str(freq_label or "")

    # 2) Seuils pour ce label
    thresholds = Config.REGLES_FREQUENCES.get(freq_label, {"attention": 1.0, "critique": 2.0})

    # 3) Dernière date connue
    last_dt = valeur_en_temps(meta.get("updated_at")) 
              #or valeur_en_temps(meta.get("metadata_default_modified_value")) \
              #or valeur_en_temps(meta.get("created_at"))
    if last_dt is None:
        return "CRITIQUE", 0, freq_label

    # 4) Calculs
    delta = temps_actuel_uct() - last_dt
    ecart_minutes = int(max(0, (delta - freq_td).total_seconds()) // 60)

    statut = "A_JOUR"
    if delta > freq_td * thresholds.get("critique", 2.0):
        statut = "CRITIQUE"
    elif delta > freq_td * thresholds.get("attention", 1.0):
        statut = "EN_RETARD"
    return statut, ecart_minutes, freq_label

def projeter_prochaine_mise_a_jour(jdd: JddOdre, regle_frequence: Dict) -> Tuple[str, str, str]:
    """
        Description: Evalue si la mise à jour respecte la fréquence déclarée
        Entrées: 
            jdd: JddOdre
            regle_frequence: Dict (mapping fréquence -> seuils point à définir avec le métier dans Config)
        Sorties:
            prochaine_echeance: str ex (qui sera à convertir en datime)
            mode_calcul: str ex (DECLARATIF, ESTIMATION)
            confiance: str ex (FAIBLE, MOYENNE, ELEVEE)
    """
    meta = jdd.metadonnees or {}
    freq_label = meta.get("metadata_custom_pas_temporel_value")
    freq_td = regle_frequence.get(freq_label)
    last_dt = valeur_en_temps(meta.get("updated_at")) or valeur_en_temps(meta.get("metadata_default_modified_value")) or valeur_en_temps(meta.get("created_at"))
    if freq_td is None or last_dt is None:
        return "", "ESTIMATION" if freq_td else "INDETERMINE", "FAIBLE"
    next_due = last_dt + freq_td
    mode = "DECLARATIF"
    confiance = "ELEVEE"
    return next_due.isoformat(), mode, confiance

def detecter_anomalie_actualisation_sur_1_jjd(jdd: JddOdre, seuil_alerte: Dict, regle_frequence: Dict) -> Tuple[List[Dict], bool]:
    """
        Description: Identifier les anomalies liées à l'actualisation (absence de date, retard, fréquence incohérente)
        Entrées: 
            jdd : JddOdre
            seuils_alerte: Dict ex attention/critique
        Sorties:
            anomalies: List[Dict] ex type, criticité, message, éléments concernés
            has_anomalie: bool
        
    """
    anomalies: List[Dict] = []
    meta = jdd.metadonnees or {}
    # Règles unitaires
    rules_jdd = (seuil_alerte or {}).get("jdd", {})
    last_dt = valeur_en_temps(meta.get("updated_at")) or valeur_en_temps(meta.get("metadata_default_modified_value")) or valeur_en_temps(meta.get("created_at"))
    if last_dt is None and rules_jdd.get("absent_last_update_is_critique", True):
        anomalies.append({
            "type": "critique",
            "message": "Date de mise à jour absente",
            "champ": "updated_at|metadata_default_modified_value|created_at"
        })
    freq_label = meta.get("metadata_custom_pas_temporel_value")
    if freq_label not in Config.TYPE_FREQUENCE and rules_jdd.get("freq_inconnue_is_attention", True):
        anomalies.append({
            "type": "attention",
            "message": "Fréquence inconnue",
            "champ": "metadata_custom_pas_temporel_value"
        })
    # Statut calculé par évaluation de conformité
    statut, ecart, _ = evaluer_confirmite_frequence(jdd, regle_frequence)
    if statut in ("EN_RETARD", "CRITIQUE"):
        anomalies.append({
            "type": "attention" if statut == "EN_RETARD" else "critique",
            "message": f"JDD {statut}",
            "ecart_minutes": ecart
        })
    return anomalies, len(anomalies) > 0
    
def generer_indicatuer_actualisation(list_jdds: List[JddOdre], seuils_alerte: Dict, regles_frequecnce: Dict,) -> Tuple[Dict, List[Dict], str]:
    """
        Description: Produire des indicateurs agrégés pour les surpervision (sur un ensemble de JDD)
        Entrée: 
            list_jdds: List[JddOdre]
            regles_frequence: Dict
            seuils_alerte: Dict

        Sorties: Tuple
            Indicateurs: Dict
                pourcentage_a_jour
                pourcentage_en_retard
                pourcentage_critiques
            top_jjds_en_retard: List[Dict]
            statut_global: str ex (OK, A_SURVEILLER, KO)
    
    """
    total = len(list_jdds) if list_jdds else 0
    if total == 0:
        return {"pourcentage_a_jour": 0, "pourcentage_en_retard": 0, "pourcentage_critiques": 0}, [], "INDETERMINE"

    n_ok = n_retard = n_critique = 0
    top: List[Dict] = []

    for j in list_jdds:
        try:
            statut, ecart, freq = evaluer_confirmite_frequence(j, regles_frequecnce)
        except Exception:
            # on ignore ce JDD pour ne pas faire tomber tout le calcul
            continue

        if statut == "A_JOUR":
            n_ok += 1
        elif statut == "EN_RETARD":
            n_retard += 1
        elif statut == "CRITIQUE":
            n_critique += 1

        if statut in ("EN_RETARD", "CRITIQUE"):
            top.append({
                "jdd": j.nom_jdd_odre or j.id_jdd_odre,
                "producteur": (j.metadonnees or {}).get("metadata_default_publisher_value", ""),
                "statut": statut,
                "ecart_minutes": ecart,
                "frequence": freq
            })

    # Tri top
    top_jdds_en_retard = sorted(
        [t for t in top if t["statut"] in ("EN_RETARD", "CRITIQUE")],
        key=lambda x: x["ecart_minutes"] or 0,
        reverse=True
    )[:10]

    # Pourcentages
    pct = lambda n: int(round(100 * n / total)) if total else 0
    indicateurs = {
        "pourcentage_a_jour": pct(n_ok),
        "pourcentage_en_retard": pct(n_retard),
        "pourcentage_critiques": pct(n_critique),
    }

    # Statut global
    global_rules = (seuils_alerte or {}).get("global", {})
    if indicateurs["pourcentage_critiques"] >= int(global_rules.get("ko_min_critiques_pct", 20)):
        statut_global = "KO"
    elif indicateurs["pourcentage_en_retard"] <= int(global_rules.get("ok_max_en_retard_pct", 10)):
        statut_global = "OK"
    else:
        statut_global = "A_SURVEILLER"

    return indicateurs, top_jdds_en_retard, statut_global
