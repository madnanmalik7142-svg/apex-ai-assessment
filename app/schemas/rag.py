from typing import List, Optional
from pydantic import BaseModel, Field


class KnowledgeDocument(BaseModel):
    id: str
    category: str = Field(..., description="Document category e.g., preparation, insurance, general")
    topic: str = Field(..., description="Short descriptive topic header")
    content: str = Field(..., description="Factual snippet text")


class RAGSearchResult(BaseModel):
    document: KnowledgeDocument
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance similarity score")


class RAGResponse(BaseModel):
    query: str
    results: List[RAGSearchResult] = Field(default_factory=list)
    has_match: bool = Field(...)

    @property
    def context_text(self) -> str:
        """Helper property to format retrieved documents for prompt context."""
        if not self.results or not self.has_match:
            return "No relevant official knowledge base guidelines found for this query."

        context_blocks = []
        for idx, res in enumerate(self.results, 1):
            doc = res.document
            block = f"--- Document {idx}: {doc.topic} ({doc.category}) ---\n{doc.content}"
            context_blocks.append(block)

        return "\n\n".join(context_blocks)
