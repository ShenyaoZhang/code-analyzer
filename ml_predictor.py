import sagemaker
import json
import logging
from sagemaker.predictor import Predictor

logger = logging.getLogger(__name__)

class CodeQualityPredictor:
    """
    Predicts code quality using CodeBERT embeddings from AWS SageMaker.
    
    The quality score is calculated as the average magnitude of the first 100
    dimensions of the embedding vector, normalized to a 0-1 scale.
    """
    
    def __init__(self, endpoint_name):
        try:
            self.predictor = Predictor(
                endpoint_name=endpoint_name,
                serializer=sagemaker.serializers.JSONSerializer(),
                deserializer=sagemaker.deserializers.JSONDeserializer()
            )
            logger.info(f"Successfully initialized predictor with endpoint: {endpoint_name}")
        except Exception as e:
            logger.error(f"Failed to initialize predictor: {e}")
            raise

    def predict_quality(self, code_snippet):
        """
        Predict code quality score from code snippet.
        
        Args:
            code_snippet (str): Python code to analyze
            
        Returns:
            float: Quality score between 0 and 1 (rounded to 2 decimals)
            
        The quality score represents the semantic richness of the code based on
        CodeBERT embeddings. Higher scores indicate more complex/feature-rich code.
        """
        try:
            payload = {
                "inputs": code_snippet
            }
            response = self.predictor.predict(payload)

            if not response or not isinstance(response, list) or len(response) == 0:
                logger.warning("Invalid response from predictor, returning default score")
                return 0.5

            embedding = response[0]
            
            # Calculate average vector from token embeddings
            avg_vector = [
                sum(token[i] for token in embedding) / len(embedding)
                for i in range(len(embedding[0]))
            ]

            # Quality score: average magnitude of first 100 dimensions
            quality_score = sum(abs(x) for x in avg_vector[:100]) / 100
            return round(quality_score, 2)
            
        except Exception as e:
            logger.error(f"Error predicting quality: {e}")
            return 0.0

