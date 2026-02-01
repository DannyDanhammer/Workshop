#!/usr/bin/env python3
import os
import sys
import requests
from pathlib import Path

# === Configuration ===
STOW_URL = "http://192.168.1.8:8080/studies"
BOUNDARY = "DICOMWEBBOUNDARY"
HEADERS_BASE = {
    "Accept": "application/dicom+json",
}

def send_dicom_study(directory: str):
    """Send all DICOM files in a directory to a DICOMweb STOW-RS endpoint, byte-for-byte identical."""
    dcm_files = list(Path(directory).rglob("*.dcm"))
    if not dcm_files:
        print(f"No DICOM files found in {directory}")
        sys.exit(1)

    print(f"Preparing to upload {len(dcm_files)} DICOM files to {STOW_URL}...")

    # Build multipart body manually, preserving raw bytes
    body_parts = []
    for dcm_path in dcm_files:
        try:
            with open(dcm_path, "rb") as f:
                data = f.read()
            body_parts.append(
                f"--{BOUNDARY}\r\n"
                "Content-Type: application/dicom\r\n\r\n".encode("utf-8")
                + data
                + b"\r\n"
            )
            print(f"Queued: {dcm_path.name} ({len(data)} bytes)")
        except Exception as e:
            print(f"Skipping {dcm_path}: {e}")

    # Final boundary
    body_parts.append(f"--{BOUNDARY}--\r\n".encode("utf-8"))
    body = b"".join(body_parts)

    headers = {
        **HEADERS_BASE,
        "Content-Type": f'multipart/related; type="application/dicom"; boundary={BOUNDARY}',
    }

    response = requests.post(STOW_URL, headers=headers, data=body, timeout=120)

    print(f"Response status: {response.status_code}")
    try:
        print(response.json())
    except Exception:
        print(response.text)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python stow_send.py /path/to/dicom/study")
        sys.exit(1)
    send_dicom_study(sys.argv[1])
