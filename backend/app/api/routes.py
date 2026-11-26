from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from jose import jwt
import bcrypt
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timedelta, timezone
from pymongo.errors import PyMongoError
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import UploadFile, File
from PIL import Image, UnidentifiedImageError
import hashlib
import io
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import json
import base64

from app.core.config import settings
from app.db.mongodb import database
from app.services.disease_service import DiseaseInferenceService


router = APIRouter()
security = HTTPBearer()


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    phone: str | None = Field(default=None, max_length=20)
    state: str | None = Field(default=None, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ProfileUpdateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    state: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    farm_size_acres: float | None = Field(default=None, ge=0)


class CropRecommendationRequest(BaseModel):
    nitrogen: float = Field(ge=0, le=300)
    phosphorus: float = Field(ge=0, le=300)
    potassium: float = Field(ge=0, le=300)
    temperature: float = Field(ge=-20, le=60)
    humidity: float = Field(ge=0, le=100)
    ph: float = Field(ge=0, le=14)
    rainfall: float = Field(ge=0, le=1000)


def create_token(user_id: str, role: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_minutes)
    payload = {"sub": user_id, "role": role, "exp": expires}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


async def current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        try:
            oid = ObjectId(user_id)
        except (InvalidId, TypeError):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user = await database.users.find_one({"_id": oid})
        if not user or not user.get("is_active", True):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


def public_user(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "role": user.get("role", "farmer"),
        "phone": user.get("phone"),
        "state": user.get("state"),
        "district": user.get("district"),
        "farm_size_acres": user.get("farm_size_acres"),
        "created_at": user["created_at"].isoformat(),
    }


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


@router.get("/health")
async def health():
    crop_model_available = resolve_model_path("crop_recommendation.joblib").exists()
    disease_model_available = resolve_model_path("crop_disease_mobilenetv2.pt").exists()
    return {
        "status": "healthy",
        "database": "configured",
        "database_name": settings.mongodb_db,
        "models": {
            "crop_recommendation": "available" if crop_model_available else "not trained",
            "crop_disease": "available" if disease_model_available else "not trained",
        },
    }


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    email = str(request.email).strip().lower()
    try:
        existing = await database.users.find_one({"email": email})
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")

        now = datetime.now(timezone.utc)
        document = {
            "name": request.name.strip(),
            "email": email,
            "password_hash": hash_password(request.password),
            "phone": request.phone,
            "state": request.state,
            "district": None,
            "farm_size_acres": None,
            "role": "farmer",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        result = await database.users.insert_one(document)
        document["_id"] = result.inserted_id
        token = create_token(str(result.inserted_id), "farmer")
        return {"access_token": token, "token_type": "bearer", "user": public_user(document)}
    except HTTPException:
        raise
    except PyMongoError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable") from exc


@router.post("/auth/login")
async def login(request: LoginRequest):
    email = str(request.email).strip().lower()
    try:
        user = await database.users.find_one({"email": email})
        if not user or not user.get("is_active", True):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        if not verify_password(request.password, user["password_hash"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        token = create_token(str(user["_id"]), user.get("role", "farmer"))
        return {"access_token": token, "token_type": "bearer", "user": public_user(user)}
    except HTTPException:
        raise
    except PyMongoError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable") from exc


@router.get("/auth/me")
async def me(user: dict = Depends(current_user)):
    return public_user(user)


@router.put("/users/profile")
async def update_profile(request: ProfileUpdateRequest, user: dict = Depends(current_user)):
    update = {
        "name": request.name.strip(),
        "phone": request.phone,
        "state": request.state,
        "district": request.district,
        "farm_size_acres": request.farm_size_acres,
        "updated_at": datetime.now(timezone.utc),
    }
    try:
        await database.users.update_one({"_id": user["_id"]}, {"$set": update})
        updated = await database.users.find_one({"_id": user["_id"]})
        return public_user(updated)
    except PyMongoError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable") from exc


_crop_model_bundle = None
_disease_service = None


def get_disease_service():
    global _disease_service
    if _disease_service is None:
        model_path = resolve_model_path("crop_disease_mobilenetv2.pt")
        classes_path = resolve_model_path("crop_disease_classes.json")
        if not model_path.exists() or not classes_path.exists():
            return None
        _disease_service = DiseaseInferenceService(model_path, classes_path)
    return _disease_service


DISEASE_GUIDANCE = {
    "Pepper__bell___Bacterial_spot": "Remove severely affected leaves, avoid overhead irrigation, improve airflow, and confirm treatment choices with a local plant protection officer.",
    "Pepper__bell___healthy": "No disease sign was predicted. Continue regular field inspection and monitor for changes.",
    "Potato___Early_blight": "Remove infected debris, rotate crops, avoid prolonged leaf wetness, and seek local guidance before fungicide use.",
    "Potato___Late_blight": "This disease can spread quickly. Isolate suspected plants, avoid irrigation on leaves, and contact local agricultural experts promptly.",
    "Potato___healthy": "No disease sign was predicted. Maintain sanitation and routine scouting.",
    "Tomato_Bacterial_spot": "Remove infected material, avoid overhead watering, sanitize tools, and consult local experts for crop-specific control.",
    "Tomato_Early_blight": "Remove infected lower leaves, improve airflow, avoid overhead watering, and confirm fungicide guidance locally.",
    "Tomato_Late_blight": "This disease can spread rapidly. Inspect nearby plants, avoid wet foliage, and contact a plant protection specialist promptly.",
    "Tomato_Leaf_Mold": "Increase ventilation, reduce humidity, remove affected leaves, and consult local guidance before chemical treatment.",
    "Tomato_Septoria_leaf_spot": "Remove infected leaves and debris, avoid overhead irrigation, rotate crops, and seek local management guidance.",
    "Tomato_Spider_mites_Two_spotted_spider_mite": "The prediction may indicate mite damage rather than an infection. Inspect leaf undersides and seek integrated pest-management guidance.",
    "Tomato__Target_Spot": "Remove infected debris, improve airflow, avoid leaf wetness, and consult local experts before treatment.",
    "Tomato__Tomato_YellowLeaf__Curl_Virus": "Remove severely infected plants where locally recommended, control whiteflies, and use resistant varieties when available.",
    "Tomato__Tomato_mosaic_virus": "Sanitize tools and hands, remove infected plants if appropriate, control plant handling, and use certified seed/seedlings.",
    "Tomato_healthy": "No disease sign was predicted. Continue regular field monitoring.",
}

DISEASE_DISPLAY_NAMES = {
    "Pepper__bell___Bacterial_spot": "Pepper — Bacterial Spot",
    "Pepper__bell___healthy": "Pepper — Healthy",
    "Potato___Early_blight": "Potato — Early Blight",
    "Potato___Late_blight": "Potato — Late Blight",
    "Potato___healthy": "Potato — Healthy",
    "Tomato_Bacterial_spot": "Tomato — Bacterial Spot",
    "Tomato_Early_blight": "Tomato — Early Blight",
    "Tomato_Late_blight": "Tomato — Late Blight",
    "Tomato_Leaf_Mold": "Tomato — Leaf Mold",
    "Tomato_Septoria_leaf_spot": "Tomato — Septoria Leaf Spot",
    "Tomato_Spider_mites_Two_spotted_spider_mite": "Tomato — Spider Mite Damage",
    "Tomato__Target_Spot": "Tomato — Target Spot",
    "Tomato__Tomato_YellowLeaf__Curl_Virus": "Tomato — Yellow Leaf Curl Virus",
    "Tomato__Tomato_mosaic_virus": "Tomato — Tomato Mosaic Virus",
    "Tomato_healthy": "Tomato — Healthy",
}
def resolve_model_path(filename: str) -> Path:
    configured = Path(settings.model_storage_path)
    candidates = [
        configured / filename,
        Path.cwd() / configured / filename,
        Path.cwd().parent / "ml" / "saved_models" / filename,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[-1]


def load_crop_model():
    global _crop_model_bundle
    if _crop_model_bundle is None:
        model_path = resolve_model_path("crop_recommendation.joblib")
        if not model_path.exists():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The crop recommendation model is not available",
            )
        _crop_model_bundle = joblib.load(model_path)
    return _crop_model_bundle


@router.post("/crops/recommend")
async def recommend_crop(request: CropRecommendationRequest, user: dict = Depends(current_user)):
    bundle = load_crop_model()
    features = bundle["features"]
    values = pd.DataFrame([[
        request.nitrogen,
        request.phosphorus,
        request.potassium,
        request.temperature,
        request.humidity,
        request.ph,
        request.rainfall,
    ]], columns=features)
    model = bundle["model"]
    encoder = bundle["label_encoder"]

    encoded_prediction = int(model.predict(values)[0])
    recommended_crop = encoder.inverse_transform([encoded_prediction])[0]
    alternatives = []
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(values)[0]
        top_indices = np.argsort(probabilities)[::-1][:3]
        alternatives = [
            {
                "crop": encoder.inverse_transform([int(index)])[0],
                "probability": round(float(probabilities[index]), 4),
            }
            for index in top_indices
        ]

    document = {
        "user_id": user["_id"],
        "inputs": {
            "N": request.nitrogen,
            "P": request.phosphorus,
            "K": request.potassium,
            "temperature": request.temperature,
            "humidity": request.humidity,
            "ph": request.ph,
            "rainfall": request.rainfall,
        },
        "recommended_crop": recommended_crop,
        "alternatives": alternatives,
        "model": "random_forest",
        "created_at": datetime.now(timezone.utc),
    }
    try:
        await database.crop_recommendations.insert_one(document)
    except PyMongoError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Prediction history database unavailable")

    return {
        "recommended_crop": recommended_crop,
        "alternatives": alternatives,
        "model_type": "Random Forest",
        "disclaimer": "This is a data-based recommendation, not a guarantee of crop suitability.",
    }


@router.get("/crops/history")
async def crop_history(user: dict = Depends(current_user)):
    cursor = database.crop_recommendations.find(
        {"user_id": user["_id"]},
        {"_id": 0},
    ).sort("created_at", -1).limit(50)
    results = await cursor.to_list(length=50)
    for result in results:
        if hasattr(result.get("created_at"), "isoformat"):
            result["created_at"] = result["created_at"].isoformat()
    return results


@router.get("/disease/history")
async def disease_history(user: dict = Depends(current_user)):
    cursor = database.disease_predictions.find(
        {"user_id": user["_id"]},
        {"_id": 0, "top_predictions": 1, "predicted_class": 1,
         "confidence": 1, "image_name": 1, "image_hash": 1,
         "thumbnail_base64": 1, "status": 1, "created_at": 1},
    ).sort("created_at", -1).limit(50)
    results = await cursor.to_list(length=50)
    for result in results:
        predicted_class = result.get("predicted_class")
        result["disease_name"] = DISEASE_DISPLAY_NAMES.get(
            predicted_class,
            predicted_class,
        )
        if result.get("image_hash"):
            result["image_url"] = f"/api/disease/history/image/{result['image_hash']}"
        if hasattr(result.get("created_at"), "isoformat"):
            result["created_at"] = result["created_at"].isoformat()
    return results


@router.get("/disease/history/image/{image_hash}")
async def disease_history_image(image_hash: str, user: dict = Depends(current_user)):
    record = await database.disease_predictions.find_one({
        "user_id": user["_id"],
        "image_hash": image_hash,
        "status": "completed",
    })
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved image not found")

    image_path = Path(record.get("image_path", ""))
    if not image_path.is_absolute():
        candidates = [
            Path.cwd() / image_path,
            Path.cwd().parent / image_path,
        ]
        image_path = next((path for path in candidates if path.exists()), image_path)
    if not image_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved image file not found")

    from fastapi.responses import FileResponse
    media_type = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"
    return FileResponse(image_path, media_type=media_type)


@router.get("/analytics/overview")
async def analytics_overview(user: dict = Depends(current_user)):
    disease_count = await database.disease_predictions.count_documents(
        {"user_id": user["_id"], "status": "completed"}
    )
    crop_count = await database.crop_recommendations.count_documents(
        {"user_id": user["_id"]}
    )
    disease_cursor = database.disease_predictions.find(
        {"user_id": user["_id"], "status": "completed"},
        {"_id": 0, "predicted_class": 1, "confidence": 1,
         "image_name": 1, "image_hash": 1,
         "thumbnail_base64": 1, "created_at": 1},
    ).sort("created_at", -1).limit(5)
    disease_history = await disease_cursor.to_list(length=5)
    for item in disease_history:
        predicted_class = item.get("predicted_class")
        item["disease_name"] = DISEASE_DISPLAY_NAMES.get(
            predicted_class,
            predicted_class,
        )
        if not item.get("thumbnail_base64") and item.get("image_hash"):
            existing = await database.disease_predictions.find_one(
                {"user_id": user["_id"], "image_hash": item["image_hash"]}
            )
            if existing and existing.get("image_path"):
                existing_path = Path(existing["image_path"])
                if not existing_path.is_absolute():
                    candidates = [
                        Path.cwd() / existing_path,
                        Path.cwd().parent / existing_path,
                    ]
                    existing_path = next((path for path in candidates if path.exists()), existing_path)
                if existing_path.exists():
                    try:
                        with Image.open(existing_path) as existing_image:
                            existing_thumbnail = existing_image.convert("RGB")
                            existing_thumbnail.thumbnail((480, 480), Image.Resampling.LANCZOS)
                            buffer = io.BytesIO()
                            existing_thumbnail.save(buffer, format="JPEG", quality=82)
                            thumbnail_base64 = base64.b64encode(buffer.getvalue()).decode("ascii")
                            item["thumbnail_base64"] = thumbnail_base64
                            await database.disease_predictions.update_one(
                                {"_id": existing["_id"]},
                                {"$set": {"thumbnail_base64": thumbnail_base64}},
                            )
                    except Exception:
                        pass
        if item.get("image_hash"):
            item["image_url"] = f"/api/disease/history/image/{item['image_hash']}"
        if hasattr(item.get("created_at"), "isoformat"):
            item["created_at"] = item["created_at"].isoformat()
    return {
        "disease_analyses": disease_count,
        "crop_recommendations": crop_count,
        "yield_forecasts": 0,
        "recent_disease_analyses": disease_history,
    }


@router.post("/disease/predict")
async def predict_disease(
    file: UploadFile = File(...),
    user: dict = Depends(current_user),
):
    allowed_types = {"image/jpeg": ".jpg", "image/png": ".png"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only JPG, JPEG, and PNG images are supported",
        )

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Image must be 10 MB or smaller")

    try:
        with Image.open(io.BytesIO(content)) as image:
            image.verify()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The uploaded file is not a valid image")

    sha256 = hashlib.sha256(content).hexdigest()
    upload_dir = Path("uploads/disease")
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_path = upload_dir / f"{sha256}{allowed_types[file.content_type]}"
    stored_path.write_bytes(content)

    disease_model = resolve_model_path("crop_disease_mobilenetv2.pt")
    classes_path = resolve_model_path("crop_disease_classes.json")
    if not disease_model.exists() or not classes_path.exists():
        document = {
            "user_id": user["_id"],
            "image_name": file.filename,
            "image_hash": sha256,
            "status": "model_not_available",
            "created_at": datetime.now(timezone.utc),
        }
        try:
            await database.disease_predictions.insert_one(document)
        except PyMongoError:
            pass
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The crop disease model has not been trained or deployed yet",
        )

    try:
        with Image.open(io.BytesIO(content)) as source_image:
            source_image = source_image.copy()
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The uploaded file could not be decoded")

    try:
        service = get_disease_service()
        top_predictions = service.predict(source_image, top_k=3)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Disease model inference failed") from exc

    predicted = top_predictions[0]
    predicted_class = predicted["class_name"]
    thumbnail = source_image.convert("RGB")
    thumbnail.thumbnail((480, 480), Image.Resampling.LANCZOS)
    thumbnail_buffer = io.BytesIO()
    thumbnail.save(thumbnail_buffer, format="JPEG", quality=82)
    thumbnail_base64 = base64.b64encode(thumbnail_buffer.getvalue()).decode("ascii")
    guidance = DISEASE_GUIDANCE.get(
        predicted_class,
        "Remove affected material only where appropriate and consult a local plant protection professional.",
    )
    document = {
        "user_id": user["_id"],
        "image_name": file.filename,
        "image_hash": sha256,
        "image_path": str(stored_path).replace("\\", "/"),
        "thumbnail_base64": thumbnail_base64,
        "predicted_class": predicted_class,
        "confidence": predicted["probability"],
        "top_predictions": top_predictions,
        "status": "completed",
        "created_at": datetime.now(timezone.utc),
    }
    try:
        await database.disease_predictions.insert_one(document)
    except PyMongoError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Prediction history database unavailable")

    return {
        "predicted_class": predicted_class,
        "disease_name": DISEASE_DISPLAY_NAMES.get(predicted_class, predicted_class),
        "crop": predicted_class.split("__")[0].replace("_", " ").split("___")[0],
        "top_predictions": [
            {
                **item,
                "disease_name": DISEASE_DISPLAY_NAMES.get(item["class_name"], item["class_name"]),
            }
            for item in top_predictions
        ],
        "confidence": predicted["probability"],
        "confidence_percent": predicted["confidence_percent"],
        "guidance": guidance,
        "disclaimer": "This is an AI-assisted screening result, not a confirmed diagnosis. Image quality and field conditions affect accuracy. Consult a local agricultural expert before pesticide or high-impact treatment decisions.",
        "test_metrics": {
            "accuracy": 0.9932454165326472,
            "precision_macro": 0.9915142370285913,
            "recall_macro": 0.9934730977104458,
            "f1_macro": 0.9924363968865076,
        },
    }
