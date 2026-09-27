import os
import uuid
import re
from pathlib import Path
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException, status
from app.config import DATA_DIR

INBOX_UPLOAD_DIR = DATA_DIR / "uploads" / "inbox"
INBOX_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
ALLOWED_DOCUMENT_EXTENSIONS = {".pdf"}
ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_DOCUMENT_EXTENSIONS

ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/heic", "image/heif",
    "application/pdf", "application/octet-stream"  # octet-stream allowed if extension matches
}

def clean_filename(filename: str) -> str:
    """Sanitizes filename by removing path traversal and special characters."""
    filename = Path(filename).name
    # Replace spaces and special characters with underscores
    filename = re.sub(r"[^\w\.-]", "_", filename)
    return filename

async def save_uploaded_file(upload_file: UploadFile) -> Tuple[str, str, str, int, str]:
    """
    Saves an uploaded file to data/uploads/inbox/ if it meets image or PDF criteria.
    Returns: (stored_rel_path, clean_filename, mime_type, file_size, item_type)
    """
    original_name = clean_filename(upload_file.filename or "uploaded_file")
    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{extension}'. Only images (.jpg, .png, .webp, .heic) and PDFs (.pdf) are supported."
        )

    # Determine item_type
    if extension in ALLOWED_IMAGE_EXTENSIONS:
        item_type = "image"
    else:
        item_type = "document"

    # Generate unique stored filename
    unique_prefix = uuid.uuid4().hex[:12]
    stored_filename = f"{unique_prefix}_{original_name}"
    target_path = INBOX_UPLOAD_DIR / stored_filename

    # Read content and enforce max size (e.g. 25 MB)
    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB
    content = await upload_file.read()
    file_size = len(content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds maximum limit of 25MB."
        )

    with open(target_path, "wb") as f:
        f.write(content)

    # Return relative path for database storage
    rel_path = f"uploads/inbox/{stored_filename}"
    mime_type = upload_file.content_type or ("image/jpeg" if item_type == "image" else "application/pdf")

    return rel_path, original_name, mime_type, file_size, item_type
