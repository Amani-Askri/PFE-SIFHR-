from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_mistralai import MistralAIEmbeddings
from config import Config


def get_embedding_model():
    return MistralAIEmbeddings(
        model=Config.EMBEDDING_MODEL,
        mistral_api_key=Config.MISTRAL_API_KEY
    )


def chunk_document(content, chunk_size=512, chunk_overlap=50):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_text(content)
    return chunks