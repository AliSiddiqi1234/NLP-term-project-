import spacy

nlp = spacy.load("en_core_web_sm")

ACTION_KEYWORDS = {
    "move": ["move", "push", "slide", "shift"],
    "pick": ["pick", "grab", "lift"],
    "place": ["place", "put", "drop", "set"]
}

RELATION_KEYWORDS = {
    "left_of": ["left of", "to the left of", "on the left of"],
    "right_of": ["right of", "to the right of", "on the right of"],
    "behind": ["behind"],
    "in_front_of": ["in front of"],
    "on_top_of": ["on top of", "over"]
}

MODIFIER_KEYWORDS = {
    "closest": ["closest", "closest to"],
    "farthest": ["farthest", "farthest from"]
}

RELATIONAL_NOUNS = {"left", "right", "front", "top", "bottom", "closest", "farthest", "you", "to", "of"}


def detect_action(doc):
    for token in doc:
        for action, verbs in ACTION_KEYWORDS.items():
            if token.lemma_ in verbs:
                return action
    return None


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


def detect_relation(text):
    text_lower = text.lower()
    for rel, patterns in RELATION_KEYWORDS.items():
        for p in patterns:
            if p in text_lower:
                return rel
    return None


def detect_modifier(text):
    """Detect modifiers like 'closest'."""
    text_lower = text.lower()
    for mod, patterns in MODIFIER_KEYWORDS.items():
        for p in patterns:
            if p in text_lower:
                return mod
    return None


def clean_reference_np(np):
    """Remove relational words but keep object tokens."""
    filtered_tokens = [t for t in np if t.text.lower() not in RELATIONAL_NOUNS]
    return filtered_tokens


def parse_command(text):
    doc = nlp(text)

    action = detect_action(doc)
    noun_chunks = [chunk for chunk in doc.noun_chunks]
    object_chunks = [chunk for chunk in noun_chunks if chunk.root.text.lower() not in RELATIONAL_NOUNS]

    primary_obj = extract_obj_from_np(object_chunks[0]) if len(object_chunks) >= 1 else None
    reference_obj = None
    modifier = None

    if len(object_chunks) >= 2:
        ref_chunk = clean_reference_np(object_chunks[1])
        reference_obj = extract_obj_from_np(ref_chunk)
        modifier = detect_modifier(text)

    relation = detect_relation(text)

    return {
        "action": action,
        "object": primary_obj,
        "relation": relation,
        "ref_object": reference_obj,
        "modifier": modifier
    }

# === Example ===
if __name__ == "__main__":
    test = "Move the red block to the closest blue block."
    result = parse_command(test)
    print(result)
