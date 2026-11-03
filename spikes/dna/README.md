# DNA and Whisper spike (P0-10, P0-11)

**Status: code ready and checked end to end on one test clip, not yet run on real reels.** These tasks are done only when the results tables below are filled in.

Questions: can we pull useful signals from a reel on CPU, and how well does Whisper handle Urdu?

## What it does

`extract.py` turns each reel into a `ReelSignals` JSON (`ml/dna/schema.py`): transcript with timings, cut times, pacing, the speech in the first 3 seconds, and one keyframe per scene.

`whisper_wer.py` reports word error rate per language group.

## What we checked

On one synthetic 11 s video with Whisper `tiny`, on CPU:

| Check | Expected | Got |
|---|---|---|
| Cut times | 4.0 s, 8.0 s | 4.0 s, 8.0 s |
| Keyframes | 3 | 3 |
| Transcript of the public JFK sample | 22 words | 0 errors |
| Processing time | NFR-1: under 2 min for 60 s | 0.8 s, not comparable to a real reel |

This shows the pipeline runs. It says nothing about accuracy on real reels or on Urdu.

## Things we learned

1. **Pin `av<18` until `faster-whisper` catches up.** With PyAV 19, `faster-whisper` 1.2.1 crashes with `unexpected keyword argument 'metadata_errors'`. The scripts pin it already.
2. **Some real cuts can be missed.** Our first test video changed only hue between scenes, and the default threshold of 27 found 0 of its 2 cuts. Compare the detected cuts with a few reels by eye and tune `--threshold`.
3. **"Roman Urdu" is a writing system, not a way of speaking.** Whisper with `language=ur` writes Urdu script, so a Roman Urdu reference will score near 100% WER without meaning anything. Measure Urdu speech against Urdu-script references first. Roman Urdu captions then need a transliteration step, and that step should be scored separately.

## Not covered yet

- **Hook type, beats and CTA.** These need the LLM structuring step into `DnaRecord`, which waits on the LLM provider decision (`progress.md`, open question 2). Gate 0 asks for a DNA record, so this must be added or the gate adjusted.
- **On-screen text.** Keyframes are saved for OCR or a vision LLM, and neither is wired up.

## Run it

Run from the repo root. Put reels under `data/`, which git ignores. Never commit real videos.

```
PYTHONPATH=. uv run spikes/dna/extract.py data/reels --model small
PYTHONPATH=. uv run spikes/dna/whisper_wer.py data/wer/manifest.csv --model small
```

Paths in the manifest are relative to the manifest. Use 10 or more clips per group, with references typed by a person who didn't see Whisper's output:

```
audio_path,group,whisper_language,reference
clips/ur_01.mp3,urdu,ur,"یہ جگہ بہت اچھی ہے"
clips/en_01.mp3,english,en,"This place is really good"
clips/mix_01.mp3,mixed,,"Yeh jagah really good hai"
```

Leave `whisper_language` empty to auto-detect. The first run downloads the model. Run `tiny` and `small` both, so the report has a baseline (`rules.md` 7.3).

## Results (fill in after running)

| P0-10 check | Result |
|---|---|
| Reels processed (target 20) | |
| Median seconds per 60 s reel, and machine used | |
| Cuts correct on 5 reels checked by eye | |
| Threshold used | |

| P0-11 group | Model | Clips | Reference words | WER |
|---|---|---|---|---|
| Urdu | | | | |
| English | | | | |
| Mixed | | | | |
