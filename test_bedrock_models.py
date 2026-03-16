import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

try:
    client = boto3.client('bedrock', region_name='us-east-1')
    
    # Let's bypass the authorization manually
    bearer = os.getenv("AWS_BEARER_TOKEN_BEDROCK")
    if bearer:
        client.meta.events.register(
            "before-sign.bedrock.*", 
            lambda request, **kwargs: request.headers.add_header("Authorization", "Bearer " + bearer)
        )
    
    res = client.list_foundation_models()
    models = [m['modelId'] for m in res['modelSummaries'] if 'nova' in m['modelId'].lower()]
    print("NOVA MODELS:", json.dumps(models, indent=2))
except Exception as e:
    print("Error:", e)
