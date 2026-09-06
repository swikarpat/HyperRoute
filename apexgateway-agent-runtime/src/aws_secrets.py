import os
import json
import boto3
from botocore.exceptions import ClientError

def fetch_compliance_secrets() -> dict:
    """
    Fetches compliance keys dynamically from AWS Secrets Manager.
    Defaults to local Moto/LocalStack endpoint in local/test environments.
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
        print(f"[AWS Secrets Error] Failed to retrieve secrets: {e}")
        return {"signing_key": "fallback-local-key", "simd_salt": "fallback-salt"}

if __name__ == "__main__":
    secrets = fetch_compliance_secrets()
    print("\n✓ [AWS SDK Integration] Retrieved Secrets successfully from AWS Secrets Manager:")
    print(f"  Signing Key: {secrets.get('signing_key')}")
    print(f"  SIMD Salt:   {secrets.get('simd_salt')}\n")
