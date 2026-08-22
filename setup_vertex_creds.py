import os
import json
import base64

def setup_credentials():
    raw = os.environ.get('GCP_SA_KEY', '').strip()
    if not raw:
        print('[INFO] GCP_SA_KEY is empty.')
        return

    # Try 1: Base64 decode
    try:
        decoded_bytes = base64.b64decode(raw)
        data = json.loads(decoded_bytes.decode('utf-8'))
        with open('vertex_sa_key.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print('[OK] Successfully created vertex_sa_key.json from Base64.')
        return
    except Exception as e1:
        pass

    # Try 2: Raw JSON
    try:
        data = json.loads(raw)
        with open('vertex_sa_key.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print('[OK] Successfully created vertex_sa_key.json from Raw JSON.')
        return
    except Exception as e2:
        print(f'[ERROR] Failed to parse GCP_SA_KEY: {e2}')

if __name__ == '__main__':
    setup_credentials()
