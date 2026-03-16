import boto3
import json
from dotenv import load_dotenv

load_dotenv()
client = boto3.client('bedrock-runtime', region_name='us-east-1')

body = {
  "taskType": "SINGLE_EMBEDDING",
  "singleEmbeddingParams": {
    "text": {
        "value": "hello world", 
        "truncationMode": "END"
    },
    "embeddingPurpose": "GENERIC_INDEX"
  }
}

try:
    res = client.invoke_model(
        modelId="amazon.nova-2-multimodal-embeddings-v1:0",
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body)
    )
    result = json.loads(res["body"].read())
    print("SUCCESS KEYS:", result.keys())
    print("EMBEDDING KEY TYPE:", type(result.get("embedding")))
except Exception as e:
    print(e)
