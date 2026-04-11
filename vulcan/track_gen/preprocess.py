import json


def _parse_json_if_possible(value):
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text:
        return value
    if text[0] not in "[{":
        return value
    try:
        return json.loads(text)
    except Exception:
        return value


def _get_field(obj, key, default=None):
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _coerce_input_object(data):
    input_obj = _get_field(data, "input", {})
    input_obj = _parse_json_if_possible(input_obj)
    if isinstance(input_obj, dict):
        return input_obj
    raise ValueError("data.input 不是可解析的对象，无法提取 messages。")


def _content_to_text(content):
    if content is None:
        return ""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                if item.strip():
                    parts.append(item.strip())
            elif isinstance(item, dict):
                text = item.get("text")
                if text:
                    parts.append(str(text).strip())
        return "\n".join([part for part in parts if part]).strip()
    return str(content).strip()


def handler(data):
    input_obj = _coerce_input_object(data)
    messages = _parse_json_if_possible(input_obj.get("messages", []))
    if not isinstance(messages, list):
        raise ValueError("messages 不是列表，无法构造模型请求。")

    system_parts = []
    request_messages = []

    for message in messages:
        message = _parse_json_if_possible(message)
        if not isinstance(message, dict):
            continue
        role = message.get("role", "user")
        text = _content_to_text(message.get("content"))
        if not text:
            continue

        if role == "system":
            system_parts.append(text)
        else:
            request_messages.append(
                {
                    "role": role,
                    "content": text,
                }
            )

    result = {
        "messages": request_messages,
        "temperature": 0.7,
        "top_p": 0.95,
        "max_tokens": 4096,
    }

    if system_parts:
        result["system"] = "\n".join(system_parts)

    return result
