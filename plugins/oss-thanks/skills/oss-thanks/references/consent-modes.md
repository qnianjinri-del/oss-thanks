# Consent Modes

OSS Thanks supports two saved preferences.

`auto-star` is the main path. When the agent detects a GitHub repository, the tool records it and immediately tries to star it from the user's GitHub account.

`review` records repositories first and waits until the end of the task for user approval.

Ask the user once, then save the preference:

```bash
python3 scripts/oss_thanks.py setup
```

For non-interactive setup after the user chooses:

```bash
python3 scripts/oss_thanks.py setup --mode auto-star
python3 scripts/oss_thanks.py setup --mode review
```

Use `OSS_THANKS_AUTO_STAR=1` only in environments where the user has already authorized automatic stars.
