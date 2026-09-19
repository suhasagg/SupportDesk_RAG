from .guardrails import grounded_answer
class SupportAgent:
    """Agentic RAG: classify -> retrieve -> rerank -> answer/abstain -> optional next diagnostic step."""
    def __init__(self,retriever,memory): self.r=retriever; self.m=memory
    def run(self,q,k=5):
        hits=self.r.rerank(q.question,self.r.retrieve(q.question,k),min(3,k))
        ans,conf,abstain=grounded_answer(q.question,hits)
        cid=q.conversation_id or q.ticket_id
        self.m.append(cid,"user",q.question); self.m.append(cid,"assistant",ans)
        return ans,conf,abstain,hits,{"plan":["retrieve","rerank","grounding_gate","generate_or_abstain"],"memory_turns":len(self.m.recent(cid))}
