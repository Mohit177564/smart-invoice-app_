def process_predictions(encoding, predicted, model):
    tokens = encoding.tokens()
    labels = [model.config.id2label[p.item()] for p in predicted[0]]

    entities = {}
    current_entity = None
    current_tokens = []

    for token, label in zip(tokens, labels):
        if label == "O":
            if current_entity:
                entities[current_entity] = entities.get(current_entity, "") + " " + " ".join(current_tokens)
                current_entity = None
                current_tokens = []
        elif label.startswith("B-"):
            if current_entity:
                entities[current_entity] = entities.get(current_entity, "") + " " + " ".join(current_tokens)
            current_entity = label[2:]
            current_tokens = [token]
        elif label.startswith("I-") and current_entity:
            current_tokens.append(token)

    # Add last entity
    if current_entity and current_tokens:
        entities[current_entity] = entities.get(current_entity, "") + " " + " ".join(current_tokens)

    # Clean result
    cleaned = {key: value.replace("##", "").replace("[PAD]", "").strip() for key, value in entities.items()}

    return cleaned
