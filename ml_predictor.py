import sagemaker
import json
from sagemaker.predictor import Predictor

class CodeQualityPredictor:
    def __init__(self, endpoint_name):
        self.predictor = Predictor(
            endpoint_name=endpoint_name,
            serializer=sagemaker.serializers.JSONSerializer(),
            deserializer=sagemaker.deserializers.JSONDeserializer()
        )

    def predict_quality(self, code_snippet):
        payload = {
            "inputs": code_snippet
        }
        response = self.predictor.predict(payload)

        embedding = response[0]
        avg_vector = [
            sum(token[i] for token in embedding) / len(embedding)
            for i in range(len(embedding[0]))
        ]

        quality_score = sum(abs(x) for x in avg_vector[:100]) / 100
        return round(quality_score, 2)

