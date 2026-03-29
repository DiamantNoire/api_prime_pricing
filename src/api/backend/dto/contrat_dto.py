"""DTOs sécurisés pour les opérations sur les contrats."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class ContratBaseDTO(BaseModel):
    """Structure contractuelle utilisée pour l'insertion et la mise à jour."""

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
    """DTO utilisé à la création."""


class ContratUpdateDTO(ContratBaseDTO):
    """DTO utilisé à la mise à jour complète (PUT)."""


class ContratResponseDTO(ContratBaseDTO):
    """DTO de réponse API."""

    index: Optional[int] = None


class ContratReadDTO(BaseModel):
    """DTO de lecture tolérant pour les données historiques en base."""

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
