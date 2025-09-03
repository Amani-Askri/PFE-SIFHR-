from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_community.vectorstores import Milvus
from langchain_anthropic import ChatAnthropic
from config import Config


def get_multi_query_retriever(llm, retriever):
    return MultiQueryRetriever.from_llm(
        retriever=retriever,
        llm=llm
    )


def create_vectorstore_retriever(collection_name, embedding_model):
    vectorstore = Milvus(
        collection_name=collection_name,
        embedding_function=embedding_model,
        connection_args={"host": Config.MILVUS_HOST, "port": Config.MILVUS_PORT}
    )
    return vectorstore.as_retriever()


def get_llm():
    return ChatAnthropic(
        anthropic_api_key=Config.ANTHROPIC_API_KEY,
        model=Config.CLAUDE_MODEL,
        temperature=0.7,
        max_tokens=None
    )