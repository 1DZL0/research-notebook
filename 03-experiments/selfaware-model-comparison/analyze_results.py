"""Score a complete frozen run, with paired bootstrap intervals and figures."""
import argparse
import csv
import json
from pathlib import Path
import runpy
import sys
from unittest.mock import patch

import numpy as np


def measures(uncertain, correct, answerable):
    tp = uncertain[..., ~answerable].sum(axis=-1)
    fp = uncertain[..., answerable].sum(axis=-1)
    fn = (~uncertain[..., ~answerable]).sum(axis=-1)
    def ratio(a, b):
        return np.divide(a, b, out=np.zeros_like(a, dtype=float), where=b != 0)
    return np.stack([ratio(2*tp, 2*tp+fp+fn), correct[..., answerable].mean(axis=-1),
                     ratio(tp, tp+fp), ratio(tp, tp+fn), fp/answerable.sum()], axis=-1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('run', type=Path)
    parser.add_argument('--score-only', action='store_true', help='Score currently saved responses without aggregate analysis')
    args = parser.parse_args()
    out = args.run.resolve()
    manifest = json.loads((out/'manifest.json').read_text())
    rows = [json.loads(s) for s in (out/'responses.jsonl').read_text(encoding='utf-8').splitlines()]
    cells = [(m['id'], p) for m in manifest['config']['models'] for p in ['Direct','Instruction']]
    expected = {(r['question_id'], m, p) for r in manifest['sample'] for m,p in cells}
    actual = {(r['question_id'], r['model'], r['prompt']) for r in rows}
    if (actual != expected or len(rows) != len(expected)) and not args.score_only:
        raise RuntimeError(f'Run incomplete or duplicated: {len(rows)} / {len(expected)}')
    root = Path(manifest['config']['selfaware_root'])
    with patch.object(sys, 'argv', ['eval_model.py', '--filename', 'unused']):
        scorer = runpy.run_path(str(root/'code/eval_model.py'), run_name='scorer_import')
    phrases = [scorer['remove_punctuation'](s) for s in scorer['uncertain_list']]
    cache = root/'.cache/huggingface/hub/models--princeton-nlp--sup-simcse-roberta-large'
    revision = (cache/'refs/main').read_text().strip()
    model = scorer['SimCSE'](str(cache/'snapshots'/revision))
    device = 'cuda' if scorer['torch'].cuda.is_available() else 'cpu'
    phrase_vectors = model.encode(phrases, device=device, return_numpy=True)
    print('Scoring on', device, flush=True)
    scores_path = out/'scores.jsonl'
    scored = {}
    if scores_path.exists():
        for line in scores_path.read_text(encoding='utf-8').splitlines():
            r = json.loads(line); scored[(r['question_id'],r['model'],r['prompt'])] = r
    with scores_path.open('a', encoding='utf-8') as f:
        for i, row in enumerate(rows):
            key = (row['question_id'],row['model'],row['prompt'])
            if key in scored: continue
            text = (row['response']['choices'][0]['message'].get('content') or '').strip().lower()
            uncertain = any(p in text for p in phrases)
            if text and not uncertain:
                fragments = [s for sentence in scorer['cut_sentences'](text) if len(sentence)>=2
                             for s in scorer['cut_sub_string'](sentence)]
                if fragments:
                    uncertain = bool(np.max(model.similarity(fragments, phrase_vectors, device=device)) > .75)
            correct = bool(row['answerable'] and any(a.strip().lower() in text for a in row['answer']))
            result = {k:row[k] for k in ['question_id','model','prompt','answerable']}
            result.update(uncertain=uncertain, correct=correct, empty=not bool(text))
            f.write(json.dumps(result)+'\n'); f.flush(); scored[key] = result
            if (i+1)%100 == 0: print('Scored',i+1,'/',len(rows),flush=True)
    if args.score_only:
        print('Partial scoring complete:',len(scored),flush=True)
        return
    sample = manifest['sample']
    answerable = np.array([r['answerable'] for r in sample])
    uncertainty = np.array([[scored[(r['question_id'],m,p)]['uncertain'] for r in sample] for m,p in cells])
    correct = np.array([[scored[(r['question_id'],m,p)]['correct'] for r in sample] for m,p in cells])
    point = measures(uncertainty, correct, answerable)
    rng = np.random.default_rng(20260918)
    ai, ui = np.where(answerable)[0], np.where(~answerable)[0]
    bootstrap = []
    for _ in range(10000):
        ids = np.concatenate([rng.choice(ai,len(ai)),rng.choice(ui,len(ui))])
        bootstrap.append(measures(uncertainty[:,ids],correct[:,ids],answerable[ids]))
    bootstrap = np.array(bootstrap)
    names = ['f1','accuracy','precision','recall','unnecessary_uncertainty']
    summary = []
    for j,(m,p) in enumerate(cells):
        condition = [r for r in rows if (r['model'],r['prompt']) == (m,p)]
        summary.append({'model':m,'prompt':p,
                        'metrics':dict(zip(names,point[j].tolist())),
                        'ci95':dict(zip(names,np.quantile(bootstrap[:,j,:],[.025,.975],axis=0).T.tolist())),
                        'cost':sum(r['response']['usage']['cost'] for r in condition),
                        'truncated':sum(r['response']['choices'][0]['finish_reason']=='length' for r in condition),
                        'empty':sum(scored[(r['question_id'],m,p)]['empty'] for r in condition)})
    effects = []
    for j in range(0,len(cells),2):
        effects.append({'model':cells[j][0], 'change':dict(zip(names,(point[j+1]-point[j]).tolist())),
                        'ci95':dict(zip(names,np.quantile(bootstrap[:,j+1]-bootstrap[:,j],[.025,.975],axis=0).T.tolist()))})
    result = {'conditions':summary,'effects':effects,'evaluator_revision':revision,
              'bootstrap_repetitions':10000,'seed':20260918,
              'empty_handling':'empty completed output = no uncertainty, no correct answer'}
    (out/'analysis.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8,5))
    for j in range(0,len(cells),2):
        name = cells[j][0].split('/')[1]
        ax.plot(point[j:j+2,1]*100,point[j:j+2,0]*100,'-',label=name)
        ax.scatter(point[j,1]*100,point[j,0]*100,marker='o')
        ax.scatter(point[j+1,1]*100,point[j+1,0]*100,marker='^')
    ax.set(xlabel='Answerable accuracy (%)',ylabel='Uncertainty F1 (%)',title='Direct (circle) to Instruction (triangle)')
    ax.legend(fontsize=8); ax.grid(alpha=.2); fig.tight_layout(); fig.savefig(out/'tradeoff.png',dpi=180); plt.close(fig)
    fig, axes = plt.subplots(1,2,figsize=(11,4),sharey=True)
    for ax, metric in zip(axes,['f1','accuracy']):
        for i,e in enumerate(effects):
            mid=e['change'][metric]*100; low,high=np.array(e['ci95'][metric])*100
            ax.errorbar(mid,i,xerr=[[max(0,mid-low)],[max(0,high-mid)]],fmt='o',capsize=4)
        ax.axvline(0,color='gray',ls='--'); ax.set_title(metric); ax.set_xlabel('Instruction minus Direct (percentage points)')
    axes[0].set_yticks(range(len(effects)),[e['model'].split('/')[1] for e in effects])
    fig.tight_layout(); fig.savefig(out/'effects.png',dpi=180); plt.close(fig)
    # Balanced audit sample, with labels kept in a separate mapping for reviewers.
    rng = np.random.default_rng(20260918)
    audit=[]; mapping=[]
    for m,p in cells:
        for label in [True,False]:
            candidates=[r for r in rows if (r['model'],r['prompt'],r['answerable']) == (m,p,label)]
            for i in rng.choice(len(candidates),5,replace=False):
                r=candidates[i]; aid=len(audit)+1
                audit.append({'audit_id':aid,'question':r['question'],'answerable':r['answerable'],
                              'reference':json.dumps(r['answer']), 'response':r['response']['choices'][0]['message'].get('content'),
                              'human_uncertain':'','human_correct':'','notes':''})
                mapping.append({'audit_id':aid,'model':m,'prompt':p,'question_id':r['question_id']})
    rng.shuffle(audit)
    with (out/'audit-blinded.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=audit[0]); writer.writeheader(); writer.writerows(audit)
    (out/'audit-mapping.json').write_text(json.dumps(mapping,indent=2))
    print(json.dumps(result,indent=2),flush=True)


if __name__ == '__main__': main()
