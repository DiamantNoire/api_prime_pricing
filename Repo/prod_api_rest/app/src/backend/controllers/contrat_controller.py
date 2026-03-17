from fastapi import APIRouter, HTTPException
from fastapi.responses import  HTMLResponse
from backend.repositories.contrat_repository import ContratRepository

contrat_router=APIRouter()
contrat_repo = ContratRepository()


@contrat_router.get("/contrats")
def get_all_contrats():
    return contrat_repo.find_all()
 

@contrat_router.get("/contrats/{id_contrat}")
def get_contrat(id_contrat: str):
    return contrat_repo.find_by_contrat(id_contrat)
 

@contrat_router.get("/contrats/type/{type_contrat}")
def get_contrat_by_type(type_contrat: str):
    return contrat_repo.find_by_type(type_contrat)
 

