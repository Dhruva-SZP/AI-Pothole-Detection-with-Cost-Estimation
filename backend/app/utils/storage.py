"""
File Storage and Path Utilities.
Handles safe saving of uploaded raw images, annotated images, and directory lifecycle.
"""

import os
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename
from app.errors import APIError


def is_allowed_file(filename: str, allowed_extensions: set) -> bool:
    """
    Checks if a file has an approved extension.
    """
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in allowed_extensions


def ensure_storage_directories(upload_folder: Path, annotated_folder: Path):
    """
    Creates upload and annotated directories if they do not exist.
    """
    upload_folder.mkdir(parents=True, exist_ok=True)
    annotated_folder.mkdir(parents=True, exist_ok=True)


def save_uploaded_file(file_storage, target_dir: Path, allowed_extensions: set) -> tuple[str, Path]:
    """
    Safely saves an uploaded file with a UUID prefix to prevent collisions.
    Returns:
        tuple[str, Path]: (stored_filename, absolute_file_path)
    """
    if not file_storage or not file_storage.filename:
        raise APIError("No file provided in the upload payload.", status_code=400)

    original_filename = secure_filename(file_storage.filename)
    if not is_allowed_file(original_filename, allowed_extensions):
        raise APIError(
            f"Invalid file type. Allowed extensions: {', '.join(sorted(allowed_extensions))}",
            status_code=415
        )

    ext = original_filename.rsplit(".", 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
    target_dir.mkdir(parents=True, exist_ok=True)
    destination_path = target_dir / unique_filename

    file_storage.save(str(destination_path))
    return unique_filename, destination_path
