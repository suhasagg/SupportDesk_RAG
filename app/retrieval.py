import re, math
from dataclasses import dataclass
from typing import List
@dataclass
class Hit: doc_id:str; title:str; text:str; score:float
class InMemoryHybridRetriever:
    """Dependency-light reference implementation. Replace with FAISS/Chroma adapters in production."""
    def __init__(self, docs): self.docs=docs
    def _tokens(self,s): return set(re.findall(r"[a-z0-9]+",s.lower()))
    def retrieve(self,q,k=5)->List[Hit]:
        qt=self._tokens(q); hits=[]
        for d in self.docs:
            dt=self._tokens(d.text); lexical=len(qt&dt)/max(1,len(qt))
            phrase=0.15 if any(x in d.text.lower() for x in [q.lower(), *list(qt)[:2]]) else 0
            hits.append(Hit(d.doc_id,d.title,d.text,min(1.0,lexical+phrase)))
        return sorted(hits,key=lambda x:x.score,reverse=True)[:k]
    def rerank(self,q,hits,k=3):
        # second retrieval layer; production version uses cross-encoder/reranker
        return sorted(hits,key=lambda h:(h.score, -len(h.text)),reverse=True)[:k]
