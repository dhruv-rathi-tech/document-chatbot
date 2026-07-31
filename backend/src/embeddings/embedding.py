from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from config.config import *

embedding_model = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL,
    encode_kwargs={"normalize_embeddings": True}
)


def create_vector_db(documents, chroma_dir, collection_name=COLLECTION_NAME):
    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embedding_model,
        persist_directory=str(chroma_dir),
        collection_name=collection_name,
    )

    return vector_store
