import json
from pathlib import Path
from typing import List, Optional
from app.schemas.rag import KnowledgeDocument, RAGSearchResult, RAGResponse


class RAGService:
    def __init__(self, kb_path: Optional[str] = None):
        if kb_path is None:
            kb_path = Path(__file__).parent.parent / "data" / "knowledge_base.json"
        else:
            kb_path = Path(kb_path)
        self.documents: List[KnowledgeDocument] = self._load_kb(kb_path)

    def _load_kb(self, path: Path) -> List[KnowledgeDocument]:
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        return [KnowledgeDocument(**item) for item in raw_data]

    STOPWORDS = {"in", "the", "a", "an", "and", "or", "of", "to", "for", "is", "are", "on", "at", "by", "with", "do", "does", "how", "what", "can", "i", "my", "you", "your"}

    def search(self, query: str, top_k: int = 2, threshold: float = 0.03) -> RAGResponse:
        """
        Simple keyword & overlap similarity score for deterministic baseline RAG.
        """
        cleaned_query = "".join([c if c.isalnum() or c.isspace() else " " for c in query.lower()])
        query_words = set(w for w in cleaned_query.split() if w not in self.STOPWORDS)
        scored_results: List[RAGSearchResult] = []

        for doc in self.documents:
            doc_text = f"{doc.topic} {doc.content} {doc.category}".lower()
            cleaned_doc_text = "".join([c if c.isalnum() or c.isspace() else " " for c in doc_text])
            doc_words = set(w for w in cleaned_doc_text.split() if w not in self.STOPWORDS)

            if not query_words:
                continue

            intersection = query_words.intersection(doc_words)
            union = query_words.union(doc_words)
            if not union:
                continue

            # Jaccard keyword overlap score
            score = len(intersection) / len(union)

            if score >= threshold:
                scored_results.append(
                    RAGSearchResult(document=doc, score=round(score, 4))
                )

        scored_results.sort(key=lambda x: x.score, reverse=True)
        top_results = scored_results[:top_k]

        return RAGResponse(
            query=query,
            results=top_results,
            has_match=len(top_results) > 0
        )


# Singleton instance for service usage
rag_service = RAGService()
