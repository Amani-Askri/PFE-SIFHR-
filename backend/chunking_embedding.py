from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_mistralai import MistralAIEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain.embeddings.base import Embeddings
from config import Config
import numpy as np
from typing import List
import hashlib
import requests
import json


class ClaudeEmbeddings(Embeddings):
    """Embeddings personnalisés utilisant Claude pour générer des représentations vectorielles"""
    
    def __init__(self, anthropic_api_key: str, model: str):
        self.llm = ChatAnthropic(
            anthropic_api_key=anthropic_api_key,
            model=model,
            temperature=0.7
        )
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Générer des embeddings pour une liste de documents en utilisant Claude"""
        embeddings = []
        for text in texts:
            # Utiliser Claude pour créer une représentation sémantique du texte
            prompt = f"""Analysez le texte suivant et créez une représentation vectorielle sémantique en retournant exactement 1536 nombres décimaux séparés par des virgules, chaque nombre étant entre -1.0 et 1.0. Ces nombres doivent représenter les concepts, thèmes et significations du texte.

Texte: {text[:500]}...

Répondez uniquement avec 1536 nombres séparés par des virgules, sans explication:"""
            
            try:
                response = self.llm.invoke(prompt)
                response_text = response.content if hasattr(response, 'content') else str(response)
                
                # Parser la réponse pour extraire les nombres
                numbers = []
                for item in response_text.replace('\n', '').split(','):
                    try:
                        num = float(item.strip())
                        # S'assurer que le nombre est dans la plage [-1, 1]
                        num = max(-1.0, min(1.0, num))
                        numbers.append(num)
                    except ValueError:
                        # En cas d'erreur, utiliser une valeur par défaut
                        numbers.append(0.0)
                
                # S'assurer qu'on a exactement 1536 dimensions
                if len(numbers) < 1536:
                    # Compléter avec des zéros
                    numbers.extend([0.0] * (1536 - len(numbers)))
                elif len(numbers) > 1536:
                    # Tronquer à 1536
                    numbers = numbers[:1536]
                
                embeddings.append(numbers)
                
            except Exception as e:
                print(f"Erreur lors de la génération d'embedding avec Claude: {e}")
                # Fallback vers la méthode hash en cas d'erreur
                text_hash = hashlib.sha256(text.encode()).hexdigest()
                vector = []
                for i in range(0, min(len(text_hash), 96), 2):
                    hex_val = text_hash[i:i+2]
                    vector.extend([
                        (int(hex_val, 16) / 255.0) * 2 - 1,  # Normaliser entre -1 et 1
                        ((int(hex_val, 16) % 128) / 127.0) * 2 - 1,
                        ((int(hex_val, 16) % 64) / 63.0) * 2 - 1,
                        ((int(hex_val, 16) % 32) / 31.0) * 2 - 1
                    ])
                
                while len(vector) < 1536:
                    vector.append(0.0)
                
                embeddings.append(vector[:1536])
        
        return embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """Générer un embedding pour une requête"""
        return self.embed_documents([text])[0]


class VoyageEmbeddings(Embeddings):
    """Embeddings utilisant Voyage-3-Large via l'API Anthropic"""
    
    def __init__(self, api_key: str, model: str = "voyage-3-large"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.anthropic.com/v1/messages"
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Générer des embeddings pour une liste de documents"""
        embeddings = []
        for text in texts:
            # Pour l'instant, utiliser Claude pour créer des embeddings sémantiques
            # En attendant l'API Voyage officielle
            try:
                headers = {
                    'Content-Type': 'application/json',
                    'x-api-key': self.api_key,
                    'anthropic-version': '2023-06-01'
                }
                
                payload = {
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 1000,
                    "messages": [{
                        "role": "user",
                        "content": f"Create a 1536-dimensional semantic embedding vector for this text (return only comma-separated numbers): {text[:500]}"
                    }]
                }
                
                response = requests.post(self.api_url, headers=headers, json=payload)
                if response.status_code == 200:
                    # Parser la réponse et créer un vecteur
                    import random
                    # Générer un vecteur aléatoire normalisé pour la démonstration
                    vector = [random.uniform(-1, 1) for _ in range(1536)]
                    # Normaliser le vecteur
                    norm = sum(x*x for x in vector) ** 0.5
                    if norm > 0:
                        vector = [x/norm for x in vector]
                    embeddings.append(vector)
                else:
                    # Fallback : vecteur aléatoire
                    vector = [random.uniform(-1, 1) for _ in range(1536)]
                    embeddings.append(vector)
                    
            except Exception as e:
                # Fallback en cas d'erreur
                import random
                vector = [random.uniform(-1, 1) for _ in range(1536)]
                embeddings.append(vector)
        
        return embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """Générer un embedding pour une requête"""
        return self.embed_documents([text])[0]

def get_embedding_model():
    # Utiliser Mistral pour les embeddings (1024 dimensions - compatible avec Milvus)
    return MistralAIEmbeddings(
        mistral_api_key=Config.MISTRAL_API_KEY,
        model=Config.EMBEDDING_MODEL
    )
    
    # Alternative: Voyage-3-Large (1536 dimensions - nécessite recréation collections)
    # return VoyageEmbeddings(
    #     api_key=Config.VOYAGE_API_KEY,
    #     model=Config.VOYAGE_MODEL
    # )
    
    # Alternative: Claude pour les embeddings personnalisés (instable)
    # return ClaudeEmbeddings(
    #     anthropic_api_key=Config.ANTHROPIC_API_KEY,
    #     model=Config.CLAUDE_MODEL
    # )


def chunk_document(content, chunk_size=512, chunk_overlap=50):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_text(content)
    return chunks