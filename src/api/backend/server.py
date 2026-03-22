# --*- coding: utf-8 -*-
# =============================================
#------ IMPORTATIONS DES LIBRAIRIES ----------#
# =============================================
from fastapi import FastAPI
from fastapi.responses import Response


# =============================================
#------ IMPORTATIONS DES LIBRAIRIES ----------#
# =============================================
from src.api.backend.controllers.controller_severite import router as severite_router
# from src.api.backend.controllers.controller_frequence import router as frequence_router


# =============================================
#------ AJOUT DES ENDPOINTS ----------#
# =============================================
app = FastAPI(
    title="API Prime Pricing",
    version="1.0.0"
)

app.include_router(severite_router)
# app.include_router(frequence_router)

@app.get("/")
def read_root():
    return {"message": "API Prime Pricing is running"}


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)

 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.backend.server:app", host="127.0.0.1", port=8000, reload=True)