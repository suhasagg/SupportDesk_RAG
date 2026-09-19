class ConversationMemory:
    def __init__(self): self.store={}
    def append(self,cid,role,text): self.store.setdefault(cid,[]).append({"role":role,"text":text})
    def recent(self,cid,n=8): return self.store.get(cid,[])[-n:]
