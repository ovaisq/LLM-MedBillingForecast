"""Pydantic models for request/response bodies."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Request body for login endpoint."""
    api_key: str


class LoginResponse(BaseModel):
    """Response body for login endpoint."""
    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str


class VisitNote(BaseModel):
    """Patient visit note data."""
    patient_note_id: str
    patient_id: str
    patient_note: dict[str, Any]


class PatientDocument(BaseModel):
    """Patient document data."""
    patient_document_id: str
    analysis_document: dict[str, Any]


class PatientCodes(BaseModel):
    """Patient codes data."""
    patient_document_id: str
    codes_document: dict[str, Any]


class PatientRecord(BaseModel):
    """Complete patient record with notes, documents, and codes."""
    patient_id: str
    patient_note_id: str
    patient_note: dict[str, Any]
    patient_document: Optional[dict[str, Any]] = None
    patient_codes: Optional[dict[str, Any]] = None


class AnalysisResponse(BaseModel):
    """Response for analysis endpoints."""
    status: str
    message: str
    patient_note_id: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: datetime


class PatientRecordList(BaseModel):
    """List of patient records."""
    records: list[PatientRecord]
