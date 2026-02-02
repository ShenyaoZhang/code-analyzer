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
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from orchestrator import AnalysisOrchestrator
from async_orchestrator import AsyncAnalysisOrchestrator
import os
import shutil
import tempfile
import subprocess
import logging
import re
import asyncio
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Code Analyzer API",
    description="Static analysis and ML-based code quality assessment",
    version="1.0.0"
)

# Add rate limiting handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = AnalysisOrchestrator()
async_orchestrator = AsyncAnalysisOrchestrator(max_workers=4)

class AnalysisRequest(BaseModel):
    repo_path: str = Field(..., description="Local path or GitHub URL to analyze")
    use_async: bool = Field(default=True, description="Use async analysis for better performance")
    
    @validator('repo_path')
    def validate_repo_path(cls, v):
        if not v or not v.strip():
            raise ValueError("repo_path cannot be empty")
        
        # Check if it's a valid URL or path
        url_pattern = re.compile(r'^https?://github\.com/[\w-]+/[\w.-]+/?$')
        if v.startswith('http'):
            if not url_pattern.match(v.rstrip('/')):
                raise ValueError("Invalid GitHub URL format")
        else:
            # For local paths, just check it's not obviously malicious
            if '..' in v or v.startswith('/etc') or v.startswith('/sys'):
                raise ValueError("Invalid or unsafe path")
        
        return v.strip()

@app.post("/analyze")
@limiter.limit("10/minute")  # Rate limit: 10 requests per minute
async def analyze_code(request: Request, analysis_request: AnalysisRequest):
    """
    Analyze a Python repository for code quality, security issues, and duplications.
    
    Args:
        analysis_request: Contains repo_path (local path or GitHub URL)
        
    Returns:
        dict: Analysis results with issues, quality scores, and recommendations
    """
    path = analysis_request.repo_path
    temp_dir = None
    
    logger.info(f"Received analysis request for: {path}")

    try:
        # Check if it's a GitHub URL
        if path.startswith("http://") or path.startswith("https://"):
            logger.info(f"Cloning repository from: {path}")
            temp_dir = tempfile.mkdtemp(prefix="code_analyzer_")
            
            try:
                result = subprocess.run(
                    ["git", "clone", "--depth", "1", path, temp_dir],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=300,  # 5 minute timeout
                    check=True
                )
                logger.info(f"Successfully cloned repository to {temp_dir}")
            except subprocess.TimeoutExpired:
                raise HTTPException(
                    status_code=408,
                    detail="Repository clone timeout (>5 minutes)"
                )
            
            repo_path = temp_dir
        else:
            # Validate local path exists
            if not os.path.exists(path):
                raise HTTPException(
                    status_code=400,
                    detail=f"Local path does not exist: {path}"
                )
            if not os.path.isdir(path):
                raise HTTPException(
                    status_code=400,
                    detail=f"Path is not a directory: {path}"
                )
            repo_path = path
            logger.info(f"Analyzing local repository: {repo_path}")

        # Perform analysis (async or sync based on request)
        if analysis_request.use_async:
            logger.info(f"Using async analysis mode for {repo_path}")
            results = await async_orchestrator.analyze_repository(repo_path)
        else:
            logger.info(f"Using sync analysis mode for {repo_path}")
            # Run sync analysis in executor to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                orchestrator.analyze_repository,
                repo_path
            )
        
        logger.info(f"Analysis complete for {path}: {len(results)} files analyzed")
        return {
            "status": "success",
            "analyzed_files": len(results),
            "results": results
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"Git clone failed: {e.stderr if hasattr(e, 'stderr') else str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Failed to clone repository. Ensure URL is valid and repository is accessible."
        )
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during analysis: {str(e)}"
        )
    finally:
        # Cleanup temp directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.debug(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp directory {temp_dir}: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "code-analyzer"}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Code Analyzer API",
        "version": "1.0.0",
        "features": [
            "Static analysis (pylint, flake8, bandit)",
            "ML-based quality prediction (CodeBERT)",
            "Code duplication detection",
            "Async concurrent analysis for performance",
            "GitHub repository support"
        ],
        "endpoints": {
            "/analyze": "POST - Analyze a repository (supports async mode)",
            "/health": "GET - Health check",
            "/docs": "GET - API documentation"
        }
    }
