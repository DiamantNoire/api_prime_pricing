from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from backend.controllers.contrat_controller import contrat_router
from backend.controllers.contrat_ml_controller import ml_router

app = FastAPI()
app.include_router(contrat_router)
app.include_router(ml_router)


@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)

 
            
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)