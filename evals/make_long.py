#!/usr/bin/env python3
"""Generate the large fixture, preferably outside this repository."""
from pathlib import Path
import sys


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "fixtures/long-allhands.txt"
    topics = ["support routing", "release readiness", "documentation", "billing checks", "customer feedback"]
    planted = {
        0: "Asha: I'll publish the release checklist by Friday.",
        400: "Ben: I'll review the billing export. No due date was assigned.",
        800: "Chen: I'll send the support routing diagram before the next review.",
        1000: "Asha: I'll update the obsolete dashboard screenshot.",
        1200: "Divya: I'll run the keyboard navigation audit tomorrow.",
        1500: "Asha: The obsolete dashboard screenshot is updated. That task is completed.",
        1999: "Eli: I'll circulate the customer feedback digest next week.",
    }
    lines = []
    for i in range(2000):
        stamp = "[{}:{:02d}:{:02d}]".format(i * 15 // 3600, i * 15 // 60 % 60, i * 15 % 60)
        topic = topics[i % len(topics)]
        text = planted.get(i, "Host: Review {} covered {}. The discussion described existing workflows, the limits of the available observations, and the difference between a proposal and an agreed task. These background remarks introduced no assignments, dates or decisions.".format(i, topic))
        lines.append(stamp + " " + text)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    print(str(path))


if __name__ == "__main__":
    main()
