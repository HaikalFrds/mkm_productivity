import os

TARGET_PROCESS_RATIO = 86.0

# ── Development Mode ──────────────────────────────────────────────────────────
# Set environment variable MKM_DEV_MODE=true to enable (never hardcoded)
DEV_MODE = os.getenv("MKM_DEV_MODE", "false").lower() == "true"
DEV_USER = {
    "id":   1,
    "name": "Administrator",
    "nik":  "admin",
    "role": "admin",
}
DEV_START_PAGE = "input_laporan"  # "dashboard" | "input_laporan" | "riwayat" | "visualisasi" | "master_data"
