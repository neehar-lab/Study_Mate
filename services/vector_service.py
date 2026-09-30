import uuid

import chromadb
import streamlit as st


@st.cache_resource
def _get_client():
    return chromadb.Client()


def build_rag_index(chunks):
    if not chunks:
        raise ValueError("No readable PDF text is available to index.")
    client = _get_client()
    collection_name = f"study_{uuid.uuid4().hex}"
    collection = client.create_collection(name=collection_name, metadata={"hnsw:space": "cosine"})
    for start in range(0, len(chunks), 500):
        batch = chunks[start : start + 500]
        collection.add(
            ids=[f"chunk_{index}" for index in range(start, start + len(batch))],
            documents=[item["text"] for item in batch],
            metadatas=[{"source": item["source"], "page": int(item["page"])} for item in batch],
        )
    return collection_name


def delete_rag_index(collection_name):
    if collection_name:
        _get_client().delete_collection(collection_name)


def retrieve_rag_chunks(collection_name, question, limit=5):
    collection = _get_client().get_collection(collection_name)
    count = collection.count()
    if not count:
        return []
    results = collection.query(
        query_texts=[question],
        n_results=min(limit, count),
        include=["documents", "metadatas", "distances"],
    )
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    return [
        {"text": document, "source": metadata["source"], "page": metadata["page"]}
        for document, metadata in zip(documents, metadatas)
    ]
