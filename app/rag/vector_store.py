import json
import math
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

class TravelVectorStore:
    """
    Vector Store for indexing and retrieving unstructured hotel content:
    - Room descriptions and view perspectives
    - Cancellation policy fine print and terms
    
    Supports ChromaDB if installed, with a built-in semantic cosine-similarity 
    retriever as a zero-dependency fallback.
    """
    def __init__(self, data_path: Optional[str] = None):
        if not data_path:
            base_dir = Path(__file__).resolve().parent.parent.parent
            data_path = str(base_dir / "mcp_server" / "data" / "raw_hotels.json")
            
        self.data_path = data_path
        self.documents: List[Dict[str, Any]] = []
        self.chroma_client = None
        self.collection = None
        
        self._load_documents()
        self._init_backend()

    def _load_documents(self):
        with open(self.data_path, "r", encoding="utf-8") as f:
            hotels = json.load(f)
            
        for hotel in hotels:
            # 1. Room view chunk
            self.documents.append({
                "doc_id": f"{hotel['hotel_id']}_view",
                "hotel_id": hotel["hotel_id"],
                "hotel_name": hotel["name"],
                "doc_type": "room_view",
                "text": f"{hotel['room_type']}. {hotel['room_description']}",
                "metadata": {
                    "area": hotel["area"],
                    "price_per_night": hotel["price_per_night"]
                }
            })
            
            # 2. Cancellation terms chunk
            self.documents.append({
                "doc_id": f"{hotel['hotel_id']}_cancellation",
                "hotel_id": hotel["hotel_id"],
                "hotel_name": hotel["name"],
                "doc_type": "cancellation_policy",
                "text": hotel["cancellation_terms"],
                "metadata": {
                    "area": hotel["area"]
                }
            })

    def _init_backend(self):
        """Try loading ChromaDB; if not installed or unavailable, fallback to semantic index."""
        try:
            import chromadb
            self.chroma_client = chromadb.Client()
            self.collection = self.chroma_client.get_or_create_collection(name="hotel_knowledge_base")
            
            ids = [doc["doc_id"] for doc in self.documents]
            texts = [doc["text"] for doc in self.documents]
            metadatas = [
                {
                    "hotel_id": doc["hotel_id"],
                    "hotel_name": doc["hotel_name"],
                    "doc_type": doc["doc_type"]
                }
                for doc in self.documents
            ]
            self.collection.add(ids=ids, documents=texts, metadatas=metadatas)
        except Exception:
            # Fallback to internal semantic cosine retriever
            self.chroma_client = None
            self.collection = None

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\w+", text.lower())

    def _compute_vector(self, text: str) -> Dict[str, float]:
        tokens = self._tokenize(text)
        freq: Dict[str, float] = {}
        for t in tokens:
            freq[t] = freq.get(t, 0.0) + 1.0
        
        # Boost key semantic domain terms
        semantic_boosts = {
            "beach": 2.5, "sea": 2.5, "ocean": 2.5, "waves": 2.0, "beachfront": 3.0,
            "panoramic": 1.5, "balcony": 1.5, "unobstructed": 2.0, "view": 1.2,
            "free": 2.5, "cancellation": 2.5, "refund": 2.5, "guaranteed": 2.0,
            "penalty": 2.0, "non-refundable": 3.0, "charged": 2.0
        }
        for term, boost in semantic_boosts.items():
            if term in freq:
                freq[term] *= boost

        # Normalize
        norm = math.sqrt(sum(v * v for v in freq.values()))
        if norm > 0:
            for k in freq:
                freq[k] /= norm
        return freq

    def _cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        dot = 0.0
        for k, v in vec1.items():
            if k in vec2:
                dot += v * vec2[k]
        return dot

    def query_semantic(self, query: str, doc_type: str, hotel_id: Optional[str] = None, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves most relevant chunks matching query and doc_type ('room_view' or 'cancellation_policy').
        """
        if self.collection:
            where_filter: Dict[str, Any] = {"doc_type": doc_type}
            if hotel_id:
                where_filter["hotel_id"] = hotel_id
                
            results = self.collection.query(
                query_texts=[query],
                where=where_filter,
                n_results=top_k
            )
            retrieved = []
            if results and results.get("documents"):
                docs = results["documents"][0]
                metas = results["metadatas"][0]
                distances = results["distances"][0] if "distances" in results and results["distances"] else [0.2] * len(docs)
                for d, m, dist in zip(docs, metas, distances):
                    score = max(0.0, 1.0 - dist)
                    retrieved.append({
                        "hotel_id": m["hotel_id"],
                        "hotel_name": m["hotel_name"],
                        "doc_type": m["doc_type"],
                        "text": d,
                        "score": round(score, 3)
                    })
            return retrieved

        # Fallback dense/sparse similarity
        query_vec = self._compute_vector(query)
        scored_docs = []
        for doc in self.documents:
            if doc["doc_type"] != doc_type:
                continue
            if hotel_id and doc["hotel_id"] != hotel_id:
                continue
            doc_vec = self._compute_vector(doc["text"])
            score = self._cosine_similarity(query_vec, doc_vec)
            scored_docs.append({
                "hotel_id": doc["hotel_id"],
                "hotel_name": doc["hotel_name"],
                "doc_type": doc["doc_type"],
                "text": doc["text"],
                "score": round(score, 3)
            })
            
        scored_docs.sort(key=lambda x: x["score"], reverse=True)
        return scored_docs[:top_k]

