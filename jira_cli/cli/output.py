import json


def print_error(code: str, message: str, details: dict) -> str:
    return json.dumps(
        {"error": {"code": code, "message": message, "details": details}},
        separators=(",", ":"),
    )
