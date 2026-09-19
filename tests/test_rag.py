from app.models import Document,TicketQuery
from app.retrieval import InMemoryHybridRetriever
from app.memory import ConversationMemory
from app.agent import SupportAgent
from app.evaluation import retrieval_metrics
def test_retrieval():
 d=[Document(doc_id="vpn",title="vpn",text="VPN error 809 firewall UDP 500 4500")]; r=InMemoryHybridRetriever(d); h=r.retrieve("VPN error 809",1); assert h[0].doc_id=="vpn"; assert retrieval_metrics(["vpn"],h)["recall_at_k"]==1
def test_agent_grounded():
 d=[Document(doc_id="dns",title="dns",text="DNS failure flush cache resolver lookup")]; a=SupportAgent(InMemoryHybridRetriever(d),ConversationMemory()); ans,c,ab,h,t=a.run(TicketQuery(ticket_id="1",question="DNS failure resolver")); assert not ab and h
