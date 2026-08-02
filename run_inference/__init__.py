import json
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
    except Exception:
        body = {}
    payload = {"stubbed": True, "function": "run_inference", "received": body}
    return func.HttpResponse(
        json.dumps(payload),
        status_code=200,
        mimetype="application/json",
    )
