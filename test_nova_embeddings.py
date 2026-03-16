import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()
client = boto3.client('bedrock-runtime', region_name='us-east-1')

# Test current payload
try:
    body = {
        "inputText": "hello world",
        "embeddingConfig": {
            "outputEmbeddingLength": 1024
        }
    }
    response = client.invoke_model(
        modelId="amazon.nova-2-multimodal-embeddings-v1:0",
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body)
    )
    result = json.loads(response["body"].read())
    print("SUCCESS current payload:", len(result.get("embedding", [])))
except Exception as e:
    print("ERROR current payload:", e)

# test messages payload
try:
    body = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "text": "hello"
                    }
                ]
            }
        ]
    }
    response = client.invoke_model(
        modelId="amazon.nova-2-multimodal-embeddings-v1:0",
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body)
    )
    result = json.loads(response["body"].read())
    print("SUCCESS messages payload:", len(result.get("embedding", [])))
except Exception as e:
    print("ERROR messages payload:", e)
