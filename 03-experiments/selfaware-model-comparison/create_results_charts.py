"""Create the chart-first presentation of the completed five-model experiment."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
REPORT = HERE / 'report'
analysis = json.loads((REPORT / 'results.json').read_text(encoding='utf-8'))

display = {
    'deepseek-v4-pro-0813': 'DeepSeek V4 Pro',
    'qwen3.7-plus': 'Qwen3.7 Plus',
    'claude-sonnet-4.6': 'Claude Sonnet 4.6',
    'kimi-k3': 'Kimi K3',
    'qwen3.7-max': 'Qwen3.7 Max',
}
models = list(display)
conditions = {(r['model'].split('/')[-1], r['prompt']): r
              for r in analysis['conditions']}
effects = {r['model'].split('/')[-1]: r for r in analysis['effects']}

DIRECT = '#d68a5f'
INSTRUCTION = '#3977a8'
GRID = '#d9dde2'


def comparison_chart():
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5), constrained_layout=True)
    y = np.arange(len(models))
    for ax, metric, title, limit in [
        (axes[0], 'f1', 'Recognising unanswerable questions (F1)', 70),
        (axes[1], 'accuracy', 'Correct answers on answerable questions', 60),
    ]:
        direct = np.array([conditions[(m, 'Direct')]['metrics'][metric] * 100 for m in models])
        instruction = np.array([conditions[(m, 'Instruction')]['metrics'][metric] * 100 for m in models])
        ax.hlines(y, direct, instruction, color='#aeb5bd', linewidth=3, zorder=1)
        ax.scatter(direct, y, color=DIRECT, s=75, label='Direct', zorder=2)
        ax.scatter(instruction, y, color=INSTRUCTION, s=75, marker='^', label='Instruction', zorder=2)
        for row, (a, b) in enumerate(zip(direct, instruction)):
            ax.text(a, row-.18, f'{a:.1f}', color=DIRECT, ha='center', va='bottom', fontsize=8)
            ax.text(b, row+.18, f'{b:.1f}', color=INSTRUCTION, ha='center', va='top', fontsize=8)
        ax.set_xlim(0, limit)
        ax.set_xlabel('Score (%)')
        ax.set_title(title, loc='left', fontweight='bold')
        ax.set_yticks(y, [display[m] for m in models])
        ax.invert_yaxis()
        ax.grid(axis='x', color=GRID, alpha=.65)
        ax.set_axisbelow(True)
    axes[1].legend(loc='upper left', frameon=False)
    fig.suptitle('What changed when models were told to acknowledge uncertainty?',
                 fontsize=15, fontweight='bold')
    fig.savefig(REPORT / 'five-model-direct-vs-instruction.png', dpi=200, bbox_inches='tight')
    plt.close(fig)


def effects_chart():
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.4), sharey=True, constrained_layout=True)
    y = np.arange(len(models))
    for ax, metric, title in [
        (axes[0], 'f1', 'Change in uncertainty F1'),
        (axes[1], 'accuracy', 'Change in answerable accuracy'),
    ]:
        values = np.array([effects[m]['change'][metric] * 100 for m in models])
        intervals = np.array([effects[m]['ci95'][metric] for m in models]) * 100
        colors = np.where(values >= 0, INSTRUCTION, '#a5464f')
        for row, (value, interval, color) in enumerate(zip(values, intervals, colors)):
            ax.plot(interval, [row, row], color=color, linewidth=3)
            ax.scatter(value, row, color=color, s=55, zorder=2)
            ax.text(value, row-.18, f'{value:+.1f}', color=color, ha='center', va='bottom', fontsize=8)
        ax.axvline(0, color='#555b63', linestyle='--', linewidth=1)
        ax.set_title(title, loc='left', fontweight='bold')
        ax.set_xlabel('Instruction minus Direct (percentage points)')
        ax.set_yticks(y, [display[m] for m in models])
        ax.invert_yaxis()
        ax.grid(axis='x', color=GRID, alpha=.65)
        ax.set_axisbelow(True)
    fig.suptitle('Prompt effects with paired 95% bootstrap intervals',
                 fontsize=15, fontweight='bold')
    fig.savefig(REPORT / 'five-model-prompt-effects.png', dpi=200, bbox_inches='tight')
    plt.close(fig)


def precision_recall_chart():
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5), sharey=True, constrained_layout=True)
    y = np.arange(len(models)); height = .34
    for ax, prompt in zip(axes, ['Direct', 'Instruction']):
        precision = np.array([conditions[(m,prompt)]['metrics']['precision']*100 for m in models])
        recall = np.array([conditions[(m,prompt)]['metrics']['recall']*100 for m in models])
        ax.barh(y-height/2, precision, height, color='#5b9279', label='Precision')
        ax.barh(y+height/2, recall, height, color='#8b6eaa', label='Recall')
        ax.set(xlim=(0,100), xlabel='Score (%)', title=prompt)
        ax.set_yticks(y, [display[m] for m in models]); ax.invert_yaxis()
        ax.grid(axis='x', color=GRID, alpha=.65); ax.set_axisbelow(True)
        for row, value in enumerate(precision): ax.text(value+1,row-height/2,f'{value:.0f}',va='center',fontsize=8)
        for row, value in enumerate(recall): ax.text(value+1,row+height/2,f'{value:.0f}',va='center',fontsize=8)
    axes[1].legend(loc='lower right', frameon=False)
    fig.suptitle('Why F1 changed: precision fell while recall rose', fontsize=15, fontweight='bold')
    fig.savefig(REPORT / 'five-model-precision-recall.png', dpi=200, bbox_inches='tight')
    plt.close(fig)


comparison_chart()
effects_chart()
precision_recall_chart()
print('Created five-model results charts.')
