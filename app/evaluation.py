def retrieval_metrics(expected_ids,hits,k=5):
    got=[h.doc_id for h in hits[:k]]; rel=set(expected_ids)
    recall=len(rel & set(got))/max(1,len(rel)); precision=len(rel & set(got))/max(1,len(got))
    rr=next((1/(i+1) for i,x in enumerate(got) if x in rel),0)
    return {"recall_at_k":recall,"precision_at_k":precision,"mrr":rr}
def generation_metrics(answer,hits):
    evidence=" ".join(h.text.lower() for h in hits); toks=[x.strip('.,:;') for x in answer.lower().split() if len(x)>4]
    support=sum(t in evidence for t in toks)/max(1,len(toks))
    return {"grounded_token_proxy":round(support,3),"citation_count":len(hits),"abstention":answer.startswith("I don't")}
