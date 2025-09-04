from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_milvus import Milvus
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from config import Config


def get_multi_query_retriever(llm, retriever):
    # Version originale complète avec multi-query
    return MultiQueryRetriever.from_llm(
        retriever=retriever,
        llm=llm
    )


def create_vectorstore_retriever(collection_name, embedding_model):
    try:
        vectorstore = Milvus(
            collection_name=collection_name,
            embedding_function=embedding_model,
            connection_args={"host": Config.MILVUS_HOST, "port": Config.MILVUS_PORT}
        )
        return vectorstore.as_retriever()
    except Exception as e:
        print(f"Warning: Could not connect to Milvus: {e}")
        # Créer un retriever factice pour les tests
        from langchain_core.retrievers import BaseRetriever
        from langchain_core.documents import Document
        from typing import List
        
        class MockRetriever(BaseRetriever):
            def _get_relevant_documents(self, query: str, **kwargs) -> List[Document]:
                return [Document(page_content="Document de test", metadata={"source": "mock"})]
        
        return MockRetriever()


def get_llm():
    # Essayer Claude d'abord, puis fallback vers Google Gemini
    try:
        print("Tentative d'utilisation de Claude Anthropic...")
        llm = ChatAnthropic(
            anthropic_api_key=Config.ANTHROPIC_API_KEY,
            model=Config.CLAUDE_MODEL,
            temperature=0.6,
            max_tokens=10000
        )
        # Test rapide pour vérifier si la clé fonctionne
        test_response = llm.invoke("Test")
        print("[OK] Claude Anthropic connecte avec succes!")
        return llm
    except Exception as e:
        print(f"[ERREUR] Claude echoue: {e}")
        print("[INFO] Passage a Google Gemini...")
        
        # Fallback vers Google Gemini
        return ChatGoogleGenerativeAI(
            google_api_key=Config.GOOGLE_API_KEY,
            model=Config.GEMINI_MODEL,
            temperature=0.6,
            max_output_tokens=10000
        )