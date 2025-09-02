from chunking_embedding import get_embedding_model, chunk_document
from minio_client import list_documents, read_document
from milvus_client import create_collection, insert_embeddings
from multi_query_retriever import get_multi_query_retriever, create_vectorstore_retriever, get_llm
import time


def main():
    # Initialisation des modèles
    embedding_model = get_embedding_model()
    llm = get_llm()
    
    # Création de la collection Milvus
    collection_name = "data_sifhr"
    create_collection(collection_name, dim=1024)
    
    # Récupération et traitement des documents depuis MinIO
    documents = list_documents()
    print(f"Documents trouvés: {documents}")
    
    if not documents:
        print("Aucun document trouvé dans MinIO")
        return None
        
    all_chunks = []
    all_metadatas = []
    
    for doc_name in documents:
        try:
            content = read_document(doc_name).read().decode("utf-8")
        except UnicodeDecodeError:
            try:
                content = read_document(doc_name).read().decode("latin-1")
            except UnicodeDecodeError:
                content = read_document(doc_name).read().decode("cp1252")
        
        chunks = chunk_document(content)
        print(f"Document {doc_name}: {len(chunks)} chunks créés")
        
        # Stocker le chemin complet MinIO
        from config import Config
        minio_path = f"minio://{Config.MINIO_ENDPOINT}/{Config.MINIO_BUCKET_NAME}/{doc_name}"
        
        all_chunks.extend(chunks)
        all_metadatas.extend([{
            "source": doc_name,
            "minio_path": minio_path,
            "bucket": Config.MINIO_BUCKET_NAME,
            "endpoint": Config.MINIO_ENDPOINT
        }] * len(chunks))
    
    # Génération des embeddings et insertion dans Milvus par lots
    if all_chunks:
        print(f"Génération des embeddings pour {len(all_chunks)} chunks...")
        
        # Traiter par lots maximaux pour être le plus efficace possible
        batch_size = 100  # Lot très grand pour maximiser la vitesse
        all_embeddings = []
        total_batches = (len(all_chunks) + batch_size - 1) // batch_size
        start_time = time.time()
        
        for i in range(0, len(all_chunks), batch_size):
            batch_chunks = all_chunks[i:i+batch_size]
            current_batch = i//batch_size + 1
            
            # Calculer le temps estimé restant
            if current_batch > 1:
                elapsed_time = time.time() - start_time
                avg_time_per_batch = elapsed_time / (current_batch - 1)
                remaining_batches = total_batches - current_batch + 1
                estimated_remaining = avg_time_per_batch * remaining_batches
                print(f"Lot {current_batch}/{total_batches} ({len(batch_chunks)} chunks) - Temps restant estimé: {estimated_remaining:.1f}s")
            else:
                print(f"Lot {current_batch}/{total_batches} ({len(batch_chunks)} chunks)")
            
            try:
                batch_start = time.time()
                batch_embeddings = embedding_model.embed_documents(batch_chunks)
                batch_time = time.time() - batch_start
                all_embeddings.extend(batch_embeddings)
                print(f"  ✓ Lot traité en {batch_time:.1f}s")
                
                # Pas de pause pour vitesse maximale (commentez si vous avez des erreurs 429)
                # if i + batch_size < len(all_chunks):
                #     time.sleep(0.5)
                    
            except Exception as e:
                print(f"Erreur lors du traitement du lot: {e}")
                print("Pause de 10 secondes avant de continuer...")
                time.sleep(10)
                # Réessayer le lot
                try:
                    batch_embeddings = embedding_model.embed_documents(batch_chunks)
                    all_embeddings.extend(batch_embeddings)
                except Exception as e2:
                    print(f"Échec définitif du lot: {e2}")
                    return None
        
        total_time = time.time() - start_time
        print(f"\nTemps total pour les embeddings: {total_time:.1f}s")
        
        if len(all_embeddings) == len(all_chunks):
            ids = list(range(len(all_chunks)))
            insert_embeddings(collection_name, ids, all_chunks, all_embeddings, all_metadatas)
            print("Embeddings insérés avec succès!")
        else:
            print("Erreur: nombre d'embeddings ne correspond pas au nombre de chunks")
            return None
    else:
        print("Aucun chunk à traiter")
    
    # Initialisation du retriever et MultiQueryRetriever
    retriever = create_vectorstore_retriever(collection_name, embedding_model)
    multi_retriever = get_multi_query_retriever(llm, retriever)
    
    return multi_retriever


if __name__ == "__main__":
    multi_retriever = main()
    print("RAG system initialisé avec succès!")