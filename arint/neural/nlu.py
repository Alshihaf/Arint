# neural/nlu.py
import re

class AdvancedNLU:
    def __init__(self):
        self.lexicon = {
            'makan': 'VERB', 'mancing': 'VERB', 'coding': 'VERB',
            'saya': 'PRON', 'gua': 'PRON', 'lu': 'PRON',
            'keren': 'ADJ', 'mantap': 'ADJ', 'rizz': 'ADJ'
        }

    def tokenize(self, text):
        return re.findall(r'\w+|[^\w\s]', text)

    def get_pos(self, tokens):
        tagged = []
        for i, word in enumerate(tokens):
            if word[0].isupper() and i != 0:
                tag = 'PROPN'
            elif word.lower() in self.lexicon:
                tag = self.lexicon[word.lower()]
            elif re.match(r'.*(ing|kan|i)$', word.lower()):
                tag = 'VERB'
            elif re.match(r'.*(ly|nya)$', word.lower()):
                tag = 'ADV'
            else:
                tag = 'NOUN'
            tagged.append((word, tag))
        return tagged