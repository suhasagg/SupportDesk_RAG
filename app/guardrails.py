def grounding_gate(hits, threshold=.20):
    return bool(hits) and hits[0].score >= threshold

def safe_context(text):
    # retrieved text is DATA, never instructions
    bad=["ignore previous instructions","system prompt","developer message"]
    low=text.lower()
    return "[potential prompt injection removed]" if any(x in low for x in bad) else text

def grounded_answer(question,hits):
    if not grounding_gate(hits): return "I don't have enough verified support documentation to answer safely.",0.0,True
    evidence=" ".join(safe_context(h.text) for h in hits)
    # offline deterministic fallback; LCEL model pipeline can replace this generator.
    words=evidence.split()[:120]
    return "Based on the retrieved support documentation: "+" ".join(words), min(.95,hits[0].score+.25),False
