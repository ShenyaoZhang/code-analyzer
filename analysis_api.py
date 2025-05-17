## analysis_api.py
#import os
#import json
#from fastapi import FastAPI, HTTPException
#from pydantic import BaseModel
#from orchestrator import AnalysisOrchestrator
#
#app = FastAPI()
#orchestrator = AnalysisOrchestrator()
#
#class AnalysisRequest(BaseModel):
#    repo_path: str  # e.g., "sample_repo"
#
#@app.post("/analyze")
#async def analyze_code(request: AnalysisRequest):
#    if not os.path.exists(request.repo_path):
#        raise HTTPException(status_code=400, detail="Repository path does not exist")
#
#    try:
#        results = orchestrator.analyze_repository(request.repo_path)
#        return results
#    except Exception as e:
#        raise HTTPException(status_code=500, detail=str(e))
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from orchestrator import AnalysisOrchestrator
import os
import shutil
import tempfile
import subprocess

app = FastAPI()
orchestrator = AnalysisOrchestrator()

class AnalysisRequest(BaseModel):
    repo_path: str  # Either local path or GitHub URL

@app.post("/analyze")
def analyze_code(request: AnalysisRequest):
    path = request.repo_path
    temp_dir = None

    try:
        # Check if it's a GitHub URL
        if path.startswith("http://") or path.startswith("https://"):
            temp_dir = tempfile.mkdtemp()
            subprocess.run(["git", "clone", path, temp_dir], check=True)
            repo_path = temp_dir
        else:
            repo_path = path

        results = orchestrator.analyze_repository(repo_path)
        return results

    except subprocess.CalledProcessError:
        raise HTTPException(status_code=400, detail="Failed to clone repository.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during analysis: {str(e)}")
    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
