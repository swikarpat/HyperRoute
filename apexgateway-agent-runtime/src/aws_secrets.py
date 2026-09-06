import os
import json
from functools import lru_cache
import boto3
from botocore.exceptions import ClientError

@lru_cache(maxsize=1)
def fetch_compliance_secrets() -> dict:
    """
    Fetches compliance keys and caches them in memory.
    Avoids blocking the hot-path transaction loop with redundant network roundtrips.
    """
    endpoint_url = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")
    region_name = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

    session = boto3.session.Session()
    client = session.client(
        service_name="secretsmanager",
        region_name=region_name,
        endpoint_url=endpoint_url,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "mock-key-test"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "mock-secret-test"),
    )

    try:
        response = client.get_secret_value(SecretId="apexgateway/fsm-compliance-keys")
        return json.loads(response["SecretString"])
    except ClientError as e:
        return {"signing_key": "fallback-local-key", "simd_salt": "fallback-salt"}
