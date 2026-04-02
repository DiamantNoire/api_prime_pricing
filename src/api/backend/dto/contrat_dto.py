"""DTOs sécurisés pour les opérations sur les contrats."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class ContratBaseDTO(BaseModel):
    """
    Structure contractuelle Pydantic utilisée pour l'insertion et la mise à jour d'un contrat.
    Tous les champs sont validés et documentés pour l'API.

    Args:
        id_client (str): Identifiant du client.
        id_vehicule (str): Identifiant du véhicule.
        id_contrat (str): Identifiant du contrat.
        bonus (float): Bonus-malus du contrat.
        type_contrat (str): Type de contrat souscrit.
        duree_contrat (int): Durée du contrat en mois.
        anciennete_info (int): Ancienneté de l'information sur le contrat.
        freq_paiement (str): Fréquence de paiement.
        paiement (str): Statut du paiement.
        utilisation (str): Type d'utilisation du véhicule.
        code_postal (str): Code postal du souscripteur.
        conducteur2 (str): Présence d'un second conducteur.
        age_conducteur1 (int): Âge du conducteur principal.
        age_conducteur2 (int): Âge du second conducteur.
        sex_conducteur1 (str): Sexe du conducteur principal.
        sex_conducteur2 (str): Sexe du second conducteur.
        anciennete_permis1 (int): Ancienneté du permis du conducteur principal.
        anciennete_permis2 (int): Ancienneté du permis du second conducteur.
        anciennete_vehicule (float): Ancienneté du véhicule.
        cylindre_vehicule (int): Cylindrée du véhicule.
        din_vehicule (int): DIN du véhicule.
        essence_vehicule (str): Type de carburant.
        marque_vehicule (str): Marque du véhicule.
        modele_vehicule (str): Modèle du véhicule.
        debut_vente_vehicule (int): Année de début de commercialisation.
        fin_vente_vehicule (int): Année de fin de commercialisation.
        vitesse_vehicule (int): Vitesse maximale du véhicule.
        type_vehicule (str): Type de véhicule.
        prix_vehicule (int): Prix du véhicule.
        poids_vehicule (int): Poids du véhicule.
        nombre_sinistres (int): Nombre de sinistres déclarés.
        montant_sinistre (float): Montant total des sinistres.
    """

    id_client: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    id_vehicule: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    id_contrat: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")

    bonus: float = Field(ge=0.0, le=2.0)
    type_contrat: Literal["Maxi", "Median1", "Median2", "Mini"]
    duree_contrat: int = Field(ge=1, le=120)
    anciennete_info: int = Field(ge=0, le=80)
    freq_paiement: Literal["Monthly", "Quarterly", "Biannual", "Yearly"]
    paiement: Literal["Yes", "No"]
    utilisation: Literal["WorkPrivate", "AllTrips", "Professional", "Retired"]
    code_postal: str = Field(pattern=r"^\d{5}$")
    conducteur2: Literal["Yes", "No"]

    age_conducteur1: int = Field(ge=18, le=100)
    age_conducteur2: int = Field(ge=0, le=100)
    sex_conducteur1: Literal["M", "F"]
    sex_conducteur2: Literal["M", "F", ""]
    anciennete_permis1: int = Field(ge=0, le=80)
    anciennete_permis2: int = Field(ge=0, le=80)
    anciennete_vehicule: float = Field(ge=0.0, le=80.0)

    cylindre_vehicule: int = Field(ge=500, le=10000)
    din_vehicule: int = Field(ge=20, le=1000)
    essence_vehicule: Literal["Gasoline", "Diesel", "Hybrid"]
    marque_vehicule: str = Field(min_length=1, max_length=80)
    modele_vehicule: str = Field(default="", max_length=80)
    debut_vente_vehicule: int = Field(ge=0, le=80)
    fin_vente_vehicule: int = Field(ge=0, le=80)
    vitesse_vehicule: int = Field(ge=80, le=400)
    type_vehicule: Literal["Tourism", "Commercial"]
    prix_vehicule: int = Field(ge=0, le=2_000_000)
    poids_vehicule: int = Field(ge=200, le=10_000)

    nombre_sinistres: int = Field(default=0, ge=0, le=50)
    montant_sinistre: float = Field(default=0.0, ge=0.0, le=10_000_000.0)

    @field_validator("anciennete_permis1")
    @classmethod
    def validate_permis1_vs_age(cls, value: int, info):
        age = info.data.get("age_conducteur1")
        if age is not None and value > age - 16:
            raise ValueError("anciennete_permis1 incohérente avec age_conducteur1")
        return value

    @field_validator("anciennete_permis2")
    @classmethod
    def validate_permis2_vs_age(cls, value: int, info):
        age2 = info.data.get("age_conducteur2")
        if age2 is not None and value > max(age2 - 16, 0):
            raise ValueError("anciennete_permis2 incohérente avec age_conducteur2")
        return value


class ContratCreateDTO(ContratBaseDTO):
    """
    DTO utilisé à la création d'un contrat (POST).
    
    Returns:
        dict: Un dictionnaire représentant le contrat créé.
    """


class ContratUpdateDTO(ContratBaseDTO):
    """
    DTO utilisé à la mise à jour complète d'un contrat (PUT).
    
    Returns:
        dict: Un dictionnaire représentant le contrat mis à jour.
    """


class ContratResponseDTO(ContratBaseDTO):
    """
    DTO de réponse API pour un contrat (GET).
    
    Args:
        index (Optional[int]): Index du contrat dans la base.
    Returns:
        dict: Un dictionnaire représentant le contrat retourné par l'API.
    """

    index: Optional[int] = None


class ContratReadDTO(BaseModel):
    """
    DTO de lecture tolérant pour les données historiques en base (lecture seule).
    
    Args:
        index (Optional[int]): Index du contrat dans la base.
        id_client (Optional[str]): Identifiant du client.
        id_vehicule (Optional[str]): Identifiant du véhicule.
        id_contrat (Optional[str]): Identifiant du contrat.
        bonus (Optional[float]): Bonus-malus du contrat.
        type_contrat (Optional[str]): Type de contrat souscrit.
        duree_contrat (Optional[int]): Durée du contrat en mois.
        anciennete_info (Optional[int]): Ancienneté de l'information sur le contrat.
        freq_paiement (Optional[str]): Fréquence de paiement.
        paiement (Optional[str]): Statut du paiement.
        utilisation (Optional[str]): Type d'utilisation du véhicule.
        code_postal (Optional[str]): Code postal du souscripteur.
        conducteur2 (Optional[str]): Présence d'un second conducteur.
        age_conducteur1 (Optional[int]): Âge du conducteur principal.
        age_conducteur2 (Optional[int]): Âge du second conducteur.
        sex_conducteur1 (Optional[str]): Sexe du conducteur principal.
        sex_conducteur2 (Optional[str]): Sexe du second conducteur.
        anciennete_permis1 (Optional[int]): Ancienneté du permis du conducteur principal.
        anciennete_permis2 (Optional[int]): Ancienneté du permis du second conducteur.
        anciennete_vehicule (Optional[float]): Ancienneté du véhicule.
        cylindre_vehicule (Optional[int]): Cylindrée du véhicule.
        din_vehicule (Optional[int]): DIN du véhicule.
        essence_vehicule (Optional[str]): Type de carburant.
        marque_vehicule (Optional[str]): Marque du véhicule.
        modele_vehicule (Optional[str]): Modèle du véhicule.
        debut_vente_vehicule (Optional[int]): Année de début de commercialisation.
        fin_vente_vehicule (Optional[int]): Année de fin de commercialisation.
        vitesse_vehicule (Optional[int]): Vitesse maximale du véhicule.
        type_vehicule (Optional[str]): Type de véhicule.
        prix_vehicule (Optional[int]): Prix du véhicule.
        poids_vehicule (Optional[int]): Poids du véhicule.
        nombre_sinistres (Optional[int]): Nombre de sinistres déclarés.
        montant_sinistre (Optional[float]): Montant total des sinistres.
    Returns:
        dict: Un dictionnaire représentant le contrat lu depuis la base.
    """

    index: Optional[int] = None
    id_client: Optional[str] = None
    id_vehicule: Optional[str] = None
    id_contrat: Optional[str] = None

    bonus: Optional[float] = None
    type_contrat: Optional[str] = None
    duree_contrat: Optional[int] = None
    anciennete_info: Optional[int] = None
    freq_paiement: Optional[str] = None
    paiement: Optional[str] = None
    utilisation: Optional[str] = None
    code_postal: Optional[str] = None
    conducteur2: Optional[str] = None

    age_conducteur1: Optional[int] = None
    age_conducteur2: Optional[int] = None
    sex_conducteur1: Optional[str] = None
    sex_conducteur2: Optional[str] = None
    anciennete_permis1: Optional[int] = None
    anciennete_permis2: Optional[int] = None
    anciennete_vehicule: Optional[float] = None

    cylindre_vehicule: Optional[int] = None
    din_vehicule: Optional[int] = None
    essence_vehicule: Optional[str] = None
    marque_vehicule: Optional[str] = None
    modele_vehicule: Optional[str] = None
    debut_vente_vehicule: Optional[int] = None
    fin_vente_vehicule: Optional[int] = None
    vitesse_vehicule: Optional[int] = None
    type_vehicule: Optional[str] = None
    prix_vehicule: Optional[int] = None
    poids_vehicule: Optional[int] = None

    nombre_sinistres: Optional[int] = None
    montant_sinistre: Optional[float] = None
