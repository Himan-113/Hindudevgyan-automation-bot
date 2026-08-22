import os
import json
import base64
import re
import sys

def setup_credentials():
    raw = os.environ.get('GCP_SA_KEY', '').strip()
    if not raw:
        print('[INFO] GCP_SA_KEY is empty. Skipping.')
        return

    # Method 1: Check if already direct JSON
    try:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            parsed = json.loads(match.group(0))
            if 'project_id' in parsed and 'private_key' in parsed:
                with open('vertex_sa_key.json', 'w', encoding='utf-8') as f:
                    json.dump(parsed, f, indent=2)
                print('[OK] Loaded Service Account key directly from JSON.')
                return
    except Exception:
        pass

    # Method 2: Decode from Base64 (sanitizing non-base64 characters)
    try:
        clean_b64 = re.sub(r'[^A-Za-z0-9+/=]', '', raw)
        decoded = base64.b64decode(clean_b64).decode('utf-8', errors='ignore')
        match = re.search(r'\{.*\}', decoded, re.DOTALL)
        if match:
            parsed = json.loads(match.group(0))
            with open('vertex_sa_key.json', 'w', encoding='utf-8') as f:
                json.dump(parsed, f, indent=2)
            print('[OK] Loaded Service Account key from sanitized Base64.')
            return
    except Exception:
        pass

    # Method 3: Fallback raw write
    try:
        with open('vertex_sa_key.json', 'w', encoding='utf-8') as f:
            f.write(raw)
        print('[OK] Written raw GCP_SA_KEY to vertex_sa_key.json.')
    except Exception as e:
        print(f'[WARNING] Could not write vertex_sa_key.json: {e}')

if __name__ == '__main__':
    setup_credentials()
