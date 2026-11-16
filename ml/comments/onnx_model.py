"""Runs the fine-tuned XLM-R comment model on CPU (notebooks/comment_classifier_xlmr.ipynb).

The notebook trains on Colab or Kaggle (CLAUDE.md hard constraint 5) and exports a folder
with `model.onnx`, `tokenizer.json` and `labels.json`. Inference needs only the optional
`nlp` dependency group (onnxruntime and tokenizers), never torch.
"""

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ml.comments.labels import CommentLabel
from ml.comments.normalise import normalise

MAX_TOKENS = 128
BATCH_SIZE = 32


class XlmrOnnxClassifier:
    def __init__(self, folder: Path) -> None:
        # Imported here so the rest of ml/comments works without the nlp group.
        import onnxruntime
        from tokenizers import Tokenizer

        self.name = f"xlmr-onnx:{folder.name}"
        self._labels = [CommentLabel(label) for label in json.loads((folder / "labels.json").read_text())]
        self._tokenizer: Any = Tokenizer.from_file(str(folder / "tokenizer.json"))
        self._tokenizer.enable_truncation(max_length=MAX_TOKENS)
        self._tokenizer.enable_padding()
        self._session: Any = onnxruntime.InferenceSession(
            str(folder / "model.onnx"), providers=["CPUExecutionProvider"]
        )
        self._inputs = {item.name for item in self._session.get_inputs()}

    def _batch(self, texts: Sequence[str]) -> list[CommentLabel]:
        import numpy

        encodings = self._tokenizer.encode_batch([normalise(text) for text in texts])
        feeds = {
            "input_ids": numpy.array([item.ids for item in encodings], dtype=numpy.int64),
            "attention_mask": numpy.array([item.attention_mask for item in encodings], dtype=numpy.int64),
        }
        logits = self._session.run(
            None, {name: value for name, value in feeds.items() if name in self._inputs}
        )[0]
        return [self._labels[int(index)] for index in logits.argmax(axis=1)]

    def predict(self, texts: Sequence[str]) -> list[CommentLabel]:
        labels: list[CommentLabel] = []
        for start in range(0, len(texts), BATCH_SIZE):
            labels += self._batch(texts[start : start + BATCH_SIZE])
        return labels
