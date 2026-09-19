"""Illustrative FAISS/Chroma/LlamaIndex adapters used when optional dependencies are installed."""
def langchain_faiss(documents, embeddings):
    from langchain_community.vectorstores import FAISS
    return FAISS.from_documents(documents, embeddings)
def langchain_chroma(documents, embeddings, collection="supportdesk"):
    from langchain_chroma import Chroma
    return Chroma.from_documents(documents, embeddings, collection_name=collection)
def llamaindex_chroma(chroma_collection, embed_model=None):
    from llama_index.vector_stores.chroma import ChromaVectorStore
    from llama_index.core import VectorStoreIndex, StorageContext
    store=ChromaVectorStore(chroma_collection=chroma_collection)
    storage=StorageContext.from_defaults(vector_store=store)
    return VectorStoreIndex([],storage_context=storage,embed_model=embed_model)
