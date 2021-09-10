import os
import io
from pathlib import Path
from hashlib import md5

import boto3
import requests

session = boto3.session.Session()
client = session.client("s3")


class S3Client:
    __slots__ = ("bucket", "bucket_folder", "bucket_region")

    def __init__(self, bucket, bucket_folder, bucket_region):
        self.bucket = bucket
        self.bucket_folder = bucket_folder
        self.bucket_region = bucket_region

    def upload_file(self, url, relative_file_path, prefix=""):
        bucket_file_path = (
            f"{self.bucket_folder}/files/{relative_file_path}"
            f"{self._create_file_name(url, prefix)}"
        )
        url = (
            f"https://{self.bucket}.s3.{self.bucket_region}.amazonaws.com/"
            f"{bucket_file_path}"
        )

        raw_file_content = self._get_raw_file_content_from_url(url)
        blob_file = self._create_blob_file(raw_file_content)

        client.put_object(
            Bucket=self.bucket,
            Key=bucket_file_path,
            Body=blob_file,
            ACL="bucket-owner-full-control",
        )

        return {
            "url": url,
            "bucket_file_path": bucket_file_path,
            "checksum": self._generate_checksum(raw_file_content)
        }

    @staticmethod
    def _create_file_name(url, prefix=None):
        start_index = url.rfind("/") + 1
        if prefix:
            return f"{prefix}-{url[start_index:]}"
        return f"{url[start_index:]}"
    
    @staticmethod
    def _get_raw_file_content_from_url(url):
        response = requests.get(url)
        return response.content
    
    @staticmethod
    def _create_blob_file(file_content):
        blob_content = io.BytesIO(file_content)
        blob_content.seek(0)
        return blob_content
    
    @staticmethod
    def _generate_checksum(file_content):
        return md5(file_content).hexdigest()

    def download_file(self, s3_file_path):
        temporary_directory = f"{Path.cwd()}/data/tmp/"
        Path(temporary_directory).mkdir(parents=True, exist_ok=True)

        start_index = s3_file_path.rfind("/") + 1
        file_name = s3_file_path[start_index:]

        local_path = f"{temporary_directory}{file_name}"
        with open(local_path, "wb") as file_:
            client.download_fileobj(self.bucket, s3_file_path, file_)

        return local_path


class FakeS3Client(S3Client):
    def upload_file(self, url, relative_file_path, prefix=""):
        file_path = f"{self.bucket_folder}/files/{relative_file_path}"
        temp_file_name, _ = self.create_temp_file(url, file_path, prefix)
        bucket_file_path = f"{file_path}{temp_file_name}"

        url = (
            f"https://{self.bucket}.s3.{self.bucket_region}.amazonaws.com/"
            f"{bucket_file_path}"
        )
        return url, bucket_file_path

    def download_file(self, s3_file_path):
        return f"{Path.cwd()}/data/tmp/{s3_file_path}"


def get_s3_client(settings):
    use_local_file = all(
        [settings.AWS_ACCESS_KEY_ID is None, settings.AWS_SECRET_ACCESS_KEY is None]
    )
    if use_local_file or os.getenv("DJANGO_CONFIGURATION") != "Prod":
        return FakeS3Client("teste", "maria-quiteria-local", "brasil")
    else:
        return S3Client(
            settings.AWS_S3_BUCKET,
            settings.AWS_S3_BUCKET_FOLDER,
            settings.AWS_S3_REGION,
        )
