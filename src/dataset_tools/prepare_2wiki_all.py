from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


DEFAULT_SPLITS = ("train", "dev", "test")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate sample-preserving JSONL exports for all 2Wiki splits."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/raw/2wiki"),
        help="Directory containing train.json, dev.json, and test.json.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("data/processed/2wiki"),
        help="Root output directory for the processed 2Wiki exports.",
    )
    parser.add_argument(
        "--splits",
        nargs="+",
        default=list(DEFAULT_SPLITS),
        help="Splits to export as sample-preserving files.",
    )
    return parser.parse_args()


def run_command(cmd: list[str], cwd: Path) -> None:
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> None:
    args = parse_args()
    project_root = Path(__file__).resolve().parents[2]
    output_root = (project_root / args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    prepare_samples_script = (
        project_root / "src" / "dataset_tools" / "prepare_2wiki_samples.py"
    )
    samples_output_dir = output_root / "samples"
    samples_output_dir.mkdir(parents=True, exist_ok=True)

    for split in args.splits:
        input_path = (project_root / args.input_dir / f"{split}.json").resolve()
        run_command(
            [
                sys.executable,
                str(prepare_samples_script),
                "--input",
                str(input_path),
                "--output-dir",
                str(samples_output_dir),
            ],
            cwd=project_root,
        )

    print(f"Finished writing processed 2Wiki outputs to {output_root}")


if __name__ == "__main__":
    main()
