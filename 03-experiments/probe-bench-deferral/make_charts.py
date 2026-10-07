"""Charts for the Probe Bench deferral experiment. Reads results.json (written by
analyse.py --json in the 02-defferal repo) and writes PNGs next to this file."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ALL = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
runs = [r for r in ALL if r.get('version', 'v4') == 'v4']   # the original 4-penalty design

TRIVIA = '#1baf7a'   # third validated categorical slot, for the trivia points
MODELS = {
    'llama-3.2-3b-instruct': 'Llama 3.2 3B',
    'llama-3.1-8b-instruct': 'Llama 3.1 8B',
    'llama-3.3-70b-instruct': 'Llama 3.3 70B',
    'qwen-2.5-7b-instruct': 'Qwen 2.5 7B',
    'qwen3-30b-a3b-instruct-2507': 'Qwen3 30B',
    'mistral-nemo': 'Mistral Nemo 12B',
    'gpt-4o-mini': 'GPT-4o mini',
    'gemini-2.5-flash-lite': 'Gemini 2.5 Flash Lite',
}
CONDITIONS = {
    'baseline': 'Baseline',
    'answer_first': 'Options listed in the other order',
    'permission': 'Told: asking for help is expected',
    'compute_ev': 'Told: work out the expected score first',
    'show_history': 'Shown its own 10 earlier answers',
    'real_user': 'Told: a customer is waiting',
    'decide_then_confidence': 'Decision first, confidence after',
    'separate_confidence': 'Confidence asked in a separate call',
    'rename_action': 'Help renamed to "flag as uncertain"',
}

# Validated two-colour palette (blue / orange), ink and grid tokens.
STRONG, WEAK = '#2a78d6', '#eb6834'
PEN_LOW, PEN_HIGH = '#86b6ef', '#184f95'   # one hue, light to dark: small to large penalty
INK, INK2, MUTED, GRID, AXIS = '#0b0b0b', '#52514e', '#898781', '#e1e0d9', '#c3c2b7'
MIN_WEAK = 10   # fewer weak problems than this: the row is flagged, not trusted
MORE = lambda d: f'gap {d:+.0f} pts'                                   # help-asking, weak minus strong
LOWER = lambda d: 'same' if round(d) == 0 else f'{abs(d):.0f} {"lower" if d < 0 else "higher"}'   # confidence on weak

plt.rcParams.update({
    'font.family': ['Segoe UI', 'DejaVu Sans'], 'font.size': 10.5,
    'text.color': INK, 'axes.labelcolor': INK2, 'xtick.color': MUTED, 'ytick.color': INK,
    'axes.edgecolor': AXIS, 'figure.facecolor': 'white', 'axes.facecolor': 'white',
})


def style(ax):
    for side in ('top', 'right', 'left'):
        ax.spines[side].set_visible(False)
    ax.grid(axis='x', color=GRID, linewidth=1)
    ax.set_axisbelow(True)
    ax.tick_params(length=0, pad=9)


def dumbbell(ax, rows, weak_key, strong_key, scale, label):
    """One row per item: strong-problem value (blue dot) and weak-problem value
    (orange triangle), joined by a line, with the difference written at the end."""
    for y, r in enumerate(rows):
        w, s = r[weak_key], r[strong_key]
        if w is None or s is None:
            continue
        w, s = w * scale, s * scale
        ax.plot([s, w], [y, y], color=AXIS, linewidth=2, zorder=1, solid_capstyle='round')
        ax.scatter(s, y, s=95, color=STRONG, edgecolor='white', linewidth=1.5, zorder=3, clip_on=False)
        ax.scatter(w, y, s=105, color=WEAK, marker='^', edgecolor='white', linewidth=1.5, zorder=4, clip_on=False)
        ax.text(max(w, s) + 3, y, label(w - s), va='center', ha='left', color=INK2, fontsize=9.5)
    ax.set_ylim(len(rows) - 0.4, -0.6)
    ax.set_xlim(0, 100)
    style(ax)


def legend(fig, y):
    handles = [
        plt.Line2D([], [], marker='^', linestyle='', color=WEAK, markersize=9, label='Weak problems = ones this model usually gets wrong'),
        plt.Line2D([], [], marker='o', linestyle='', color=STRONG, markersize=9, label='Strong problems = ones this model usually gets right'),
    ]
    fig.legend(handles=handles, loc='upper left', bbox_to_anchor=(0.01, y), ncol=2, frameon=False,
               fontsize=10, handletextpad=0.3, columnspacing=1.6)


def row_label(name, r):
    n = r['weak_problems']
    note = f'{n} weak problems' if n >= MIN_WEAK else f'only {n} weak problems'
    return f'{name}\n{note}'


def model_chart(dataset, filename, title, subtitle):
    rows = [r for r in runs if r['dataset'] == dataset and r['condition'] == 'baseline' and r['model'] in MODELS]
    if not rows:
        return
    rows.sort(key=lambda r: -(r['gap'][0] if r['gap'] else -1))
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 1.6 + 0.62 * len(rows)), sharey=True)
    dumbbell(axes[0], rows, 'defer_weak', 'defer_strong', 100, MORE)
    dumbbell(axes[1], rows, 'conf_weak', 'conf_strong', 1, LOWER)
    axes[0].set_title('How often it asks for help', loc='left', fontweight='bold', fontsize=11)
    axes[1].set_title('How confident it says it is', loc='left', fontweight='bold', fontsize=11)
    axes[0].set_xlabel('Share of decisions where it asked for help (%)')
    axes[1].set_xlabel('Average stated confidence (0 to 100)')
    axes[0].set_yticks(range(len(rows)), [row_label(MODELS[r['model']], r) for r in rows])
    for tick, r in zip(axes[0].get_yticklabels(), rows):
        tick.set_color(INK if r['weak_problems'] >= MIN_WEAK else MUTED)
    top = 1 - 0.3 / fig.get_figheight()
    fig.suptitle(title, x=0.01, y=top, ha='left', fontsize=14, fontweight='bold')
    fig.text(0.01, top - 0.42 / fig.get_figheight(), subtitle, ha='left', va='top', color=INK2, fontsize=10)
    legend(fig, top - 0.62 / fig.get_figheight())
    fig.tight_layout(rect=(0, 0, 1, top - 0.78 / fig.get_figheight()))
    fig.savefig(HERE / filename, dpi=200, bbox_inches='tight')
    plt.close(fig)


def condition_chart():
    rows = {r['condition']: r for r in runs
            if r['dataset'] == 'gsm8k' and r['model'] == 'llama-3.1-8b-instruct'}
    rows = [rows[c] for c in CONDITIONS if c in rows]
    fig, ax = plt.subplots(figsize=(9.5, 1.6 + 0.5 * len(rows)))
    dumbbell(ax, rows, 'defer_weak', 'defer_strong', 100, MORE)
    ax.set_yticks(range(len(rows)), [CONDITIONS[r['condition']] for r in rows])
    ax.set_xlabel('Share of decisions where it asked for help (%)')
    top = 1 - 0.3 / fig.get_figheight()
    fig.suptitle('Changing the prompt changes how much Llama 8B asks, not how well it aims',
                 x=0.01, y=top, ha='left', fontsize=14, fontweight='bold')
    fig.text(0.01, top - 0.42 / fig.get_figheight(),
             'Llama 3.1 8B on GSM8K, 25 weak and 25 strong problems, 600 decisions per row. '
             'Each row changes one thing in the prompt.\n'
             'Gap = how much more it asks on weak problems than on strong ones. A bigger gap means better aim.', ha='left', va='top', color=INK2, fontsize=10)
    legend(fig, top - 0.84 / fig.get_figheight())
    fig.tight_layout(rect=(0, 0, 1, top - 1.0 / fig.get_figheight()))
    fig.savefig(HERE / 'conditions-llama-8b.png', dpi=200, bbox_inches='tight')
    plt.close(fig)


def penalty_chart():
    """Help-asking on weak problems at the smallest and the largest penalty.
    Two marks close together = the penalty made no difference."""
    rows = [r for r in runs if r['condition'] == 'baseline' and r['model'] in MODELS
            and r['weak_problems'] >= MIN_WEAK]
    change = lambda r: r['by_penalty']['64']['defer_weak'] - r['by_penalty']['1']['defer_weak']
    rows.sort(key=lambda r: (r['dataset'], -change(r)))
    fig, ax = plt.subplots(figsize=(9.5, 1.6 + 0.5 * len(rows)))
    for y, r in enumerate(rows):
        low, high = r['by_penalty']['1']['defer_weak'] * 100, r['by_penalty']['64']['defer_weak'] * 100
        ax.plot([low, high], [y, y], color=AXIS, linewidth=2, zorder=1, solid_capstyle='round')
        ax.scatter(low, y, s=95, color=PEN_LOW, edgecolor='white', linewidth=1.5, zorder=3, clip_on=False)
        ax.scatter(high, y, s=85, color=PEN_HIGH, marker='D', edgecolor='white', linewidth=1.5, zorder=4, clip_on=False)
        ax.text(max(low, high) + 3, y, f'{high - low:+.0f} pts', va='center', ha='left', color=INK2, fontsize=9.5)
    names = [MODELS[r['model']] + ('' if r['dataset'] == 'gsm8k' else '\non harder problems') for r in rows]
    ax.set_yticks(range(len(rows)), names)
    ax.set_ylim(len(rows) - 0.4, -0.6)
    ax.set_xlim(0, 100)
    ax.set_xlabel('Share of weak-problem decisions where it asked for help (%)')
    style(ax)
    top = 1 - 0.3 / fig.get_figheight()
    fig.suptitle('Making a wrong answer 64 times more costly barely changes how often models ask',
                 x=0.01, y=top, ha='left', fontsize=14, fontweight='bold')
    fig.text(0.01, top - 0.42 / fig.get_figheight(),
             'How often each model asks for help on its weak problems. '
             'If the two marks sit close together, the penalty made no difference.',
             ha='left', va='top', color=INK2, fontsize=10)
    handles = [
        plt.Line2D([], [], marker='o', linestyle='', color=PEN_LOW, markersize=9, label='Penalty 1: a wrong answer costs 1 point'),
        plt.Line2D([], [], marker='D', linestyle='', color=PEN_HIGH, markersize=8, label='Penalty 64: a wrong answer costs 64 points'),
    ]
    fig.legend(handles=handles, loc='upper left', bbox_to_anchor=(0.01, top - 0.62 / fig.get_figheight()),
               ncol=2, frameon=False, fontsize=10, handletextpad=0.3, columnspacing=1.6)
    fig.tight_layout(rect=(0, 0, 1, top - 0.78 / fig.get_figheight()))
    fig.savefig(HERE / 'penalty-effect.png', dpi=200, bbox_inches='tight')
    plt.close(fig)


def payoff_chart():
    """Score per decision at penalty 64: what each model got, against always answering,
    always asking, and an oracle that asks exactly when its ability says to."""
    rows = [r for r in runs if r['condition'] == 'baseline' and r['model'] in MODELS
            and r['weak_problems'] >= MIN_WEAK]
    rows.sort(key=lambda r: (r['dataset'], -r['payoff']['64']['model']))
    fig, ax = plt.subplots(figsize=(9.5, 1.8 + 0.5 * len(rows)))
    for y, r in enumerate(rows):
        p = r['payoff']['64']
        ax.plot([p['always_answer'], p['model']], [y, y], color=AXIS, linewidth=2, zorder=1, solid_capstyle='round')
        ax.scatter(p['always_answer'], y, s=80, facecolor='white', edgecolor=MUTED, linewidth=1.5, zorder=3, clip_on=False)
        ax.scatter(p['model'], y, s=105, color=WEAK, marker='^', edgecolor='white', linewidth=1.5, zorder=4, clip_on=False)
        ax.scatter(p['oracle'], y, s=95, color=STRONG, edgecolor='white', linewidth=1.5, zorder=4, clip_on=False)
        ax.text(p['model'], y - 0.3, f"{p['model']:.1f}", ha='center', va='bottom', color=INK2, fontsize=9)
    ax.axvline(-0.2, color=INK2, linewidth=1, zorder=2)
    ax.text(-0.2, -0.75, 'always ask: -0.2', ha='right', va='bottom', color=INK2, fontsize=9.5)
    names = [MODELS[r['model']] + ('' if r['dataset'] == 'gsm8k' else '\non harder problems') for r in rows]
    ax.set_yticks(range(len(rows)), names)
    ax.set_ylim(len(rows) - 0.4, -0.9)
    ax.set_xlim(-40, 3)
    ax.set_xlabel('Average score per decision at penalty 64 (right answer +1, wrong answer -64, asking for help -0.2)')
    style(ax)
    top = 1 - 0.3 / fig.get_figheight()
    fig.suptitle('At penalty 64 every model would have scored higher by always asking for help',
                 x=0.01, y=top, ha='left', fontsize=14, fontweight='bold')
    fig.text(0.01, top - 0.42 / fig.get_figheight(),
             'What each model scored, against two fixed policies on the same problems. '
             'Always asking scores -0.2 on every problem, the vertical line.',
             ha='left', va='top', color=INK2, fontsize=10)
    handles = [
        plt.Line2D([], [], marker='o', linestyle='', markerfacecolor='white', markeredgecolor=MUTED, markersize=9, label='If it always answered'),
        plt.Line2D([], [], marker='^', linestyle='', color=WEAK, markersize=9, label='What the model actually scored'),
        plt.Line2D([], [], marker='o', linestyle='', color=STRONG, markersize=9, label='Oracle: asks exactly when its ability says to'),
    ]
    fig.legend(handles=handles, loc='upper left', bbox_to_anchor=(0.01, top - 0.62 / fig.get_figheight()),
               ncol=3, frameon=False, fontsize=10, handletextpad=0.3, columnspacing=1.4)
    fig.tight_layout(rect=(0, 0, 1, top - 0.78 / fig.get_figheight()))
    fig.savefig(HERE / 'payoff-penalty-64.png', dpi=200, bbox_inches='tight')
    plt.close(fig)


def scatter_chart():
    """One point per model and task (baseline runs with 10+ weak problems, any version):
    how far its stated confidence drops on weak problems against how much more it asks."""
    pts = [r for r in ALL if r['condition'] == 'baseline' and r['model'] in MODELS
           and r['weak_problems'] >= MIN_WEAK and r['conf_weak'] is not None]
    colour = {'gsm8k': STRONG, 'gsmhard': WEAK, 'trivia': TRIVIA}
    marker = {'gsm8k': 'o', 'gsmhard': 'D', 'trivia': '^'}
    short = {'llama-3.2-3b-instruct': 'Llama 3B', 'llama-3.1-8b-instruct': 'Llama 8B',
             'llama-3.3-70b-instruct': 'Llama 70B', 'qwen3-30b-a3b-instruct-2507': 'Qwen3 30B',
             'mistral-nemo': 'Nemo 12B', 'gpt-4o-mini': 'GPT-4o mini', 'gemini-2.5-flash-lite': 'Gemini Lite'}
    fig, ax = plt.subplots(figsize=(8.5, 6.2))
    for r in pts:
        x, y = r['conf_strong'] - r['conf_weak'], r['gap'][0] * 100
        ax.scatter(x, y, s=110, color=colour[r['dataset']], marker=marker[r['dataset']],
                   edgecolor='white', linewidth=1.5, zorder=3)
        name = short[r['model']] + (' (100 problems)' if r.get('version') == 'v5' else '')
        if y >= 6 or r['model'] == 'llama-3.3-70b-instruct':   # the bottom-left cluster gets one shared note
            offset = (7, -13) if r['dataset'] == 'trivia' else (7, 4)   # trivia labels go below, clear of neighbours
            ax.annotate(name, (x, y), xytext=offset, textcoords='offset points', color=INK2, fontsize=9)
    ax.annotate('Nemo, GPT-4o mini (both tasks),\nGemini Lite on GSM-Hard', (2.5, 2.8), xytext=(0.6, -1.0),
                textcoords='data', color=INK2, fontsize=9, va='top')
    ax.set_xlim(-2, 32)
    ax.set_ylim(-4, 38)
    ax.set_xlabel('How much lower its stated confidence is on weak problems than on strong ones (points)')
    ax.set_ylabel('How much more it asks for help on weak problems (points)')
    style(ax)
    ax.grid(axis='y', color=GRID, linewidth=1)
    handles = [plt.Line2D([], [], marker=marker[d], linestyle='', color=colour[d], markersize=9, label=lab)
               for d, lab in [('gsm8k', 'GSM8K'), ('gsmhard', 'GSM-Hard'), ('trivia', 'TriviaQA')]]
    ax.legend(handles=handles, loc='upper left', frameon=False, fontsize=10)
    top = 1 - 0.3 / fig.get_figheight()
    fig.suptitle('Where the stated confidence drops on weak problems, the help-asking follows',
                 x=0.01, y=top, ha='left', fontsize=14, fontweight='bold')
    fig.text(0.01, top - 0.42 / fig.get_figheight(),
             'One point per model and task, baseline prompt, models with at least 10 weak problems.',
             ha='left', va='top', color=INK2, fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, top - 0.55 / fig.get_figheight()))
    fig.savefig(HERE / 'confidence-vs-asking.png', dpi=200, bbox_inches='tight')
    plt.close(fig)


model_chart('gsm8k', 'models-gsm8k.png',
            'Only some models ask for help more on the problems they are bad at',
            'Baseline prompt on GSM8K maths problems. 50 problems and 600 decisions per model. '
            'Gap = how much more it asks on weak problems than on strong ones.')
model_chart('gsmhard', 'models-gsmhard.png',
            'On harder problems the stronger models still almost never ask for help',
            'Baseline prompt on GSM-Hard (the same problems with very large numbers). 600 decisions per model. '
            'Gap = how much more it asks on weak problems than on strong ones.')
condition_chart()
penalty_chart()
payoff_chart()
scatter_chart()
print('Created Probe Bench deferral charts.')
