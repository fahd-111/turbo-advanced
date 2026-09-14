"""Keep terminal diagnostics short; the original output stays in the log."""

import re
import sys
from pathlib import Path

MAX_DIAGNOSTICS = 6
MAX_LINE_LENGTH = 240
ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
DIAGNOSTIC = re.compile(
    r"error|warn|fail|vulnerabil|severity|would reformat|fixing |^INFO:|"
    r"\b[EIFW]\d{3}\b|\.(?:py|tsx?|jsx?):\d+",
    re.IGNORECASE,
)


def summarize_output(output, failed):
    lines = tuple(
        dict.fromkeys(
            " ".join(line.replace("│", " ").split())
            for line in ANSI_ESCAPE.sub("", output).splitlines()
            if line.strip()
        )
    )
    diagnostics = [line for line in lines if DIAGNOSTIC.search(line)]
    if not diagnostics and failed:
        diagnostics = list(lines[-MAX_DIAGNOSTICS:])
    return "\n".join(
        "  " + line[:MAX_LINE_LENGTH] for line in diagnostics[:MAX_DIAGNOSTICS]
    )


if __name__ == "__main__":
    summary = summarize_output(
        Path(sys.argv[1]).read_text(errors="replace"), sys.argv[2] != "0"
    )
    if summary:
        print(summary)
