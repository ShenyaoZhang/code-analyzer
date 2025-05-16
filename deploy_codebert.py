import sagemaker
from sagemaker.huggingface import HuggingFaceModel
from sagemaker import get_execution_role, Session

# Define IAM role — adjust if you're not using SageMaker Studio
role = "arn:aws:iam::585768150727:role/SageMakerExecutionRole"

# Define model hub parameters
hub = {
    'HF_MODEL_ID': 'microsoft/codebert-base',  # CodeBERT model
    'HF_TASK': 'feature-extraction'
}

# Create SageMaker HuggingFace Model
huggingface_model = HuggingFaceModel(
    transformers_version='4.26.0',
    pytorch_version='1.13.1',
    py_version='py39',
    env=hub,
    role=role
)

# Deploy the model
predictor = huggingface_model.deploy(
    initial_instance_count=1,
    instance_type='ml.m5.large'  # Use ml.t2.medium if you want cheaper
)

print("Endpoint name:", predictor.endpoint_name)
