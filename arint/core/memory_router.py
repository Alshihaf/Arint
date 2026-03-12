# core/memory_router.py
import re
from collections import defaultdict
from tools.seafil import Seafil
from tools.cleaners import find_patterns

class BrainCore:
    def __init__(self):
        self.snippets = []
        self.patterns = []
        self.insights = []  
        self.seafil = Seafil()
    
    def add_snippet(self, text, source="unknown"):
        processed = self.seafil.process(text, source=source, auto_save=True)
        if processed:
            short = processed.content[:200] + "..." if len(processed.content) > 200 else processed.content
            self.snippets.append(f"[{processed.type}] {short}")
            return True
        return False
    
    def consolidate(self):
        full_text = " ".join(self.snippets)
        self.patterns = find_patterns([full_text])
        self.insights = [f"Observed pattern: {w} ({c})" for w, c in self.patterns[:5]]