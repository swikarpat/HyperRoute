import os
import json
from functools import lru_cache
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, BotoCoreError

@lru_cache(maxsize=1)
def fetch_compliance_secrets() -> dict:
    """
    Fetches compliance keys and caches them in memory.
    Safely falls back to local keys if AWS Moto mock server is offline.
    """
    endpoint_url = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")
    region_name = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

    fast_config = Config(connect_timeout=0.5, read_timeout=0.5, retries={"max_attempts": 1})
    session = boto3.session.Session()
    client = session.client(
        service_name="secretsmanager",
        region_name=region_name,
        endpoint_url=endpoint_url,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "mock-key-test"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "mock-secret-test"),
        config=fast_config
    )

    try:
        response = client.get_secret_value(SecretId="hyperroute/fsm-compliance-keys")
        return json.loads(response["SecretString"])
    except (ClientError, BotoCoreError, Exception):
        return {"signing_key": "fallback-local-key", "simd_salt": "fallback-salt"}
