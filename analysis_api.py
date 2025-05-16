# analysis_api.py
import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from orchestrator import AnalysisOrchestrator

app = FastAPI()
orchestrator = AnalysisOrchestrator()

class AnalysisRequest(BaseModel):
    repo_path: str  # e.g., "sample_repo"

@app.post("/analyze")
async def analyze_code(request: AnalysisRequest):
    if not os.path.exists(request.repo_path):
        raise HTTPException(status_code=400, detail="Repository path does not exist")

    try:
        results = orchestrator.analyze_repository(request.repo_path)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
