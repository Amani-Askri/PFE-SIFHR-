from minio import Minio
from minio.error import S3Error
from config import Config


def get_minio_client():
    return Minio(
        Config.MINIO_ENDPOINT,
        access_key=Config.MINIO_ACCESS_KEY,
        secret_key=Config.MINIO_SECRET_KEY,
        secure=False
    )


def list_documents():
    client = get_minio_client()
    try:
        objects = client.list_objects(Config.MINIO_BUCKET_NAME)
        return [obj.object_name for obj in objects]
    except S3Error as e:
        print(f"Erreur lors du listage des documents: {e}")
        return []


def read_document(document_name):
    client = get_minio_client()
    try:
        return client.get_object(Config.MINIO_BUCKET_NAME, document_name)
    except S3Error as e:
        print(f"Erreur lors de la lecture du document {document_name}: {e}")
        return None