from __future__ import annotations

import os
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from investor_agent.agent import InvestorDataAgent
from investor_agent.config import OUTPUT_CSV

app = FastAPI(title="Investor Data Agent", version="1.0")

BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "static")
OUTPUT_DIR = os.path.join(STATIC_DIR, "outputs")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/static/index.html")


class RunRequest(BaseModel):
    query: str = Field(..., description='Example: "Fintech investors in India investing $500k–$2M"')
    max_results: int = Field(8, ge=1, le=20)
    max_pages: int | None = Field(None, ge=1)
    provider: str | None = Field(None, description="Force provider: openai or gemini")
    output_mode: str = Field("csv", description="csv or json (json still returns records)")


class RunResponse(BaseModel):
    job_id: str
    records_count: int
    records: list[dict[str, Any]] = []
    csv_url: str | None = None


@app.post("/api/run", response_model=RunResponse)
def run(req: RunRequest):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    job_id = str(uuid.uuid4())
    output_csv = os.path.join(OUTPUT_DIR, f"{job_id}.csv")

    agent = InvestorDataAgent(output_csv=output_csv, sleep_s=1.0)
    try:
        records = agent.run(
            req.query,
            max_results=req.max_results,
            max_pages=req.max_pages,
            provider=req.provider,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Run failed: {e}") from e

    csv_url = f"/api/download/{job_id}" if req.output_mode in ("csv", "json") else None
    return RunResponse(
        job_id=job_id,
        records_count=len(records),
        records=records,
        csv_url=csv_url,
    )


@app.get("/api/download/{job_id}")
def download(job_id: str):
    if "/" in job_id or "\\" in job_id:
        raise HTTPException(status_code=400, detail="Invalid job_id.")
    path = os.path.join(OUTPUT_DIR, f"{job_id}.csv")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="CSV not found.")
    return FileResponse(path, media_type="text/csv", filename=f"{job_id}.csv")


@app.get("/api/health")
def health():
    return JSONResponse({"status": "ok", "default_csv": OUTPUT_CSV})

