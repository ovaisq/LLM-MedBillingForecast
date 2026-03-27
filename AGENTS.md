# AGENTS.md
# Guidelines for AI Coding Agents in LLM-MedBillingForecast

## Project Overview
Medical billing forecasting system using LLMs (Ollama) and FastAPI/Flask. Processes patient visit notes to generate ICD-10/CPT/HCPCS codes and billing estimates.

## Tech Stack
- **Frameworks**: FastAPI (primary), Flask (legacy)
- **Database**: PostgreSQL with psycopg2
- **LLM**: Ollama (medllama2, phi4, deepseek-llm, etc.)
- **Auth**: JWT (python-jose)
- **Encryption**: Fernet (cryptography)
- **Deployment**: Gunicorn WSGI, Docker

## Commands

### Dependencies
```bash
pip install -r requirements.txt
```

### Run Application
```bash
# FastAPI (development)
python main.py

# FastAPI (production)
gunicorn -c gunicorn.conf.py main:app

# Flask (legacy)
python zollama.py
```

### Testing
```bash
# Run all tests
python testit.py

# Run single test class
python -m unittest testit.TestFastAPIApp

# Run single test method
python -m unittest testit.TestFastAPIApp.test_login_endpoint

# Run with verbose output
python -m unittest -v testit.TestFastAPIApp
```

### Linting (if available)
```bash
# Check for style issues
flake8 *.py app/ services/

# Type checking
mypy app/ services/
```

## Code Style Guidelines

### Imports (PEP 8)
1. Standard library imports (alphabetical)
2. Third-party imports (alphabetical)
3. Local application imports (alphabetical)

```python
import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from database import insert_data_into_table
```

### Formatting
- **Indentation**: 4 spaces (no tabs)
- **Line Length**: 100 characters max
- **Quotes**: Double quotes for strings, single quotes for dict keys where needed
- **Trailing commas**: Required in multi-line structures

### Naming Conventions
- **Modules**: `lowercase.py` or `lowercase_with_underscores.py`
- **Classes**: `PascalCase`
- **Functions/Methods**: `snake_case`
- **Constants**: `UPPER_CASE`
- **Private**: `_leading_underscore` prefix
- **Variables**: `snake_case` (descriptive, no abbreviations)

### Type Hints
- Use type hints for all function parameters and return types
- Use `from __future__ import annotations` for Python 3.9+ features
- Use `Optional[X]` for nullable values
- Use `dict[str, Any]` not `Dict[str, Any]`
- Use `list[X]` not `List[X]`

```python
def analyze_visit_note(visit_note_id: str) -> bool:
    ...

def get_patient_record(patient_id: str) -> list[dict[str, Any]]:
    ...
```

### Docstrings
Use triple double quotes with Google style:

```python
def function_name(param: str) -> dict[str, Any]:
    """Short description of what this does.

    Args:
        param: Description of the parameter

    Returns:
        Description of return value

    Raises:
        HTTPException: When error condition occurs
    """
```

### Error Handling

**FastAPI**: Use HTTPException with appropriate status codes
```python
from fastapi import HTTPException

if not result:
    raise HTTPException(status_code=502, detail="Ollama Server not available")
```

**General**: Log errors before raising
```python
import logging

try:
    result = some_operation()
except Exception as e:
    logging.error("Error in operation: %s", str(e))
    raise HTTPException(status_code=500, detail="Internal server error")
```

### Configuration
- Use `setup.config` for local configuration (copied from `setup.config.template`)
- Use environment variables for production secrets
- Access via `app.core.config.settings` in FastAPI, `config.get_config()` elsewhere

### Database
- Use parameterized queries with `%s` placeholders
- Use `get_select_query_result_dicts()` for SELECT queries returning dicts
- Use `insert_data_into_table()` for INSERT operations
- Always handle `psycopg2.Error` exceptions

### Security
- Never log secrets, API keys, or tokens
- Use JWT for authentication
- Encrypt patient data using Fernet encryption
- Check `PATIENT_DATA_ENCRYPTION_ENABLED` flag

### Async/Await
- Use `asyncio.to_thread()` for blocking I/O operations
- Prefer async patterns in FastAPI endpoints

```python
async def fetch_code(prompt_key: str, content: str) -> dict[str, Any]:
    return await asyncio.to_thread(prompt_chat, llm, prompts[prompt_key] + content, False)
```

### Logging
- Use module-level logger or `logging` directly
- Format: `logging.info("Message: %s", variable)`
- Log patient note IDs truncated for privacy: `patient_note_id[0:10]`

### Pydantic Models
- Define in `app/models/schemas.py`
- Use descriptive field names
- Include docstrings for all models
- Use `Optional[X]` for nullable fields

```python
class PatientRecord(BaseModel):
    """Complete patient record with notes, documents, and codes."""
    patient_id: str
    patient_note_id: str
    patient_note: dict[str, Any]
    patient_document: Optional[dict[str, Any]] = None
```

### Legacy Flask Code
- Still exists in `zollama.py`
- Use `@jwt_required()` decorator for protected routes
- Return `jsonify()` responses
- Use `abort()` for error responses

## File Organization
```
app/
  main.py              # FastAPI app entry
  api/v1/endpoints.py  # API routes
  core/                # Config, security utils
  models/schemas.py    # Pydantic models

services/
  analysis.py          # Business logic

*.py                   # Legacy Flask, utils, database

testit.py             # Unit tests
```

## Testing
- Use `unittest.TestCase` for test classes
- Use `TestClient` from FastAPI for endpoint testing
- Mock external services (Ollama, database) using `unittest.mock`
- Override dependencies to bypass auth in tests
- Test both success and failure cases

## Critical Notes
- Patient data must be encrypted at rest
- Ollama server availability varies (handle 502 errors)
- LLM responses need decryption before processing
- Database uses JSONB columns for flexible document storage
- HCPCS codes are Medicare-specific with locality-based pricing
