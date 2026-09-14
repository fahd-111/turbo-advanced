"""Count tracked source files, excluding generated API clients and declarations."""

import subprocess
from pathlib import Path

SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".css", ".sh"}


def is_source_file(path):
    return (
        path.suffix in SOURCE_SUFFIXES
        and not path.name.endswith(".d.ts")
        and "frontend/packages/types/api" not in path.as_posix()
        and not {"node_modules", ".next", ".venv"}.intersection(path.parts)
    )


def report_metrics():
    tracked = subprocess.check_output(["git", "ls-files", "-z"], text=True).split("\0")
    paths = [
        Path(name)
        for name in tracked
        if name and is_source_file(Path(name)) and Path(name).is_file()
    ]
    line_count = sum(
        len(path.read_text(errors="replace").splitlines()) for path in paths
    )
    print(
        f"INFO: Tracked source: {len(paths)} files, {line_count} lines (including blanks/comments)"
    )
    print(
        "INFO: "
        + ", ".join(
            f"{suffix}: {sum(path.suffix == suffix for path in paths)} files"
            for suffix in sorted({path.suffix for path in paths})
        )
    )
    components = sum(
        path.suffix == ".tsx"
        and ("components" in path.parts or "frontend/packages/ui" in path.as_posix())
        for path in paths
    )
    print(f"INFO: Component-directory TSX files: {components}")


if __name__ == "__main__":
    report_metrics()
