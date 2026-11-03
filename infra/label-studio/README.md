# Label Studio

Self-hosted labelling for the comment classifier. Rules are in `docs/label-guideline.md`.

## Start it

```
uvx --python 3.12 --from label-studio==1.23.2 label-studio start --port 8080
```

Or with Docker (`docker compose -f infra/label-studio/docker-compose.yml up`).

Then open http://localhost:8080 and create an account.

## Set up the project

1. Create a project called **Comment labels**.
2. Under **Settings > Labeling Interface > Code**, paste `label_config.xml`.
3. Import `sample_comments.csv` and do the calibration round. These comments are made up for training. Real comments never go in git.
4. Under **Settings > Annotation**, give the shared subset 2 labellers, and hide other people's answers.

Hotkeys: `1` to `6` for the label, `q` `w` `e` `r` `t` for language, `u` for unsure.

## Measure agreement

Export as JSON from Label Studio, then:

```
PYTHONPATH=. uv run python spikes/labelling/report.py export.json <user_id_1> <user_id_2>
```

## Sharing with the team

This setup is reachable only from your own machine. To share it, host it on the VPS behind HTTPS with signup closed, because real comments will be inside. Back up the data volume, since labels are weeks of work.
