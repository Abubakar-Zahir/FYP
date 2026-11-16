# ml

Plain Python ML code. It takes explicit inputs and returns typed outputs, so the same code runs in notebooks and workers.

It must not import `fastapi`, `celery`, `sqlalchemy` or anything from `apps/`. `tests/test_boundaries.py` enforces this.

```
uv run pytest ml
```

## Comment classifier (`ml/comments/`)

| File | What |
|---|---|
| `normalise.py` | Roman Urdu spelling variants to one form (kia, kya, kyaa become kya). An Urdu speaker should extend `VARIANTS` |
| `dataset.py` | Reads a Label Studio export. Splits train and test **by reel**, deterministically |
| `models.py` | `CharNgramClassifier` (main CPU model) and `EnglishOnlyBaseline` |
| `zero_shot.py` | The LLM zero-shot baseline: the label guideline as a prompt |
| `evaluate.py` | Macro F1 with a 95% bootstrap interval, F1 per label, confusion matrix |
| `onnx_model.py` | Runs the XLM-R model from `notebooks/comment_classifier_xlmr.ipynb` on CPU (`nlp` group) |

```
uv run python -m ml.comments.train data/labels/comments.json --out data/models/comments
PYTHONPATH=apps/api:. uv run python apps/api/scripts/evaluate_zero_shot.py data/labels/comments.json
```

All three use the same held-out split, so their numbers can go in one table. The target is that the main model beats both baselines on macro F1 (prd.md Member C acceptance 1).
