"""DTOs backend pour les endpoints FastAPI."""

from .contrat_dto import ContratCreateDTO, ContratReadDTO, ContratResponseDTO, ContratUpdateDTO

__all__ = [
    "ContratCreateDTO",
    "ContratReadDTO",
    "ContratResponseDTO",
    "ContratUpdateDTO",
]
