"""Frozen paired SelfAware study with durable reservations and bounded retries."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
import threading
import time

import requests
from dotenv import dotenv_values

HERE = Path(__file__).resolve().parent
SYSTEM = 'You are an excellent question responder.'
PROMPTS = {
    'Direct': 'Q:{}\nA:',
    'Instruction': 'When answering questions, interpret them literally and think them carefully. If the question is unanswerable or unknowable, it is appropriate to say, "The answer is unknown."\nQ: {}\nA:',
}


def sample_data(data):
    rng = random.Random(20260918)
    selected = []
    for label, count in [(True, 520), (False, 230)]:
        groups = defaultdict(list)
        for row in data:
            if row['answerable'] is label:
                groups[row.get('source', 'unknown')].append(row)
        total = sum(map(len, groups.values()))
        quotas = {k: count * len(v) / total for k, v in groups.items()}
        sizes = {k: math.floor(v) for k, v in quotas.items()}
        for k in sorted(groups, key=lambda k: (-(quotas[k] - sizes[k]), k))[:count-sum(sizes.values())]:
            sizes[k] += 1
        for k in sorted(groups):
            selected.extend(rng.sample(groups[k], sizes[k]))
    rng.shuffle(selected)
    # A balanced two-question pilot, retained in the main paired sample.
    first = [next(r for r in selected if r['answerable'] is b) for b in (True, False)]
    return first + [r for r in selected if r not in first]


class Ledger:
    def __init__(self, path, limit):
        self.path, self.limit = path, limit
        self.lock = threading.Lock()
        self.items = json.loads(path.read_text()) if path.exists() else []

    def save(self):
        temporary = self.path.with_suffix('.tmp')
        temporary.write_text(json.dumps(self.items, indent=2), encoding='utf-8')
        temporary.replace(self.path)

    def total(self):
        return sum(x.get('actual', x['reserved']) for x in self.items)

    def reserve(self, amount, task):
        with self.lock:
            if self.total() + amount > self.limit:
                raise RuntimeError('Budget exhausted before dispatch')
            self.items.append({'task': task, 'reserved': amount})
            self.save()
            return len(self.items)-1

    def settle(self, index, cost):
        with self.lock:
            if not isinstance(cost, (int, float)) or not math.isfinite(cost) or cost < 0:
                raise RuntimeError('Missing or invalid cost; reservation retained')
            reserved = self.items[index]['reserved']
            self.items[index]['actual'] = cost
            self.save()
            if cost > reserved + 1e-9:
                raise RuntimeError('Charge exceeded conservative reservation; stop')


def reservation(messages, rates):
    # Text token count conservatively bounded by UTF-8 bytes plus framing margin.
    inputs = sum(len(m['content'].encode('utf-8')) for m in messages) + 256
    return (inputs*rates['prompt'] + 1024*rates['completion']) / 1e6 * 1.1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--pilot-only', action='store_true')
    parser.add_argument('--resume', type=Path)
    parser.add_argument('--config', type=Path, default=HERE/'config-original.json')
    parser.add_argument('--extend-from', type=Path,
                        help='Reuse the exact frozen sample and account for the earlier run in the $35 total')
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding='utf-8'))
    root = Path(config['selfaware_root'])
    raw = (root/'data/SelfAware.json').read_bytes()
    data = json.loads(raw)['example']
    selected = sample_data(data)
    prior_cost = 0
    if args.extend_from:
        prior = args.extend_from.resolve()
        prior_manifest = json.loads((prior/'manifest.json').read_text(encoding='utf-8'))
        if prior_manifest['dataset_sha256'] != hashlib.sha256(raw).hexdigest():
            raise RuntimeError('Original dataset changed; cannot reuse its sample')
        if prior_manifest['sample'] != selected:
            raise RuntimeError('Selected questions differ from the frozen first run')
        prior_ledger = json.loads((prior/'ledger.json').read_text(encoding='utf-8'))
        prior_cost = sum(item.get('actual', item['reserved']) for item in prior_ledger)
    assert len(selected) == len({r['question_id'] for r in selected}) == 750
    print('Frozen sample:', dict(Counter(r['answerable'] for r in selected)), flush=True)
    if not args.execute:
        print('Offline preflight passed. No API calls.'); return
    key = dotenv_values(root/'.env')['OPENROUTER_API_KEY']
    headers = {'Authorization': 'Bearer '+key}
    info = requests.get('https://openrouter.ai/api/v1/key', headers=headers, timeout=30)
    info.raise_for_status()
    remaining = info.json()['data']['limit_remaining']
    if remaining is None:
        raise RuntimeError('A provider-side key limit is required')
    if args.resume:
        out = args.resume.resolve()
        manifest = json.loads((out/'manifest.json').read_text())
        config, selected = manifest['config'], manifest['sample']
    else:
        out = HERE/'runs'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-budget750')
        out.mkdir(parents=True, exist_ok=False)
        manifest = {'config': config, 'sample': selected, 'seed': 20260918,
                    'dataset_sha256': hashlib.sha256(raw).hexdigest(),
                    'budget_usd': min(35-prior_cost, remaining)-.25,
                    'key_remaining_at_start': remaining,
                    'extended_from': str(args.extend_from.resolve()) if args.extend_from else None,
                    'prior_cost_usd': prior_cost,
                    'sampling': 'answerability and source; no category or group IDs in dataset',
                    'prompts': PROMPTS, 'system': SYSTEM}
        (out/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    ledger = Ledger(out/'ledger.json', manifest['budget_usd'])
    # Resumption must respect both the original ledger and current key allowance.
    ledger.limit = min(ledger.limit, ledger.total() + remaining - .25)
    cells = [(m, p) for m in config['models'] for p in config['prompts']]
    random.Random(20260918).shuffle(cells)
    results = out/'responses.jsonl'
    done = set()
    if results.exists():
        for line in results.read_text(encoding='utf-8').splitlines():
            row = json.loads(line)
            done.add((row['question_id'], row['model'], row['prompt']))
    stopped = threading.Event()
    write_lock = threading.Lock()

    def generate(task):
        question, model, prompt = task
        identity = (question['question_id'], model['id'], prompt)
        if identity in done: return
        messages = [{'role':'system', 'content':SYSTEM},
                    {'role':'user', 'content':PROMPTS[prompt].format(question['question'])}]
        payload = {'model':model['id'], 'messages':messages, 'temperature':.7,
                   'max_tokens':1024, 'reasoning':{'enabled':False},
                   'provider':{'require_parameters':True, 'sort':'price', 'max_price':model['max_price']}}
        for attempt in range(5):
            if stopped.is_set(): return
            index = ledger.reserve(reservation(messages, model['max_price']), identity)
            try:
                response = requests.post('https://openrouter.ai/api/v1/chat/completions',
                                         headers=headers, json=payload, timeout=150)
                if response.status_code != 200:
                    with write_lock, (out/'errors.jsonl').open('a', encoding='utf-8') as f:
                        f.write(json.dumps({'task':identity, 'status':response.status_code,
                                            'attempt':attempt, 'body':response.text[:1000]})+'\n')
                    if response.status_code in (429, 500, 502, 503, 504) and attempt < 4:
                        time.sleep(min(45, 3 * 2**attempt)); continue
                    raise RuntimeError(f'Provider HTTP {response.status_code}; see errors.jsonl')
                body = response.json()
                if not body.get('choices') or not body.get('usage'):
                    with write_lock, (out/'errors.jsonl').open('a', encoding='utf-8') as f:
                        f.write(json.dumps({'task':identity,'status':body.get('error',{}).get('code'),
                                            'attempt':attempt,'body':json.dumps(body)[:1000]})+'\n')
                    if attempt < 4:
                        time.sleep(min(45, 3 * 2**attempt)); continue
                    raise RuntimeError('Provider returned an error body without a completion')
                # Save raw response even if usage/controls fail validation.
                row = {**question, 'model':model['id'], 'prompt':prompt, 'response':body}
                with write_lock, results.open('a', encoding='utf-8') as f:
                    f.write(json.dumps(row, ensure_ascii=False)+'\n')
                ledger.settle(index, body.get('usage', {}).get('cost'))
                if body.get('usage', {}).get('completion_tokens_details', {}).get('reasoning_tokens', 0):
                    raise RuntimeError('Reasoning-off control violated')
                if not body.get('choices') or body['choices'][0].get('finish_reason') == 'error':
                    raise RuntimeError('Invalid generation response')
                done.add(identity)
                return
            except requests.RequestException:
                # Uncertain billing keeps the entire reservation, including on retry.
                if attempt < 4:
                    time.sleep(min(45, 3 * 2**attempt)); continue
                stopped.set(); raise
            except Exception:
                stopped.set(); raise

    print('Run directory:', out, 'Extension budget:', round(ledger.limit, 4),
          'Prior cost:', round(manifest.get('prior_cost_usd',0),4), flush=True)
    questions = selected[:2] if args.pilot_only else selected
    with ThreadPoolExecutor(max_workers=8) as pool:
        for start in range(0, len(questions), 10):
            batch = questions[start:start+10]
            futures = [pool.submit(generate, (question, m, p)) for question in batch for m,p in cells]
            for future in futures: future.result()
            print(f'{start+len(batch)}/750 paired questions; {len(done)} responses; reserved/charged ${ledger.total():.4f}', flush=True)
    print('PILOT COMPLETE' if args.pilot_only else 'GENERATION COMPLETE', flush=True)


if __name__ == '__main__':
    main()
