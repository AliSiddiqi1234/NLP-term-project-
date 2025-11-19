import spacy
import pandas as pd
from collections import Counter

nlp = spacy.load("en_core_web_sm")

#words to ignore when parsing reference NPs
RELATIONAL_NOUNS = {"left", "right", "front", "top", "bottom", "closest", "farthest", "you", "to", "of"}

#load our dataset
def load_dataset(path="NLICorpusData.csv"):
    return pd.read_csv(path)

#extract the action keywords from our dataset 
def extract_action_keywords(df):
    verb_counter = Counter()

    for text in df["Instruction"]:
        doc = nlp(str(text))
        for token in doc:
            if token.pos_ == "VERB":
                verb_counter[token.lemma_.lower()] += 1

    #create a list which contains all the verbs taht show up more than once  
    common_verbs = [v for v, c in verb_counter.items() if c >= 2]

    return {"action": common_verbs}


SPATIAL_WORDS = {
    "left", "right", "front", "behind", "top", "bottom",
    "middle", "between", "under", "over", "below", "above"
}

#extract the relational keywords from our dataset, like "left" and "right" 
def extract_relation_keywords(df):
    phrase_counter = Counter()

    for text in df["Instruction"]:
        tokens = str(text).lower().split()
        for i in range(len(tokens) - 2):
            tri = " ".join(tokens[i:i+3])
            if any(w in tri for w in SPATIAL_WORDS):
                phrase_counter[tri] += 1

    common_phrases = [p for p, c in phrase_counter.items() if c >= 2]
    return {"relation": common_phrases}


MODIFIER_CANDIDATES = {"closest", "nearest", "farthest", "biggest", "smallest"}

#extract the modifier keywords, which tells you more about the other you want the robot to place near   
def extract_modifier_keywords(df):
    modifier_counter = Counter()

    for text in df["Instruction"]:
        doc = nlp(str(text))
        for token in doc:
            if token.text.lower() in MODIFIER_CANDIDATES:
                modifier_counter[token.text.lower()] += 1

    return {"modifier": list(modifier_counter.keys())}

#takes user input and checks to see if the word they gave was actually a valid action        
def detect_action(doc, ACTION_KEYWORDS):
    action_words = ACTION_KEYWORDS.get("action", [])
    for token in doc:
        lemma = token.lemma_.lower()
        if lemma in action_words:
            return lemma        
    return None

#get the color and shape of the object based off the corpus
def extract_obj_from_np(np):
    color = None
    shape = None
    for token in np:
        if token.text.lower() in RELATIONAL_NOUNS:
            continue
        if token.pos_ == "ADJ":
            color = token.text
        if token.pos_ == "NOUN":
            shape = token.text
    return {"color": color, "shape": shape} if shape else None

#checks user input and returns the actual relation of the object  
def detect_relation(text, RELATION_KEYWORDS):
    text_lower = text.lower()
    for phrase in RELATION_KEYWORDS.get("relation", []):
        if phrase in text_lower:
            return phrase       
    return None

#literally like the other two functions, but for modifiers 
def detect_modifier(text, MODIFIER_KEYWORDS):
    text_lower = text.lower()
    for mod in MODIFIER_KEYWORDS.get("modifier", []):
        if mod in text_lower:
            return mod          
    return None

#gets words which are not in the dictionary of relation nouns   
def clean_reference_np(np):
    return [t for t in np if t.text.lower() not in RELATIONAL_NOUNS]

#the actual parser to be used on user input 
def parse_command(text, ACTION_KEYWORDS, RELATION_KEYWORDS, MODIFIER_KEYWORDS):
    doc = nlp(text)

    action = detect_action(doc, ACTION_KEYWORDS)
    #basically gets all the noun phrases from the text for a list  
    noun_chunks = [chunk for chunk in doc.noun_chunks]
    #removes nouns like left, right, etc
    object_chunks = [
        chunk for chunk in noun_chunks 
        if chunk.root.text.lower() not in RELATIONAL_NOUNS
    ]

    #the main object of a users sentence 
    primary_obj = extract_obj_from_np(object_chunks[0]) if len(object_chunks) >= 1 else None
    reference_obj = None
    modifier = None

    #if there are secondary objects in the sentence, remove the relational nouns from it if it has any, get the color and shape, as well as figure out if it has any modifiers        
    if len(object_chunks) >= 2:
        ref_chunk = clean_reference_np(object_chunks[1])
        reference_obj = extract_obj_from_np(ref_chunk)
        modifier = detect_modifier(text, MODIFIER_KEYWORDS)
    
    relation = detect_relation(text, RELATION_KEYWORDS)

    return {
        "action": action,
        "object": primary_obj,
        "relation": relation,
        "ref_object": reference_obj,
        "modifier": modifier
    }

if __name__ == "__main__":
    df = load_dataset()

    #get all the keywords from our corpus 
    ACTION_KEYWORDS = extract_action_keywords(df)
    RELATION_KEYWORDS = extract_relation_keywords(df)
    MODIFIER_KEYWORDS = extract_modifier_keywords(df)

    print("Action keywords:", ACTION_KEYWORDS)
    print("Relation keywords:", RELATION_KEYWORDS)
    print("Modifier keywords:", MODIFIER_KEYWORDS)

    while True:
        text = input("Enter a text command using the given keywords above in a sentence: ")
        if text.lower() == "quit":
            break

        parsed = parse_command(text, ACTION_KEYWORDS, RELATION_KEYWORDS, MODIFIER_KEYWORDS)
        print(parsed)
