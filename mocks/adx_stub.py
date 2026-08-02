# mocks/adx_stub.py
import json
_storage_file = 'mock_adx_storage.json'
def insert(record):
    try:
        with open(_storage_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\\n')
        return True
    except Exception as e:
        return False
