"""API v1 endpoints for medical billing forecasting."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.security import create_access_token, get_current_user
from app.models.schemas import (
    AnalysisResponse,
    HealthResponse,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    PatientRecord,
)
from services.analysis import analyze_visit_note, analyze_visit_notes, get_patient_record

router = APIRouter(prefix="/api/v1", tags=["billing-forecast"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    from datetime import datetime, timezone

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc),
    )


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Generate JWT access token.

    Args:
        request: Login request with API key

    Returns:
        Login response with access token
    """
    if request.api_key != settings.service_shared_secret:
        raise HTTPException(status_code=401, detail="Invalid secret")

    access_token = create_access_token({"sub": settings.identity})
    return LoginResponse(access_token=access_token)


@router.get("/analyze-visit-notes", response_model=MessageResponse)
async def analyze_visit_notes_endpoint(
    current_user: dict = Depends(get_current_user),
):
    """Analyze all OSCE format Visit Notes in database.

    Args:
        current_user: Verified user from JWT token

    Returns:
        Message response
    """
    try:
        if not analyze_visit_notes():
            raise HTTPException(status_code=502, detail="Ollama Server not available")
        return MessageResponse(message="analyze_visit_notes completed")
    except HTTPException:
        raise
    except Exception as e:
        logging.error("Error in analyze_visit_notes: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/analyze-visit-note", response_model=MessageResponse)
async def analyze_visit_note_endpoint(
    visit_note_id: str = Query(..., description="Patient note identifier"),
    current_user: dict = Depends(get_current_user),
):
    """Analyze a specific OSCE format Visit Note.

    Args:
        visit_note_id: Patient note identifier
        current_user: Verified user from JWT token

    Returns:
        Message response
    """
    try:
        result = analyze_visit_note(visit_note_id)
        if not result:
            raise HTTPException(status_code=502, detail="Ollama Server not available")
        return MessageResponse(message="analyze_visit_note completed")
    except HTTPException:
        raise
    except Exception as e:
        logging.error("Error in analyze_visit_note: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/get-patient/{patient_id}", response_model=PatientRecord)
async def get_patient_endpoint(
    patient_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get patient record with notes, documents, and billing information.

    Args:
        patient_id: Patient identifier
        current_user: Verified user from JWT token

    Returns:
        Patient record data
    """
    try:
        patient_record = get_patient_record(patient_id)
        if not patient_record:
            raise HTTPException(status_code=404, detail="Patient not found")
        # Return first record as PatientRecord model
        return patient_record[0]
    except HTTPException:
        raise
    except Exception as e:
        logging.error("Error in get_patient: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
