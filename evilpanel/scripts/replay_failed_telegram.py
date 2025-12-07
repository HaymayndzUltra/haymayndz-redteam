import json
import os
import time
import argparse
import sys

from evilpanel.core.telegram_notifier import notifier, FAILED_LOG


def main(path):
    if not notifier.enabled:
        print("Notifier is disabled. Enable via telegram.yaml or env.")
        sys.exit(1)
    if not os.path.exists(path):
        print(f"No failed log at {path}")
        return
    sent = 0
    failed = 0
    with open(path, "r") as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except Exception:
            failed += 1
            continue
        notifier.enqueue(event)
        sent += 1
        time.sleep(0.6)
    print(f"Replayed queued events: {sent}, failed parses: {failed}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default=FAILED_LOG, help="Path to failed jsonl log")
    args = parser.parse_args()
    main(args.file)

