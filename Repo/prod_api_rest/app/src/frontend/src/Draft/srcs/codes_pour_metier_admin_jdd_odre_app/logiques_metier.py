
# --- Application de supervision des jeux de données ODRE
# chemin: srcs/codes_pour_admin_jdd_odre_app/logiques_metier.py
# ==== coding: utf-8 ====

# === Importation de librairies  ===#
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, date
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple, Mapping, Iterable

# === Importation d'entités métier ===
from srcs.configs import Configurations
from srcs.codes_pour_metier_admin_jdd_odre_app.modelisation_jdd_odre import JddOdre


# =============================================================================
# Regroupement par thématiques métier
#   - Thème 1 : Validation des jeux de données (A venir)
#   - Thème 2 : Connexion à l'application (A venir)
#   - Thème 3 : Surveillance des flux (A venir)
#   - Thème 4 : Qualité de la donnée (A venir)
#   - Thème 5 : Actualisation des données (implémenté)
#   - Thème 6 : Gestion des référentiels (A venir)
#   - Thème 7 : Développements (A venir)
# =============================================================================


# =============================================================================
# Thème 1 : Validation des jeux de données (A venir)
# =============================================================================

# Ici iront plus tard les règles métier de validation (schéma, complétude, cohérence…)
# Exemple de signatures futures :
# def valider_metadonnees(jdd: JddOdre) -> List[str]: ...
# def valider_ressources(jdd: JddOdre) -> List[str]: ...
# Pour le moment, on ne les implémente pas.
# -----------------------------------------------------------------------------


# =============================================================================
# Thème 2 : Connexion à l'application (A venir)
# =============================================================================

# Le domaine ne connaît pas la technique (auth, tokens, I/O). Rien à mettre ici.
# -----------------------------------------------------------------------------


# =============================================================================
# Thème 3 : Surveillance des flux (A venir)
# =============================================================================

# Les règles de détection d'anomalies de flux pourront venir ici, en pur métier.
# -----------------------------------------------------------------------------


# =============================================================================
# Thème 4 : Qualité de la donnée (A venir)
# =============================================================================

# Indicateurs de qualité (taux de nulls, contrôles métiers), en pur domaine.
# -----------------------------------------------------------------------------


# =============================================================================
# Thème 5 : Actualisation des données (implémenté)
# =============================================================================

class StatutActualisation(str, Enum):
    """Statut d'actualisation d'un JDD (vision métier)."""
    A_JOUR = "à jour"
    PAS_A_JOUR = "pas à jour"


@dataclass(frozen=True)
class FrequenceMiseAJour:
    """
    Objet-valeur : fréquence attendue d'actualisation d'un JDD.
    - periode : durée attendue entre deux mises à jour
    - tolerance_ratio : marge de tolérance relative (ex. 0.10 -> +10%)
    """
    periode: timedelta
    tolerance_ratio: float = 0.10

    def delai_acceptables(self) -> timedelta:
        """Durée limite acceptée (période + tolérance)."""
        return self.periode * (1.0 + max(0.0, self.tolerance_ratio))


@dataclass(frozen=True)
class RessourceImpact:
    """
    Projection métier minimale d'une ressource non à jour (pour expliciter l'impact).
    """
    uid_ressource: Optional[str]
    display_name: Optional[str]
    origin_type: Optional[str]
    updated_at: Optional[datetime]
    enabled: bool


@dataclass(frozen=True)
class AnalyseActualisationJdd:
    """
    Résultat d'analyse d'actualisation pour un JDD.
    """
    uid: Optional[str]
    dataset_id: Optional[str]
    statut: StatutActualisation
    ressources_count: int
    ressources_non_a_jour_count: int
    repartition_par_origin_type: Mapping[str, int]
    ressources_non_a_jour: Tuple[RessourceImpact, ...]
    date_anniversaire: Optional[date]
    age_jdd_jours: Optional[int]


# ---------- Helpers (purement métier, sans techno) ---------------------------

def _texte_vers_timedelta(valeur: Optional[str]) -> Optional[timedelta]:
    """
    Convertit une fréquence textuelle en timedelta.
    Supporte quelques valeurs FR/EN usuelles et des jours numériques.
      - 'quotidienne' / 'daily'     -> 1 jour
      - 'hebdomadaire' / 'weekly'   -> 7 jours
      - 'mensuelle' / 'monthly'     -> 30 jours (approx)
      - 'trimestrielle' / 'quarterly' -> 90 jours (approx)
      - 'annuelle' / 'yearly'       -> 365 jours (approx)
      - '7' -> 7 jours (interprétation simple)
    Si non reconnue : None (au cas d'usage d'appliquer un fallback).
    """
    if not valeur:
        return None
    s = str(valeur).strip().lower()
    mapping = {
        "quotidienne": 1, "daily": 1,
        "hebdomadaire": 7, "weekly": 7,
        "mensuelle": 30, "monthly": 30,
        "trimestrielle": 90, "quarterly": 90,
        "annuelle": 365, "yearly": 365,
    }
    if s in mapping:
        return timedelta(days=mapping[s])
    # Valeur numérique -> jours
    try:
        return timedelta(days=int(s))
    except Exception:
        return None


def _extraire_frequence_attendue(metadonnees: Optional[Dict[str, Any]],
                                 frequence_par_defaut: Optional[timedelta],
                                 tolerance_ratio: float) -> Optional[FrequenceMiseAJour]:
    """
    Détermine la fréquence attendue d'un JDD à partir des métadonnées connues.
    Priorité décroissante :
      1) metadata_dcat_accrualperiodicity_value
      2) metadata_custom_pas_temporel_value
    Sinon : frequence_par_defaut si fournie.
    """
    if not metadonnees:
        return FrequenceMiseAJour(frequence_par_defaut, tolerance_ratio) if frequence_par_defaut else None

    cles = [
        "metadata_dcat_accrualperiodicity_value",
        "metadata_custom_pas_temporel_value"
    ]
    for k in cles:
        if k in metadonnees and metadonnees.get(k):
            td = _texte_vers_timedelta(metadonnees.get(k))
            if td:
                return FrequenceMiseAJour(periode=td, tolerance_ratio=tolerance_ratio)

    return FrequenceMiseAJour(frequence_par_defaut, tolerance_ratio) if frequence_par_defaut else None


def _extraire_identifiants(metadonnees: Optional[Dict[str, Any]]) -> Tuple[Optional[str], Optional[str]]:
    """Extrait (uid, dataset_id) des métadonnées si présents."""
    if not metadonnees:
        return None, None
    uid = metadonnees.get("uid")
    dataset_id = metadonnees.get("dataset_id")
    return (str(uid) if uid is not None else None,
            str(dataset_id) if dataset_id is not None else None)


def _extraire_date_creation(metadonnees: Optional[Dict[str, Any]]) -> Optional[datetime]:
    """
    Extrait la date de création depuis les métadonnées (champ 'created_at').
    Précondition (côté application) : si issue d'un texte, elle a déjà été convertie en datetime.
    """
    if not metadonnees:
        return None
    created_at = metadonnees.get("created_at")
    return created_at if isinstance(created_at, datetime) else None


def _ressource_est_active(ressource: Dict[str, Any]) -> bool:
    """
    Détermine si la ressource est active du point de vue métier.
    On considère désactivée si enabled ∈ {False, 'false', '0'}.
    """
    enabled = ressource.get("enabled", True)
    if isinstance(enabled, bool):
        return enabled
    s = str(enabled).strip().lower()
    return s not in {"false", "0"}


def _ressource_est_a_jour(ressource: Dict[str, Any],
                          maintenant: datetime,
                          frequence: Optional[FrequenceMiseAJour],
                          periode_defaut: Optional[timedelta]) -> bool:
    """
    Règle métier d'actualisation d'une ressource :
      - Ressource désactivée => considérée 'à jour' (ne bloque pas le JDD).
      - Si updated_at absent ou non-datetime => 'pas à jour'.
      - Sinon, (maintenant - updated_at) <= delai_acceptables.
        delai_acceptables = frequence ou periode_defaut (la tolérance peut être intégrée à la source).
      - Si aucune règle : considérer 'à jour' par défaut (politique métier).
    """
    if not _ressource_est_active(ressource):
        return True

    updated_at = ressource.get("updated_at")
    if not isinstance(updated_at, datetime):
        return False

    delai = None
    if frequence is not None:
        delai = frequence.delai_acceptables()
    elif periode_defaut is not None:
        delai = periode_defaut

    if delai is None:
        return True

    return (maintenant - updated_at) <= delai


def _compter_par_origin_type(ressources: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    """Comptage des ressources par type d'origine ('origin_type')."""
    rep: Dict[str, int] = {}
    for r in ressources:
        cle = str(r.get("origin_type") or "").strip().lower()
        rep[cle] = rep.get(cle, 0) + 1
    return rep


# ---------- Service de domaine : analyse d'actualisation ----------------------

class ServiceActualisationDomaine:
    """
    Service de domaine pur :
      - ne dépend d'aucune techno (pas de pandas, pas de JSON, pas de config globale)
      - reçoit un JddOdre (entité métier), une horloge (now) et des paramètres de politique
      - retourne un résultat métier 'AnalyseActualisationJdd'
    """

    def analyser_un_jdd(self,
                        jdd: JddOdre,
                        maintenant: datetime,
                        frequence_par_defaut: Optional[timedelta] = None,
                        tolerance_ratio: float = 0.10) -> AnalyseActualisationJdd:
        """
        Analyse l'actualisation d'un JDD unique.
        Préconditions (assurées par la couche application) :
          - jdd.metadonnees : dict avec 'uid', 'dataset_id', 'created_at' (datetime) si pertinents
          - jdd.ressources : liste/tuple de dicts Python avec au moins :
                'uid_ressource', 'display_name', 'origin_type',
                'updated_at' (datetime), 'enabled' (bool/str)
        """
        metadonnees = jdd.metadonnees or {}
        ressources = tuple(jdd.ressources) if isinstance(jdd.ressources, (list, tuple)) else tuple()

        uid, dataset_id = _extraire_identifiants(metadonnees)
        date_creation = _extraire_date_creation(metadonnees)
        frequence = _extraire_frequence_attendue(metadonnees, frequence_par_defaut, tolerance_ratio)

        repartition = _compter_par_origin_type(ressources)

        non_a_jour: List[RessourceImpact] = []
        for r in ressources:
            est_frais = _ressource_est_a_jour(r, maintenant, frequence, frequence_par_defaut)
            if not est_frais:
                non_a_jour.append(RessourceImpact(
                    uid_ressource=r.get("uid_ressource"),
                    display_name=r.get("display_name"),
                    origin_type=r.get("origin_type"),
                    updated_at=r.get("updated_at") if isinstance(r.get("updated_at"), datetime) else None,
                    enabled=_ressource_est_active(r)
                ))

        statut = StatutActualisation.A_JOUR if len(non_a_jour) == 0 else StatutActualisation.PAS_A_JOUR
        age_jours = (maintenant.date() - date_creation.date()).days if date_creation else None
        date_anniv = date_creation.date() if date_creation else None

        return AnalyseActualisationJdd(
            uid=uid,
            dataset_id=dataset_id,
            statut=statut,
            ressources_count=len(ressources),
            ressources_non_a_jour_count=len(non_a_jour),
            repartition_par_origin_type=repartition,
            ressources_non_a_jour=tuple(non_a_jour),
            date_anniversaire=date_anniv,
            age_jdd_jours=age_jours,
        )

    def analyser_liste_jdd(self,
                           jdds: Iterable[JddOdre],
                           maintenant: datetime,
                           frequence_par_defaut: Optional[timedelta] = None,
                           tolerance_ratio: float = 0.10) -> List[AnalyseActualisationJdd]:
        """
        Analyse l'actualisation d'une liste de JDD.
        """
        return [
            self.analyser_un_jdd(
                jdd=j,
                maintenant=maintenant,
                frequence_par_defaut=frequence_par_defaut,
                tolerance_ratio=tolerance_ratio
            )
            for j in jdds
        ]


# ---------- Indicateurs globaux (métier) -------------------------------------

@dataclass(frozen=True)
class IndicateursGlobauxActualisation:
    nb_jdd: int
    nb_a_jour: int
    nb_pas_a_jour: int
    nb_ressources_total: int
    nb_ressources_non_a_jour: int
    repartition_origin_type: Mapping[str, int]


def calculer_indicateurs_globaux(analyses: Iterable[AnalyseActualisationJdd]) -> IndicateursGlobauxActualisation:
    """
    Agrège des analyses pour produire des indicateurs globaux d'actualisation.
    """
    analyses_list = list(analyses)
    nb_jdd = len(analyses_list)
    nb_a_jour = sum(1 for a in analyses_list if a.statut == StatutActualisation.A_JOUR)
    nb_pas_a_jour = nb_jdd - nb_a_jour

    nb_ress_total = sum(a.ressources_count for a in analyses_list)
    nb_ress_non_frais = sum(a.ressources_non_a_jour_count for a in analyses_list)

    rep: Dict[str, int] = {}
    for a in analyses_list:
        for k, v in a.repartition_par_origin_type.items():
            rep[k] = rep.get(k, 0) + int(v)

    return IndicateursGlobauxActualisation(
        nb_jdd=nb_jdd,
        nb_a_jour=nb_a_jour,
        nb_pas_a_jour=nb_pas_a_jour,
        nb_ressources_total=nb_ress_total,
        nb_ressources_non_a_jour=nb_ress_non_frais,
        repartition_origin_type=rep
    )


# =============================================================================
# Thème 6 : Gestion des référentiels (A venir)
# =============================================================================

# Ex. futures règles de cohérence des référentiels.
# -----------------------------------------------------------------------------


# =============================================================================
# Thème 7 : Développements / Idées (A venir)
# =============================================================================

# Espace pour prototyper de nouvelles règles métier.
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class EtatActualisationJdd:
    """
    État d'actualisation d'un JDD (version compacte et directe).
    """
    uid: Optional[str]
    statut: str  # "à jour" | "pas à jour"
    derniere_mise_a_jour: Optional[datetime]
    delta_depuis_derniere_maj: Optional[timedelta]
    delta_depuis_creation: Optional[timedelta]
    prochaine_mise_a_jour: Optional[datetime]
    ressources_total: int
    ressources_non_a_jour: int
    ressources_non_a_jour_noms: Tuple[str, ...]  # utile pour l'UI (affichage/exports)

    @classmethod
    def calculer(
        cls,
        uid: Optional[str],
        date_creation: Optional[datetime],
        ressources: List[Dict[str, Any]],
        maintenant: datetime,
        periode: timedelta,
        tolerance: float,
    ) -> "EtatActualisationJdd":
        """
        Calcule un état d'actualisation à partir de ressources 'disponibles'.
        Règles :
          - Ressource ignorée si 'enabled' est faux ('false', '0', 'no', 'non').
          - Si 'updated_at' est absent ou non datetime -> ressource non à jour.
          - Délai acceptable = période * (1 + tolérance).
          - Statut du JDD : basé sur la dernière MAJ globale parmi les ressources actives datées.
        """
        # --- helpers locaux minimalistes ---
        def _est_active(r: Dict[str, Any]) -> bool:
            v = r.get("enabled", True)
            if isinstance(v, bool):
                return v
            s = str(v).strip().lower()
            return s not in {"false", "0", "no", "non"}

        def _nom_ressource(r: Dict[str, Any]) -> str:
            return str(r.get("display_name") or r.get("uid") or "").strip()

        # --- filtrage ressources actives ---
        ressources_actives = [r for r in ressources if _est_active(r)]

        # --- calcul dernière mise à jour globale (parmi celles avec datetime) ---
        mises_a_jour = [r["updated_at"] for r in ressources_actives if isinstance(r.get("updated_at"), datetime)]
        derniere_maj: Optional[datetime] = max(mises_a_jour) if mises_a_jour else None

        delai_acceptable = periode * (1.0 + max(0.0, tolerance))
        delta_depuis_derniere_maj: Optional[timedelta] = (maintenant - derniere_maj) if derniere_maj else None
        est_a_jour = (delta_depuis_derniere_maj is not None) and (delta_depuis_derniere_maj <= delai_acceptable)

        prochaine_maj: Optional[datetime] = (derniere_maj + periode) if derniere_maj else None

        # --- ressources non à jour : sans date OU dépassant le délai ---
        ressources_non_ok_noms: List[str] = []
        for r in ressources_actives:
            upd = r.get("updated_at")
            if not isinstance(upd, datetime):
                # pas de date => non à jour
                nom = _nom_ressource(r)
                if nom:
                    ressources_non_ok_noms.append(nom)
                continue
            # date existante : comparer au délai acceptable
            if (maintenant - upd) > delai_acceptable:
                nom = _nom_ressource(r)
                if nom:
                    ressources_non_ok_noms.append(nom)

        return cls(
            uid=uid,
            statut="à jour" if est_a_jour else "pas à jour",
            derniere_mise_a_jour=derniere_maj,
            delta_depuis_derniere_maj=delta_depuis_derniere_maj,
            delta_depuis_creation=(maintenant - date_creation) if isinstance(date_creation, datetime) else None,
            prochaine_mise_a_jour=prochaine_maj,
            ressources_total=len(ressources),  # total "vu", pas seulement les actives
            ressources_non_a_jour=len(ressources_non_ok_noms),
            ressources_non_a_jour_noms=tuple(ressources_non_ok_noms),
        )
