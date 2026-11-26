# AgriSense AI

Traditional AI/ML agricultural decision-support platform.

## Technology

- React 19, Vite, Tailwind CSS, Recharts, Lucide
- FastAPI, Pydantic, Motor
- MongoDB
- Docker Compose

## Run locally

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

### Backend

```powershell
cd backend
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs`.

### Docker

```powershell
docker compose up --build
```

## Current status
The premium dashboard shell, registration/login UI, JWT authentication, Mongo-backed user storage, protected profile APIs, API health foundation, real PlantVillage crop-disease inference, and a trained crop recommendation model are implemented.

Dashboard sample/fabricated values have been removed.

The disease CNN is deployed using MobileNetV2 and the trained 15-class PlantVillage checkpoint. Uploaded images are validated and preprocessed before real inference.

The saved crop model is a Random Forest trained on 2,200 cleaned public-dataset rows. It achieved 99.3182% accuracy on the held-out test set and 99.375% mean five-fold cross-validation accuracy. These metrics are recorded in `ml/saved_models/crop_recommendation_metrics.json`.
