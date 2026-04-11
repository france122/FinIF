"""
Vulcan postprocess — Track generation (GPT-5).
"""
import json


def handler(data):
    # 1. 解析输入
    input_data = json.loads(data.input)

    # 2. 获取模型输出
    model_output = json.loads(data.steps['model_request'].output)

    # 3. 提取 response text
    response_text = ""
    for item in model_output.get("output", []):
        if isinstance(item, dict) and item.get("type") == "message":
            for part in item.get("content", []):
                if isinstance(part, dict) and part.get("type") == "output_text":
                    response_text = part.get("text", "").strip()
                    break
            if response_text:
                break

    # 4. 解析 JSON 数组（4 条 track）
    tracks = []
    parse_error = ""
    if response_text:
        text = response_text
        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                tracks = parsed
            elif isinstance(parsed, dict):
                tracks = [parsed]
        except json.JSONDecodeError as e:
            parse_error = f"track_parse_error: {e}"

    return {
        "query_id": input_data.get("query_id", ""),
        "batch": input_data.get("batch", ""),
        "tracks": tracks,
        "n_tracks": len(tracks),
        "parse_error": parse_error,
        "usage": model_output.get("usage"),
    }
