import chromadb
from app.config import settings

_client = chromadb.PersistentClient(path=settings.chroma_path)
_collection = _client.get_or_create_collection("chunks")


def add_chunks(ids, texts, embeddings, metadatas):
    _collection.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)


def search(query_embedding, k=10, doc_ids=None):
    where = {"doc_id": {"$in": doc_ids}} if doc_ids else None
    res = _collection.query(query_embeddings=[query_embedding], n_results=k, where=where)
    out = []
    for i in range(len(res["ids"][0])):
        out.append({
            "chunk_id": res["ids"][0][i],
            "text": res["documents"][0][i],
            "meta": res["metadatas"][0][i],
            "distance": res["distances"][0][i],
        })
    return out


def get_all(doc_ids=None):
    where = {"doc_id": {"$in": doc_ids}} if doc_ids else None
    res = _collection.get(where=where)
    return [
        {"chunk_id": res["ids"][i], "text": res["documents"][i], "meta": res["metadatas"][i]}
        for i in range(len(res["ids"]))
    ]


def delete_doc(doc_id: int):
    _collection.delete(where={"doc_id": doc_id})
