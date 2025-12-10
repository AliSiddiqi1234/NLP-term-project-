import spacy

# Load Spacy Model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Spacy model not found. Run: python -m spacy download en_core_web_sm")
    nlp = None

# Keywords
ACTION_KEYWORDS = {
    "move": ["move", "push", "slide", "shift", "go", "walk"],
    "pick": ["pick", "grab", "lift", "take", "collect", "get"],
    "place": ["place", "put", "drop", "set", "leave", "release"],
}

RELATION_KEYWORDS = {
    "left_of": ["left of", "to the left of", "on the left of", "left"],
    "right_of": ["right of", "to the right of", "on the right of", "right"],
    "behind": ["behind"],
    "in_front_of": ["in front of"],
    "on_top_of": ["on top of", "over"],
}

MODIFIER_KEYWORDS = {
    "closest": ["closest", "closest to", "nearest", "near"],
    "farthest": ["farthest", "farthest from", "far"],
}

RELATIONAL_NOUNS = {
    "left",
    "right",
    "front",
    "top",
    "bottom",
    "closest",
    "farthest",
    "you",
    "to",
    "of",
    "the",
    "a",
    "an",
}


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
    # Default to block if we have a color but no shape
    if color and not shape:
        shape = "block"
    return {"color": color, "shape": shape} if shape else None


def detect_relation(text):
    text_lower = text.lower()
    for rel, patterns in RELATION_KEYWORDS.items():
        for p in patterns:
            if p in text_lower:
                return rel
    return None


def detect_modifier(text):
    text_lower = text.lower()
    for mod, patterns in MODIFIER_KEYWORDS.items():
        for p in patterns:
            if p in text_lower:
                return mod
    return None


def clean_reference_np(np):
    filtered_tokens = [t for t in np if t.text.lower() not in RELATIONAL_NOUNS]
    return filtered_tokens


def parse_command(text):
    if nlp is None:
        return {}

    doc = nlp(text)

    action = detect_action(doc)
    noun_chunks = [chunk for chunk in doc.noun_chunks]

    # Filter noun chunks to find actual objects
    object_chunks = []
    for chunk in noun_chunks:
        clean_text = " ".join(
            [t.text for t in chunk if t.text.lower() not in RELATIONAL_NOUNS]
        )
        if clean_text.strip():
            object_chunks.append(chunk)

    primary_obj = (
        extract_obj_from_np(object_chunks[0]) if len(object_chunks) >= 1 else None
    )
    reference_obj = None
    modifier = None

    if len(object_chunks) >= 2:
        reference_obj = extract_obj_from_np(object_chunks[1])
        modifier = detect_modifier(text)

    relation = detect_relation(text)

    return {
        "action": action,
        "object": primary_obj,
        "relation": relation,
        "ref_object": reference_obj,
        "modifier": modifier,
    }
