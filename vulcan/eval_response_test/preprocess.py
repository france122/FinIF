"""
Vulcan preprocess — Test response generation (GPT-5).
"""


def _content_to_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
        return "\n".join(parts)
    return str(content)


def handler(data):
    import json

    raw = data.input
    if isinstance(raw, str):
        raw = json.loads(raw)

    messages = raw.get("messages", [])

    input_messages = []
    for msg in messages:
        role = msg.get("role", "user")
        text = _content_to_text(msg.get("content", ""))
        if role == "system":
            continue
        input_messages.append({"role": role, "content": text})

    return {
        "input": input_messages,
        "reasoning": {"effort": "medium"},
    }
