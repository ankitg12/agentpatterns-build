#!/usr/bin/env python3
"""
Build an O'Reilly-style PDF from agentpatterns-ai/website using pandoc + Eisvogel.

Uses pandoc --defaults to pass input files via YAML, avoiding Windows command-line
length limits (WinError 206) that occur when passing 700+ file paths as arguments.

Usage:
    python build.py                                  # full book
    python build.py --sections anti-patterns         # one section
    python build.py --sections "context-engineering,instructions"  # multiple
"""
import argparse
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import yaml
import collect as _collect


def _pandoc_path() -> str:
    """Return 'pandoc' — subprocess resolves it from PATH."""
    return "pandoc"

def _mmdc_path() -> str:
    """Resolve mmdc — tries PATH first, then common npm global locations."""
    import shutil
    found = shutil.which("mmdc") or shutil.which("mmdc.cmd")
    if found:
        return found
    # Windows npm global fallback
    npm_bin = Path.home() / "AppData" / "Roaming" / "npm" / "mmdc.cmd"
    if npm_bin.exists():
        return str(npm_bin)
    raise FileNotFoundError("mmdc not found. Install: npm install -g @mermaid-js/mermaid-cli")

def preprocess_mermaid(files: list, out_dir: Path) -> list:
    """Pre-render mermaid blocks via mmdc. Returns updated file list."""
    cache = out_dir / "mermaid-cache"
    cache.mkdir(exist_ok=True)
    result = []
    changed = 0
    for f in files:
        path = Path(f)
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            result.append(f)
            continue
        if "```mermaid" not in content:
            result.append(f)
            continue
        # Derive a stable output name (section/filename)
        out_md = cache / f"{path.parent.name}-{path.name}"
        ret = subprocess.run(
            [_mmdc_path(), "-i", str(path), "--outputFormat=pdf", "--pdfFit", "-o", str(out_md)],
            capture_output=True, encoding="utf-8", errors="replace",
        )
        if ret.returncode == 0 and out_md.exists():
            result.append(str(out_md))
            changed += 1
        else:
            result.append(f)  # fallback: use original
    if changed:
        print(f"Mermaid: pre-rendered {changed} file(s) via mmdc")
    return result


def main():
    parser = argparse.ArgumentParser(description="Build Agent Patterns PDF")
    parser.add_argument("--repo",     default=str(Path.home() / "repos" / "github.com" / "agentpatterns-ai" / "website"))
    parser.add_argument("--out",      default=".")
    parser.add_argument("--pdf",      default=str(Path.home() / "Downloads" / "agentpatterns-encyclopedia.pdf"))
    parser.add_argument("--sections", default=None, help="Comma-separated sections (default: all)")
    parser.add_argument("--engine",   default="xelatex", choices=["typst", "xelatex", "pdflatex"], help="PDF engine (default: xelatex)")
    args = parser.parse_args()

    repo_path = Path(args.repo).resolve()
    out_dir   = Path(args.out).resolve()
    metadata  = out_dir / "metadata.yaml"
    template  = _collect._find_eisvogel()

    if not repo_path.exists():
        sys.exit(f"Repo not found: {repo_path}")
    if not metadata.exists():
        sys.exit(f"metadata.yaml not found in {out_dir}")

    # Resolve sections
    if args.sections:
        sections = [s.strip() for s in args.sections.split(",")]
        invalid = [s for s in sections if s not in _collect.SECTION_ORDER]
        if invalid:
            sys.exit(f"Unknown sections: {invalid}\nValid: {_collect.SECTION_ORDER}")
    else:
        sections = _collect.SECTION_ORDER

    # Collect files
    root_files = _collect.prepend_root_files(repo_path) if not args.sections else []
    files = root_files + [
        f for s in sections
        for f in _collect.collect_section_files(s, repo_path)
    ]
    print(f"Sections: {sections}")
    print(f"Files:    {len(files)}")
    # Pre-render mermaid diagrams
    files = preprocess_mermaid(files, out_dir)


    # Derive output path — per-section gets its own name
    pdf = Path(args.pdf)
    if args.sections and len(sections) == 1:
        pdf = pdf.with_stem(f"agentpatterns-{sections[0]}")
    pdf = str(pdf)
    print(f"Output:   {pdf}")

    # Build pandoc defaults dict — input-files lives here, not on the CLI.
    # This is the fix for WinError 206 (Windows command-line too long with 700+ paths).
    defaults: dict = {
        "input-files": [str(f) for f in files],
        "from": "markdown",
        "to": "pdf",
        "output-file": pdf,
        "pdf-engine": args.engine,
        "table-of-contents": True,
        "toc-depth": 2,
        "number-sections": True,
        "file-scope": True,
        "citeproc": True,
        "resource-path": [str(out_dir / "mermaid-cache"), str(repo_path)],
    }

    # Build extra CLI args for things not supported in defaults file
    extra_args = []
    if args.engine != "typst":
        defaults["metadata-files"] = [str(metadata)]
        defaults["template"] = template
        defaults["top-level-division"] = "chapter"
        defaults["highlight-style"] = "tango"
        extra_args += [f"--lua-filter={out_dir / 'strip-control-chars.lua'}"]
    else:
        typst_template = str(
            Path.home() / "repos/github.com/andyburri/pandoc-typst-template/template/bergfink.typst"
        )
        defaults["template"] = typst_template
        # typst doesn't support syntax highlighting via Eisvogel

    # Write defaults to a temp file so the pandoc command line stays short
    defaults_file = Path(tempfile.mktemp(suffix=".yaml", prefix="pandoc-defaults-"))
    try:
        defaults_file.write_text(
            yaml.dump(defaults, allow_unicode=True, default_flow_style=False),
            encoding="utf-8",
        )

        start = time.time()
        result = subprocess.run(
            [_pandoc_path(), f"--defaults={defaults_file}"] + extra_args,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode != 0:
            sys.exit(f"pandoc failed:\n{result.stderr}")


        elapsed = time.time() - start
        label = f"{int(elapsed // 60)}m{int(elapsed % 60)}s"
        print(f"Done in {label} -> {pdf}")

    finally:
        defaults_file.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
