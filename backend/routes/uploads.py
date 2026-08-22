"""
Document upload for the public Employee Registration Form (resume / ID proof).
Public by design -- an applicant has no account yet when submitting these --
but files are restricted by type/size and stored under a random filename.
"""
import os
import uuid

from fastapi import APIRouter, HTTPException, UploadFile, File, status

from config import settings

router = APIRouter(prefix="/api/uploads", tags=["Uploads"])

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"}


@router.post("", summary="Upload a resume or ID proof document (public)")
async def upload_document(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Allowed: PDF, JPG, PNG, DOC, DOCX.",
        )

    contents = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB}MB.",
        )

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}{ext}"
    stored_path = os.path.join(settings.UPLOAD_DIR, stored_name)
    with open(stored_path, "wb") as f:
        f.write(contents)

    return {"url": f"/uploads/{stored_name}", "filename": file.filename}
