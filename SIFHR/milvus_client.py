from pymilvus import MilvusClient, DataType
from config import Config


def get_milvus_client():
    return MilvusClient(
        uri=f"http://{Config.MILVUS_HOST}:{Config.MILVUS_PORT}"
    )


def create_collection(collection_name, dim=1024):
    client = get_milvus_client()
    
    if client.has_collection(collection_name):
        client.drop_collection(collection_name)
    
    schema = client.create_schema(auto_id=True, enable_dynamic_field=True)
    
    schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True)
    schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=dim)
    schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=65535)
    schema.add_field(field_name="source", datatype=DataType.VARCHAR, max_length=1024)
    schema.add_field(field_name="minio_path", datatype=DataType.VARCHAR, max_length=2048)
    schema.add_field(field_name="bucket", datatype=DataType.VARCHAR, max_length=256)
    schema.add_field(field_name="endpoint", datatype=DataType.VARCHAR, max_length=256)
    
    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="vector",
        index_type="IVF_FLAT",
        metric_type="COSINE",
        params={"nlist": 1024}
    )
    
    client.create_collection(
        collection_name=collection_name,
        schema=schema,
        index_params=index_params
    )
    
    print(f"Collection {collection_name} créée avec succès.")


def insert_embeddings(collection_name, ids, texts, embeddings, metadatas):
    client = get_milvus_client()
    
    # Insérer par petits lots pour éviter la limite de taille de message
    batch_size = 1000  # Lot raisonnable pour Milvus
    total_inserted = 0
    
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i+batch_size]
        batch_embeddings = embeddings[i:i+batch_size]
        batch_metadatas = metadatas[i:i+batch_size]
        
        data = []
        for text, embedding, metadata in zip(batch_texts, batch_embeddings, batch_metadatas):
            data.append({
                "vector": embedding,
                "text": text,
                "source": metadata.get("source", ""),
                "minio_path": metadata.get("minio_path", ""),
                "bucket": metadata.get("bucket", ""),
                "endpoint": metadata.get("endpoint", "")
            })
        
        client.insert(collection_name=collection_name, data=data)
        total_inserted += len(data)
        print(f"Inséré lot {i//batch_size + 1}: {len(data)} embeddings (Total: {total_inserted}/{len(texts)})")
    
    print(f"✓ Tous les {total_inserted} embeddings insérés dans {collection_name}")


def search_similar(collection_name, query_embedding, limit=5):
    client = get_milvus_client()
    
    results = client.search(
        collection_name=collection_name,
        data=[query_embedding],
        anns_field="vector",
        search_params={"metric_type": "COSINE", "params": {"nprobe": 10}},
        output_fields=["text", "source"],
        limit=limit
    )
    
    return results[0]