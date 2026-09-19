from fastapi import FastAPI
from .models import *
from .retrieval import InMemoryHybridRetriever
from .memory import ConversationMemory
from .agent import SupportAgent
from .evaluation import generation_metrics
DOCS=[Document(doc_id="vpn-001",title="VPN Troubleshooting",text="If corporate VPN fails, verify network connectivity, confirm credentials, check MFA, then restart the VPN client. If error 809 persists, verify firewall and UDP 500/4500 access."),Document(doc_id="mail-001",title="Email Troubleshooting",text="For mailbox sync failures, verify service status, network connectivity and account authentication. Recreate the local profile only after preserving required local data."),Document(doc_id="dns-001",title="DNS Runbook",text="For name resolution failures, run a DNS lookup, compare configured resolvers, flush local DNS cache, and escalate if authoritative records are incorrect.")]
app=FastAPI(title="SupportDesk-RAG",version="1.0.0")
r=InMemoryHybridRetriever(DOCS); mem=ConversationMemory(); agent=SupportAgent(r,mem)
@app.get("/health")
def health(): return {"status":"ok"}
@app.post("/v1/support/answer",response_model=Answer)
def answer(q:TicketQuery):
    a,c,ab,h,t=agent.run(q,q.top_k); cites=[Citation(doc_id=x.doc_id,title=x.title,snippet=x.text[:180],score=x.score) for x in h]
    t["generation_eval"]=generation_metrics(a,h)
    return Answer(answer=a,citations=cites,confidence=c,abstained=ab,trace=t)
