from typing import Protocol
from uuid import UUID

import boto3
from botocore.exceptions import ClientError
from mypy_boto3_s3 import S3Client


class LockObjectStore(Protocol):
    def put_manifest(self, lock_id: UUID, manifest_sha256: str, payload: str) -> str: ...


class NullLockObjectStore:
    def put_manifest(self, lock_id: UUID, manifest_sha256: str, payload: str) -> str:
        del payload
        return f"memory://locks/{lock_id}/{manifest_sha256}.json"


class S3LockObjectStore:
    def __init__(
        self,
        endpoint_url: str,
        bucket: str,
        access_key_id: str,
        secret_access_key: str,
    ) -> None:
        self.bucket = bucket
        self.client: S3Client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name="us-east-1",
        )
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError as error:
            code = str(error.response.get("Error", {}).get("Code", ""))
            if code not in {"404", "NoSuchBucket", "NotFound"}:
                raise
            self.client.create_bucket(Bucket=self.bucket)

    def put_manifest(self, lock_id: UUID, manifest_sha256: str, payload: str) -> str:
        key = f"locks/{lock_id}/{manifest_sha256}.json"
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=payload.encode(),
            ContentType="application/json",
            Metadata={"sha256": manifest_sha256, "immutable": "true"},
        )
        return f"s3://{self.bucket}/{key}"
