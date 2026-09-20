"""Reproduce paper values beside the completed extension, without implying equivalence."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
REPORT = HERE / 'report'

paper_f1 = {
    'davinci': 45.67,
    'text-davinci-001': 49.61,
    'text-davinci-002': 47.48,
    'text-davinci-003': 51.43,
    'GPT-3.5 Turbo': 54.12,
    'GPT-4': 75.47,
}
paper_accuracy = {
    'text-ada-001': 2.48,
    'text-babbage-001': 4.45,
    'text-curie-001': 4.70,
    'text-davinci-001': 10.61,
    'text-davinci-002': 15.70,
    'text-davinci-003': 30.25,
    'GPT-3.5 Turbo': 38.29,
    'GPT-4': 42.64,
}

analysis = json.loads((REPORT / 'results.json').read_text(encoding='utf-8'))
current = {
    row['model'].split('/')[-1]: {
        'f1': row['metrics']['f1'] * 100,
        'accuracy': row['metrics']['accuracy'] * 100,
    }
    for row in analysis['conditions'] if row['prompt'] == 'Instruction'
}


def panel(ax, values, title, color, limit, human=False):
    labels = list(values)
    scores = list(values.values())
    bars = ax.barh(labels, scores, color=color, edgecolor='#31343a', linewidth=.5)
    ax.invert_yaxis()
    ax.set_xlim(0, limit)
    ax.set_title(title, loc='left', fontweight='bold')
    ax.set_xlabel('Score (%)')
    ax.grid(axis='x', alpha=.18)
    ax.set_axisbelow(True)
    ax.bar_label(bars, fmt='%.2f', padding=3, fontsize=8)
    if human:
        ax.axvline(84.93, color='#8f2633', linestyle='--', linewidth=1.5)
        ax.text(84.1, -.38, 'Human 84.93', ha='right', va='bottom',
                color='#8f2633', fontsize=8, fontweight='bold')


fig, axes = plt.subplots(1, 2, figsize=(12, 5.4), constrained_layout=True)
panel(axes[0], paper_f1, 'Paper (2023): Instruction F1', '#d99068', 92, human=True)
panel(axes[1], {k:v['f1'] for k,v in current.items()},
      'Our extension (2026): Instruction F1', '#4b7ba7', 92, human=True)
fig.suptitle('Uncertainty recognition on SelfAware', fontsize=15, fontweight='bold')
fig.text(.5, -.01,
         'Descriptive comparison only: paper models mostly use the full dataset; GPT-4 and human use 100 random cases; ours uses a frozen stratified sample of 750.',
         ha='center', fontsize=8, color='#555b63')
fig.savefig(REPORT / 'paper-vs-extension-f1.png', dpi=200, bbox_inches='tight')
plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(12, 5.8), constrained_layout=True)
panel(axes[0], paper_accuracy, 'Paper (2023): answerable accuracy', '#d9ad68', 60)
panel(axes[1], {k:v['accuracy'] for k,v in current.items()},
      'Our extension (2026): answerable accuracy', '#4f8b70', 60)
fig.suptitle('Correct answers under the Instruction prompt', fontsize=15, fontweight='bold')
fig.text(.5, -.01,
         'Descriptive comparison only. Accuracy is substring matching; model access, samples and generation environments differ.',
         ha='center', fontsize=8, color='#555b63')
fig.savefig(REPORT / 'paper-vs-extension-accuracy.png', dpi=200, bbox_inches='tight')
plt.close(fig)

(REPORT / 'paper-comparison-values.json').write_text(json.dumps({
    'source': 'Yin et al. (2023), Figures 3 and 6',
    'paper_instruction_f1': paper_f1,
    'paper_instruction_answerable_accuracy': paper_accuracy,
    'paper_human_f1': 84.93,
    'extension_instruction': current,
    'comparison_status': 'descriptive only',
    'sample_note': 'Paper: full SelfAware except GPT-4 uses 100 random instances; human uses 100 random instances. Extension: fixed stratified sample of 750.',
}, indent=2), encoding='utf-8')

print('Created paper comparison figures and source values.')
