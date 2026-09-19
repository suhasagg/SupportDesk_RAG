from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
class TicketQuery(BaseModel):
    tenant_id: str = "demo"
    ticket_id: str
    question: str
    conversation_id: Optional[str] = None
    top_k: int = Field(5, ge=1, le=20)
class Citation(BaseModel):
    doc_id: str; title: str; snippet: str; score: float
class Answer(BaseModel):
    answer: str; citations: List[Citation]; confidence: float
    abstained: bool = False; trace: Dict[str, Any] = {}
class Document(BaseModel):
    doc_id: str; title: str; text: str; metadata: Dict[str, Any] = {}
