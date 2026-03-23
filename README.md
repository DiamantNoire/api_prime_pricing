# API Prime Pricing

Projet de prediction de prime auto avec pipeline ML et API FastAPI.

## Contenu du repo

- `src/models/`: entrainement des modeles, feature engineering et fusion des predictions.
- `src/api/backend/`: API FastAPI publiee pour la prediction.
- `src/api/frontend/`: interface Streamlit locale.
- `output_models/`: artefacts JSON publies avec l'API.
- `db/`: base SQLite locale.

## Endpoints principaux

- `GET /health`: healthcheck global.
- `GET /predictio_frequence/health`: verifie que le modele frequence est charge.
- `POST /predict_frequence`: calcule la prediction frequence sur un JSON unitaire.
- `GET /predictio_severite/health`: verifie que le modele severite est charge.
- `POST /predict_severite`: calcule la prediction severite sur un JSON unitaire.
- `POST /predict_price`: calcule une prime simple avec `frequence * severite`.

## Demarrage local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.api.backend.server:app --host 0.0.0.0 --port 8000
```

## Deploiement Render

Le backend est prepare pour Render:

- chemins de modeles resolves avec `Path`, sans chemin local `/home/...`
- chargement des modeles au startup FastAPI
- commande de demarrage compatible `PORT`
- configuration prete dans `render.yaml`

### Build command

```bash
pip install -r requirements.txt
```

### Start command

```bash
uvicorn src.api.backend.server:app --host 0.0.0.0 --port $PORT
```

### Creation du service

1. Pousser la branche de deploiement sur GitHub.
2. Creer un `Web Service` Python sur Render.
3. Renseigner le build command et le start command ci-dessus.
4. Verifier que `output_models/modeles/model_frequence.json` et `output_models/modeles/model_severite.json` sont bien presents dans le repo distant.

## Tests API

### Local

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/predictio_frequence/health
curl -s http://127.0.0.1:8000/predictio_severite/health
```

### Render

```bash
curl -s https://your-api.onrender.com/health
curl -s https://your-api.onrender.com/predictio_frequence/health
curl -s https://your-api.onrender.com/predictio_severite/health
```

### POST sur les deux endpoints avec un JSON complet

```bash
JSON='{"bonus":0.33,"type_contrat":"Mini","duree_contrat":6,"anciennete_info":3,"freq_paiement":"Quarterly","paiement":"Yes","utilisation":"Professional","code_postal":"75119","conducteur2":"Yes","age_conducteur1":29,"age_conducteur2":27,"sex_conducteur1":"M","sex_conducteur2":"F","anciennete_permis1":11,"anciennete_permis2":8,"anciennete_vehicule":1.7,"cylindre_vehicule":1598,"din_vehicule":132,"essence_vehicule":"Hybrid","marque_vehicule":"TOYOTA","modele_vehicule":"COROLLA","debut_vente_vehicule":2020,"fin_vente_vehicule":2024,"vitesse_vehicule":205,"type_vehicule":"SUV","prix_vehicule":28990,"poids_vehicule":1425}'

curl -s -X POST http://127.0.0.1:8000/predict_frequence -H "Content-Type: application/json" -d "$JSON"
curl -s -X POST http://127.0.0.1:8000/predict_severite -H "Content-Type: application/json" -d "$JSON"
curl -s -X POST http://127.0.0.1:8000/predict_price -H "Content-Type: application/json" -d "$JSON"
```

### POST Render

```bash
curl -s -X POST https://your-api.onrender.com/predict_frequence -H "Content-Type: application/json" -d "$JSON"
curl -s -X POST https://your-api.onrender.com/predict_severite -H "Content-Type: application/json" -d "$JSON"
curl -s -X POST https://your-api.onrender.com/predict_price -H "Content-Type: application/json" -d "$JSON"
```

## 5 payloads aleatoires (hors base) + commandes POST (severite)

### Payload 1

```bash
curl -s -X POST http://127.0.0.1:8000/predict_severite \
  -H "Content-Type: application/json" \
  -d '{"bonus":0.27,"type_contrat":"Mini","duree_contrat":4,"anciennete_info":2,"freq_paiement":"Quarterly","paiement":"Yes","utilisation":"Professional","code_postal":"69008","conducteur2":"Yes","age_conducteur1":31,"age_conducteur2":29,"sex_conducteur1":"M","sex_conducteur2":"F","anciennete_permis1":12,"anciennete_permis2":9,"anciennete_vehicule":2.4,"cylindre_vehicule":1499,"din_vehicule":125,"essence_vehicule":"Hybrid","marque_vehicule":"TOYOTA","modele_vehicule":"C-HR","debut_vente_vehicule":2019,"fin_vente_vehicule":2024,"vitesse_vehicule":198,"type_vehicule":"SUV","prix_vehicule":31500,"poids_vehicule":1460}'
```

### Payload 2

```bash
curl -s -X POST http://127.0.0.1:8000/predict_severite \
  -H "Content-Type: application/json" \
  -d '{"bonus":0.81,"type_contrat":"Maxi","duree_contrat":1,"anciennete_info":8,"freq_paiement":"Yearly","paiement":"No","utilisation":"Retired","code_postal":"13012","conducteur2":"No","age_conducteur1":68,"age_conducteur2":0,"sex_conducteur1":"F","sex_conducteur2":null,"anciennete_permis1":44,"anciennete_permis2":0,"anciennete_vehicule":12.8,"cylindre_vehicule":1198,"din_vehicule":82,"essence_vehicule":"Gasoline","marque_vehicule":"PEUGEOT","modele_vehicule":"208","debut_vente_vehicule":2014,"fin_vente_vehicule":2019,"vitesse_vehicule":172,"type_vehicule":"Tourism","prix_vehicule":13890,"poids_vehicule":1025}'
```

### Payload 3

```bash
curl -s -X POST http://127.0.0.1:8000/predict_severite \
  -H "Content-Type: application/json" \
  -d '{"bonus":0.46,"type_contrat":"Medium","duree_contrat":10,"anciennete_info":5,"freq_paiement":"Monthly","paiement":"Yes","utilisation":"Commuting","code_postal":"31000","conducteur2":"Yes","age_conducteur1":42,"age_conducteur2":40,"sex_conducteur1":"M","sex_conducteur2":"F","anciennete_permis1":22,"anciennete_permis2":19,"anciennete_vehicule":4.1,"cylindre_vehicule":1997,"din_vehicule":184,"essence_vehicule":"Diesel","marque_vehicule":"BMW","modele_vehicule":"320D","debut_vente_vehicule":2018,"fin_vente_vehicule":2023,"vitesse_vehicule":232,"type_vehicule":"Sedan","prix_vehicule":42100,"poids_vehicule":1655}'
```

### Payload 4

```bash
curl -s -X POST http://127.0.0.1:8000/predict_severite \
  -H "Content-Type: application/json" \
  -d '{"bonus":0.12,"type_contrat":"Mini","duree_contrat":2,"anciennete_info":1,"freq_paiement":"Monthly","paiement":"Yes","utilisation":"Urban","code_postal":"75019","conducteur2":"No","age_conducteur1":24,"age_conducteur2":0,"sex_conducteur1":"F","sex_conducteur2":null,"anciennete_permis1":4,"anciennete_permis2":0,"anciennete_vehicule":0.9,"cylindre_vehicule":998,"din_vehicule":70,"essence_vehicule":"Electric","marque_vehicule":"RENAULT","modele_vehicule":"ZOE","debut_vente_vehicule":2021,"fin_vente_vehicule":2025,"vitesse_vehicule":140,"type_vehicule":"City","prix_vehicule":26900,"poids_vehicule":1502}'
```

### Payload 5

```bash
curl -s -X POST http://127.0.0.1:8000/predict_severite \
  -H "Content-Type: application/json" \
  -d '{"bonus":0.63,"type_contrat":"Maxi","duree_contrat":7,"anciennete_info":6,"freq_paiement":"HalfYearly","paiement":"No","utilisation":"Family","code_postal":"44000","conducteur2":"Yes","age_conducteur1":53,"age_conducteur2":50,"sex_conducteur1":"M","sex_conducteur2":"F","anciennete_permis1":31,"anciennete_permis2":28,"anciennete_vehicule":7.3,"cylindre_vehicule":1595,"din_vehicule":150,"essence_vehicule":"Gasoline","marque_vehicule":"VOLKSWAGEN","modele_vehicule":"TIGUAN","debut_vente_vehicule":2017,"fin_vente_vehicule":2024,"vitesse_vehicule":210,"type_vehicule":"SUV","prix_vehicule":38900,"poids_vehicule":1710}'
```
