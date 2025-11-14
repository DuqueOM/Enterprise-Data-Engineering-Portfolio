# scripts/annotate.py
# Example: push tasks to Label Studio project via API (requires LABEL_STUDIO_URL and API_KEY)
import os, json, requests

LABEL_STUDIO_URL = os.getenv('LABEL_STUDIO_URL','http://localhost:8080')
API_KEY = os.getenv('LABEL_STUDIO_API_KEY', '')
PROJECT_ID = int(os.getenv('LABEL_STUDIO_PROJECT_ID','1'))

def import_tasks(tasks):
    headers = {'Authorization': f'Token {API_KEY}'}
    url = f"{LABEL_STUDIO_URL}/api/projects/{PROJECT_ID}/tasks/bulk/"
    r = requests.post(url, json=tasks, headers=headers)
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    # Load processed file and create simple tasks
    in_path = 'data/processed/faqs_clean.jsonl'
    tasks = []
    with open(in_path, 'r', encoding='utf8') as f:
        for line in f:
            obj = json.loads(line)
            tasks.append({'data': {'text': obj['text'], 'source_url': obj['source_url']}})
            if len(tasks) >= 100:
                break
    if not API_KEY:
        print('Set LABEL_STUDIO_API_KEY environment variable before running.')
    else:
        resp = import_tasks(tasks)
        print('Imported tasks:', resp.get('task_ids',[])[:5])
