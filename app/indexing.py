"""Five indexing approaches: fixed chunks, recursive chunks, semantic-ish paragraphs,
parent-child chunks, and summary+detail records. Production adapters can persist to FAISS/Chroma."""
from .models import Document

def fixed(doc, size=450): return [(doc.doc_id+f":f{i}", doc.text[i:i+size]) for i in range(0,len(doc.text),size)]
def recursive(doc, size=700):
    parts=[p.strip() for p in doc.text.split("\n\n") if p.strip()]; out=[]; buf=""
    for p in parts:
        if len(buf)+len(p)>size and buf: out.append(buf); buf=""
        buf+=("\n\n" if buf else "")+p
    if buf: out.append(buf)
    return [(doc.doc_id+f":r{i}",x) for i,x in enumerate(out)]
def semantic(doc): return [(doc.doc_id+f":s{i}",p) for i,p in enumerate(doc.text.split("\n\n")) if p.strip()]
def parent_child(doc):
    parents=recursive(doc,1200); out=[]
    for pid,p in parents:
        for i in range(0,len(p),300): out.append((pid+f":c{i//300}",p[i:i+300],pid,p))
    return out
def summary_detail(doc):
    summary=" ".join(doc.text.split()[:80]); return [(doc.doc_id+":summary",summary),(doc.doc_id+":detail",doc.text)]
