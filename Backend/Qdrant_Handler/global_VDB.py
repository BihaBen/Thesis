import logging
import os
import uuid
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
from langchain.embeddings import OpenAIEmbeddings
from typing import Dict


client = QdrantClient(host="localhost", port=6333)

embedding_model = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))

def initialize_qdrant(collection_name: str, vector_size: int):

    try:
        client.get_collection(collection_name)
        client.delete_collection(collection_name)
        logging.info(f"Létező gyűjtemény törölve: {collection_name}")
    except Exception:
        logging.info(f"Új gyűjtemény készül: {collection_name}")

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )
    logging.info(f"Qdrant gyűjtemény létrehozva: {collection_name}")

def process_document(file_contents: Dict[str, str], collection_name: str) -> Dict:

    all_chunks = []
    all_embeddings = []
    vector_size = None

    for filename, content in file_contents.items():
        try:
            chunks = dynamic_semantic_chunk_splitter(content)
            logging.info(f"{len(chunks)} chunk generálva a(z) {filename} fájlhoz.")

            embeddings = generate_embeddings(chunks)

            all_chunks.extend([
                {"chunk": chunk, "text_title": filename} for chunk in chunks
            ])
            all_embeddings.extend(embeddings)

            if vector_size is None:
                vector_size = len(embeddings[0])

        except Exception as e:
            logging.error(f"Hiba történt a(z) {filename} fájl feldolgozása során: {str(e)}")

    initialize_qdrant(collection_name, vector_size)

    upsert_embeddings(collection_name, all_embeddings, all_chunks)

    return {"status": "success", "chunks": len(all_chunks)}

def dynamic_semantic_chunk_splitter(text: str, max_chunk_size: int = 1000) -> list:
    paragraphs = text.split("\n")
    chunks = []
    current_chunk = []
    current_chunk_size = 0

    for paragraph in paragraphs:
        if current_chunk_size + len(paragraph) > max_chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_chunk_size = 0

        current_chunk.append(paragraph)
        current_chunk_size += len(paragraph)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    logging.info(f"{len(chunks)} darabra bontottuk a szöveget.")
    return chunks

def generate_embeddings(text_chunks: list) -> list:
    """
    Embeddingek generálása a chunkokhoz.
    """
    logging.info(f"Embeddingek generálása {len(text_chunks)} chunkhoz.")
    embeddings = embedding_model.embed_documents(text_chunks)
    return embeddings

def upsert_embeddings(collection_name: str, embeddings: list, chunks: list):
    """
    Embeddingek feltöltése a Qdrant adatbázisba.
    """
    logging.info(f"Embeddingek feltöltése a {collection_name} gyűjteménybe.")

    points = [
        {
            "id": str(uuid.uuid4()),
            "vector": embeddings[i],
            "payload": chunks[i],
        }
        for i in range(len(embeddings))
    ]

    client.upsert(
        collection_name=collection_name,
        points=points
    )
    logging.info(f"{len(points)} embedding feltöltve a {collection_name} gyűjteménybe.")

############################################################################
# Releváns adatok keresése
############################################################################
def search_relevant(query: str, collection_name: str, top_k: int = 5) -> list:
    try:
        query_embedding = embedding_model.embed_query(query)

        search_results = client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=top_k
        )

        relevant_docs = []
        for result in search_results:
            payload = result.payload
            relevant_docs.append({
                "content": payload["chunk"],
                "title": payload.get("text_title", "N/A"),
                "score": result.score
            })

        return relevant_docs

    except Exception as e:
        logging.error(f"Hiba történt a releváns dokumentumok keresése során: {str(e)}")
        return []

def store_string_to_qdrant( text: str, who: str, collection_name: str):

    try:
        # Ellenőrizd, hogy a gyűjtemény létezik-e, ha nem, hozd létre
        vector_size = len(embedding_model.embed_query(text))  # Alapértelmezett vektorméret meghatározása
        try:
            client.get_collection(collection_name)
        except Exception:
            initialize_qdrant(collection_name, vector_size)

        # Szöveg felosztása chunkokra
        chunks = dynamic_semantic_chunk_splitter(text)

        # Embeddingek generálása a chunkokhoz
        embeddings = generate_embeddings(chunks)

        # Qdrant pontok előkészítése
        points = [
            {
                "id": str(uuid.uuid4()),  # Egyedi azonosító
                "vector": embeddings[i],  # Embedding a chunk-hoz
                "payload": {
                    "chunk": chunks[i],  # Szöveg chunk
                    "title": who,        # "user" vagy "bot"
                }
            }
            for i in range(len(chunks))
        ]
        # Pontok feltöltése a gyűjteménybe
        client.upsert(
            collection_name=collection_name,
            points=points
        )

        logging.info(f"{len(points)} pont sikeresen feltöltve a {collection_name} gyűjteménybe.")

    except Exception as e:
        logging.error(f"Hiba történt a dokumentum tárolása során: {str(e)}")
