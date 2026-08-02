import json
from http import HTTPStatus
def main(req):
    try:
        body = req.get_json()
    except Exception:
        body = {}
    return {
        'statusCode': HTTPStatus.OK,
        'body': json.dumps({'stubbed': True, 'received': body})
    }
