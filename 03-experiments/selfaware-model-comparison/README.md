# SelfAware experiment support

This folder supports `../selfaware.qmd`. The research page contains the readable
study description and charts. This folder contains only what is needed to inspect
or reproduce the experiment.

## Code

- `run_experiment.py` selects the frozen sample and collects model responses.
- `analyze_results.py` applies the original uncertainty detector and calculates
  paired bootstrap intervals.
- `create_results_charts.py` creates the five-model result figures.
- `create_paper_comparison.py` recreates the published comparison values beside
  our Instruction results.
- `test_experiment.py` checks sampling, outcome calculations and run safeguards.

## Configurations and results

- `config-original.json` defines DeepSeek V4 Pro, Qwen3.7 Plus and Claude Sonnet
  4.6.
- `config-extension.json` defines Kimi K3 and Qwen3.7 Max.
- `report/results.json` contains the final five-model scores and paired effects.
- `report/paper-comparison-values.json` records values transcribed from Figures
  3 and 6 of Yin et al. (2023).
- `report/*.png` are the figures embedded in the Quarto page.

The ignored `runs/` folder contains raw responses, frozen manifests, logs and
per-question scores. API keys are never stored here.

## Rebuild charts

From the notebook root:

```powershell
& ../SelfAware/.venv/Scripts/python.exe 03-experiments/selfaware-model-comparison/create_results_charts.py
& ../SelfAware/.venv/Scripts/python.exe 03-experiments/selfaware-model-comparison/create_paper_comparison.py
quarto render 03-experiments/selfaware.qmd --to html
```

## Test

```powershell
& ../SelfAware/.venv/Scripts/python.exe -m unittest discover -s 03-experiments/selfaware-model-comparison -p test_experiment.py -v
```
