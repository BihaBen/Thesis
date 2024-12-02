import logging
import uuid
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
from transformers import AutoModelForCausalLM, AutoTokenizer
from langchain.text_splitter import RecursiveCharacterTextSplitter
import torch
from typing import Dict
from sentence_transformers import SentenceTransformer
from typing import List


client = QdrantClient(host="localhost", port=6333)

device = "cuda" if torch.cuda.is_available() else "cpu"

embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

llama_model_name = "meta-llama/Llama-3.2-1B"
tokenizer = AutoTokenizer.from_pretrained(llama_model_name)
llama_model = AutoModelForCausalLM.from_pretrained(llama_model_name)
llama_model.to(device)
llama_model.eval()


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
    vector_size = 384

    for filename, content in file_contents.items():
        try:
            splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
            chunks = splitter.split_text(content)
            logging.info(f"{len(chunks)} chunk generálva a(z) {filename} fájlhoz.")
            embeddings = generate_embeddings(chunks)

            all_chunks.extend([
                {"chunk": chunk, "text_title": filename} for chunk in chunks
            ])
            all_embeddings.extend(embeddings)

        except Exception as e:
            logging.error(f"Hiba történt a(z) {filename} fájl feldolgozása során: {str(e)}")

    initialize_qdrant(collection_name, vector_size)

    upsert_embeddings(collection_name, all_embeddings, all_chunks)

    return {"status": "success", "chunks": len(all_chunks)}



def generate_embeddings(text_chunks: List[str]) -> List[list]:
    if not text_chunks:
        return []
    
    embeddings = embedding_model.encode(text_chunks, show_progress_bar=True, batch_size=32)

    embeddings_list = [embedding.tolist() for embedding in embeddings]

    return embeddings_list

def upsert_embeddings(collection_name: str, embeddings: list, chunks: list):
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
# Search for relevant data
############################################################################
def search_relevant(query: str, collection_name: str, top_k: int = 3) -> List[Dict]:
    try:
        query_embedding = embedding_model.encode(query, show_progress_bar=False).tolist()
        search_results = client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=top_k
        )

        relevant_docs = []
        for result in search_results:
            payload = result.payload
            relevant_docs.append({
                "id": result.id,
                "content": payload.get("chunk", "N/A"),
                "title": payload.get("text_title", "N/A"),
                "score": result.score
            })

        return relevant_docs

    except Exception as e:
        logging.error(f"Hiba történt a releváns dokumentumok keresése során: {str(e)}")
        return []
    
def save_text_to_qdrant(text: str, who: str, collection_name: str):
    try:
        # Generálj embeddinget a szövegből
        embedding = embedding_model.encode([text], show_progress_bar=False)[0].tolist()
        
        # Gyűjtemény inicializálása, ha még nincs
        try:
            client.get_collection(collection_name)
        except Exception:
            vector_size = 384  # Ez az embedding modell kimenetének mérete
            initialize_qdrant(collection_name, vector_size)

        # Dokumentum készítése
        document_payload = {
            "chunk": text,  # A tényleges szöveg
            "text_title": who  # A dokumentum típusa (bot vagy user)
        }

        # Pont létrehozása és feltöltés
        point = {
            "id": str(uuid.uuid4()),
            "vector": embedding,
            "payload": document_payload
        }

        client.upsert(
            collection_name=collection_name,
            points=[point]
        )

        logging.info(f"Dokumentum elmentve: {who}, {collection_name}")
        return {"status": "success", "id": point["id"]}

    except Exception as e:
        logging.error(f"Hiba történt a dokumentum mentése során: {str(e)}")
        return {"status": "error", "message": str(e)}
