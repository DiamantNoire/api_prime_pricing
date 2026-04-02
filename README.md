# API Prime Pricing

Projet de prediction de prime auto base sur deux modeles ML (frequence et severite), exposes via une API FastAPI et une application Streamlit.

## Architecture

- App Streamlit: interface web utilisateur pour la simulation et la consultation des predictions
- API FastAPI: endpoints d'inference et de healthcheck
- Modeles ML: entrainement frequence/severite et fusion de la prime
- Artefacts modeles: modeles exportes utilises par l'API en inference
- Base de donnees: stockage SQLite local

Correspondance des dossiers:

- `src/app/`: application Streamlit principale
- `src/api/backend/`: API FastAPI
- `src/models/`: pipeline et scripts ML
- `output_models/modeles/`: artefacts JSON des modeles
- `db/`: base SQLite locale

## URLs de production

- API FastAPI: https://api-prime-pricing.onrender.com
- App Streamlit: https://api-prime-pricing-app-cas.onrender.com

## Endpoints API principaux

- `GET /`
- `GET /health`
- `GET /predictio_frequence/health`
- `GET /predictio_severite/health`
- `POST /predict_frequence`
- `POST /predict_severite`
- `POST /predict_price`
- `GET /contrats?limit=20`
- `GET /contrats/{id_contrat}`
- `POST /contrats`
- `PUT /contrats/{id_contrat}`
- Documentation OpenAPI: `/docs`

## Installation locale (uv recommande)

Prerequis:

- Python 3.11+
- `uv` installe (`pip install uv`)

Setup:

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

Lancer l'API:

```bash
uvicorn src.api.backend.server:app --host 0.0.0.0 --port 8000
```

Lancer l'application Streamlit locale (front principal):

```bash
streamlit run src/app/app.py --server.address=0.0.0.0 --server.port=8501
```

## Qualite et tests

Lancer le controle qualite local:

```bash
bash lint_and_typecheck.sh
```

Lancer les tests:

```bash
pytest
```

## CI/CD GitHub Actions

### CI

Workflow: `CI API Prime Pricing`

- Format/lint: black, ruff, flake8, pylint
- Tests: pytest
- Validation Docker: build + smoke test des endpoints

### CD

Workflow: `CD API Prime Pricing`

- Declenchement automatique si la CI est `success` sur `main`
- Appel des deux deploy hooks Render:
  - `api_prime_pricing`
  - `api_prime_pricing_app`

Actions: https://github.com/DiamantNoire/api_prime_pricing/actions

## Deploiement Render

Points importants:

- Les deux services doivent pointer sur la branche `main`
- Le service API est configure en mode Docker (voir `render.yaml`)
- Lancement API via le `CMD` du `Dockerfile`

Les deploiements sont automatises via GitHub Actions CD (deploy hooks).

## Exemples rapides (API)

Health:

```bash
curl -s https://api-prime-pricing.onrender.com/health
curl -s https://api-prime-pricing.onrender.com/predictio_frequence/health
curl -s https://api-prime-pricing.onrender.com/predictio_severite/health
```

Prediction frequence:

```bash
JSON_FREQUENCE='{"bonus":0.42,"type_contrat":"Mini","duree_contrat":6,"anciennete_info":3,"freq_paiement":"Quarterly","paiement":"Yes","utilisation":"Professional","code_postal":"75015","conducteur2":"No","age_conducteur1":31,"sex_conducteur1":"M","anciennete_permis1":12,"anciennete_vehicule":2.1,"cylindre_vehicule":1498,"din_vehicule":110,"essence_vehicule":"Hybrid","marque_vehicule":"TOYOTA","modele_vehicule":"YARIS","vitesse_vehicule":180,"type_vehicule":"Tourism","prix_vehicule":24500,"poids_vehicule":1200}'

curl -s -X POST https://api-prime-pricing.onrender.com/predict_frequence \
  -H "Content-Type: application/json" \
  -d "$JSON_FREQUENCE"
```

Prediction severite:

```bash
JSON_SEVERITE='{"bonus":0.61,"type_contrat":"Median1","duree_contrat":12,"anciennete_info":5,"freq_paiement":"Monthly","paiement":"Yes","utilisation":"WorkPrivate","code_postal":"69003","conducteur2":"Yes","age_conducteur1":45,"age_conducteur2":41,"sex_conducteur1":"F","sex_conducteur2":"M","anciennete_permis1":25,"anciennete_permis2":20,"anciennete_vehicule":4.5,"cylindre_vehicule":1598,"din_vehicule":130,"essence_vehicule":"Diesel","marque_vehicule":"PEUGEOT","modele_vehicule":"3008","vitesse_vehicule":195,"type_vehicule":"Tourism","prix_vehicule":32900,"poids_vehicule":1520}'

curl -s -X POST https://api-prime-pricing.onrender.com/predict_severite \
  -H "Content-Type: application/json" \
  -d "$JSON_SEVERITE"
```

Prediction prime (frequence x severite):

```bash
curl -s -X POST https://api-prime-pricing.onrender.com/predict_price \
  -H "Content-Type: application/json" \
  -d "$JSON_SEVERITE"
```

Creation d'un contrat (endpoint `POST /contrats`):

```bash
JSON_CONTRAT='{"id_client":"cli_001","id_vehicule":"veh_001","id_contrat":"ctr_001","bonus":0.58,"type_contrat":"Median1","duree_contrat":12,"anciennete_info":4,"freq_paiement":"Monthly","paiement":"Yes","utilisation":"WorkPrivate","code_postal":"69003","conducteur2":"Yes","age_conducteur1":40,"age_conducteur2":37,"sex_conducteur1":"M","sex_conducteur2":"F","anciennete_permis1":22,"anciennete_permis2":19,"anciennete_vehicule":3.5,"cylindre_vehicule":1598,"din_vehicule":120,"essence_vehicule":"Gasoline","marque_vehicule":"RENAULT","modele_vehicule":"MEGANE","debut_vente_vehicule":2,"fin_vente_vehicule":8,"vitesse_vehicule":190,"type_vehicule":"Tourism","prix_vehicule":27900,"poids_vehicule":1350,"nombre_sinistres":0,"montant_sinistre":0.0}'

curl -s -X POST https://api-prime-pricing.onrender.com/contrats \
  -H "Content-Type: application/json" \
  -d "$JSON_CONTRAT"
```
