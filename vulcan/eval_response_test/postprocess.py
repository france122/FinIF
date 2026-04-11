"""
Vulcan postprocess — Test response generation (GPT-5).
"""
import json


def handler(data):
    # 1. 解析输入
    input_data = json.loads(data.input)

    # 2. 获取模型输出
    model_output = json.loads(data.steps['model_request'].output)

    # 3. 提取 response text: output[].type=="message" → content[].type=="output_text" → text
    response_text = ""
    for item in model_output.get("output", []):
        if isinstance(item, dict) and item.get("type") == "message":
            for part in item.get("content", []):
                if isinstance(part, dict) and part.get("type") == "output_text":
                    response_text = part.get("text", "").strip()
                    break
            if response_text:
                break

    return {
        "sample_id": input_data.get("sample_id", ""),
        "query_id": input_data.get("query_id", ""),
        "batch": input_data.get("batch", ""),
        "track_type": input_data.get("track_type", ""),
        "constraints": input_data.get("constraints", []),
        "response": response_text,
        "response_nonempty": bool(response_text),
        "usage": model_output.get("usage"),
    }
