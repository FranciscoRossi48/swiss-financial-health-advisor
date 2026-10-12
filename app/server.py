"""Production entry point for Pulse: the API under /api and the built web app at the root.

Serving both from one process keeps the deployment to a single Cloud Run service and lets the
web app call the API on the same origin, so no CORS configuration is needed in production.
Run locally with: uvicorn server:app --app-dir app (after `npm run build` in web/).
"""

from __future__ import annotations

import os
from pathlib import Path

from api import app as api_app
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[1]
WEB_DIST = Path(os.environ.get("PULSE_WEB_DIST", ROOT / "web" / "dist"))

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/api", api_app)
if WEB_DIST.is_dir():
    app.mount("/", StaticFiles(directory=WEB_DIST, html=True), name="web")
