# Code Analyzer

A comprehensive Python code analysis tool that combines static analysis, ML-based quality prediction, and code duplication detection. Powered by CodeBERT via AWS SageMaker for intelligent quality assessment.

## Features

- **Static Analysis**: Integrated pylint, flake8, and bandit for code quality and security
- **ML Quality Prediction**: CodeBERT-based semantic analysis via AWS SageMaker
- **Code Duplication Detection**: Identify duplicate code blocks across files
- **Security Scanning**: Detect hardcoded passwords, unsafe eval usage, and system calls
- **Maintainability Metrics**: Calculate complexity and maintainability indices
- **Smart Recommendations**: Context-aware suggestions for code improvements
- **REST API**: FastAPI endpoint with rate limiting and validation
- **GitHub Integration**: Analyze repositories directly from GitHub URLs

## Architecture

```
code-analyzer/
├── analyzer.py              # Core analysis engine
├── orchestrator.py          # Repository-level orchestration
├── analysis_api.py          # FastAPI REST API
├── ml_predictor.py          # ML quality prediction
├── code_metrics.py          # Metrics calculation
├── duplication_detector.py  # Duplicate code detection
├── recommendation_engine.py # Smart recommendations
├── deploy_codebert.py       # SageMaker deployment script
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container configuration
└── sample_repo/            # Test repository
```

## Prerequisites

- Python 3.9+
- AWS account with SageMaker access (for ML features)
- Git (for GitHub repository cloning)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/ShenyaoZhang/code-analyzer.git
cd code-analyzer
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the environment template and update with your credentials:

```bash
cp env-template.txt .env
```

Edit `.env` with your values:

```bash
SAGEMAKER_ENDPOINT_NAME=your-endpoint-name
SAGEMAKER_ROLE_ARN=arn:aws:iam::YOUR_ACCOUNT:role/SageMakerExecutionRole
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
LOG_LEVEL=INFO
```

### 4. Deploy CodeBERT to SageMaker (First-time setup)

```bash
python deploy_codebert.py
```

This will deploy the CodeBERT model to SageMaker and output an endpoint name. Update your `.env` file with this endpoint name.

## Usage

### Command Line

#### Analyze a single file

```bash
python analyzer.py path/to/file.py
```

#### Analyze an entire repository

```bash
python orchestrator.py
```

By default, this analyzes the `sample_repo` directory. Edit `orchestrator.py` to change the target path.

### REST API

#### Start the API server

```bash
uvicorn analysis_api:app --host 0.0.0.0 --port 8000
```

#### API Endpoints

**POST /analyze** - Analyze a repository

```bash
# Analyze local repository
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/path/to/repo"}'

# Analyze GitHub repository
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "https://github.com/username/repo"}'
```

**GET /health** - Health check

```bash
curl http://localhost:8000/health
```

**GET /docs** - Interactive API documentation

Open `http://localhost:8000/docs` in your browser for Swagger UI documentation.

### Docker

#### Build the image

```bash
docker build -t code-analyzer .
```

#### Run the container

```bash
docker run -p 8000:8000 \
  -e SAGEMAKER_ENDPOINT_NAME=your-endpoint \
  -e AWS_ACCESS_KEY_ID=your-key \
  -e AWS_SECRET_ACCESS_KEY=your-secret \
  -e AWS_DEFAULT_REGION=us-east-1 \
  code-analyzer
```

## Output Format

The analyzer returns comprehensive results for each file:

```json
{
  "status": "success",
  "analyzed_files": 3,
  "results": {
    "file1.py": {
      "analysis_id": "uuid",
      "file_path": "file1.py",
      "quality_score": 0.85,
      "maintainability": 92.5,
      "issues": [
        {
          "type": "style",
          "severity": "warning",
          "line": 10,
          "column": 80,
          "message": "Line too long (85 > 79 characters)",
          "tool": "flake8",
          "rule": "E501"
        }
      ],
      "recommendations": [
        {
          "line": 10,
          "tool": "flake8",
          "rule": "E501",
          "suggestion": "Break long lines into shorter ones.",
          "message": "Line too long (85 > 79 characters)"
        }
      ],
      "duplicates": [
        {
          "source": "file2.py",
          "line_range": [5, 8],
          "snippet": "duplicate code..."
        }
      ]
    }
  }
}
```

## Metrics Explained

### Quality Score (0.0 - 1.0)

The ML-based quality score uses CodeBERT embeddings to assess code semantic richness. Higher scores indicate more complex, feature-rich code. The score is calculated as the average magnitude of the first 100 dimensions of the embedding vector.

- **0.0 - 0.3**: Simple code, minimal features
- **0.3 - 0.6**: Moderate complexity
- **0.6 - 1.0**: High complexity, feature-rich

### Maintainability Index (0 - 100)

Calculated using cyclomatic complexity and lines of code:

```
score = 100 - (complexity × 2 + LOC × 0.5)
```

- **85 - 100**: Excellent maintainability
- **65 - 84**: Good maintainability
- **50 - 64**: Moderate maintainability
- **< 50**: Difficult to maintain

## Configuration

### Rate Limiting

The API includes built-in rate limiting (10 requests/minute per IP). Modify in `analysis_api.py`:

```python
@limiter.limit("10/minute")  # Adjust as needed
```

### Duplication Detection

Change minimum lines for duplication detection in `orchestrator.py`:

```python
self.dup_checker = DuplicationDetector(min_lines=3)  # Default: 3
```

### Logging

Set log level via environment variable:

```bash
export LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Code Style

```bash
# Check code style
flake8 .
pylint *.py

# Security scan
bandit -r .
```

## Troubleshooting

### SageMaker Endpoint Errors

**Problem**: `EndpointNotFound` or connection errors

**Solution**: 
1. Verify endpoint exists: `aws sagemaker list-endpoints`
2. Check endpoint name in `.env` matches deployed endpoint
3. Ensure AWS credentials have SageMaker access

### Tool Not Found Errors

**Problem**: `flake8/pylint/bandit not found`

**Solution**: Reinstall dependencies
```bash
pip install -r requirements.txt --force-reinstall
```

### Unicode Decode Errors

The analyzer automatically handles encoding issues, falling back to latin-1 encoding when UTF-8 fails.

### Docker Networking

If running in Docker and analyzing local files, mount the directory:

```bash
docker run -v /path/to/code:/data code-analyzer
```

## Security Considerations

- Never commit `.env` file with credentials
- Use IAM roles in production instead of access keys
- Configure CORS appropriately in `analysis_api.py`
- Validate all input paths to prevent directory traversal
- Review rate limits based on your infrastructure

## Cost Optimization

SageMaker endpoints incur hourly charges. To reduce costs:

1. Use smaller instance types: `ml.t2.medium` instead of `ml.m5.large`
2. Delete endpoints when not in use:
   ```bash
   aws sagemaker delete-endpoint --endpoint-name your-endpoint
   ```
3. Use SageMaker Serverless Inference for sporadic usage

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: [Your repo issues page]
- Email: [Your email]

## Roadmap

- [ ] Support for JavaScript/TypeScript
- [ ] Custom rule configuration
- [ ] HTML report generation
- [ ] Integration with CI/CD pipelines
- [ ] Real-time file watching mode
- [ ] Performance profiling
- [ ] Code complexity visualization

