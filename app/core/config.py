"""
Centralized application configuration.

This module reads upload-related settings from environment variables and
provides safe defaults for local development.
"""

from __future__ import annotations

import os
from pathlib import Path

# Upload directory can be overridden through environment variable.
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))

# Maximum upload size in bytes (default: 5 MiB).
MAX_UPLOAD_SIZE_BYTES = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(5 * 1024 * 1024)))

# Allowed MIME types for uploaded files.
ALLOWED_UPLOAD_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

