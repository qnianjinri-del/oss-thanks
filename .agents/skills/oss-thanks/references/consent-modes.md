# Consent Modes

`review` is the default mode. Repositories are recorded locally, and the user decides whether to star them after the task.

`auto-star` is an explicit opt-in mode. The tool may call GitHub as soon as a repository is detected, but only when the user has enabled consent with:

```bash
python3 scripts/oss_thanks.py init --mode auto-star --yes
```

For one-off commands, `--mode auto-star --yes` enables auto-star only for that invocation.

Use `OSS_THANKS_AUTO_STAR=1` only in environments where the user has already authorized automatic stars.
