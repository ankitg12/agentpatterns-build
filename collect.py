#!/usr/bin/env python3
"""
Collect .md files from agentpatterns-ai/website in nav order via .pages files.
Outputs pandoc-defaults.yaml with all paths and metadata.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import yaml
import glob


def _find_eisvogel() -> str:
    """Auto-detect eisvogel.latex in pandoc user data dir."""
    pandoc_dir = Path.home() / "AppData" / "Roaming" / "pandoc" / "templates"
    matches = sorted(pandoc_dir.glob("**/eisvogel.latex"))
    if matches:
        return str(matches[-1])
    # XDG fallback (Linux/macOS)
    xdg = Path.home() / ".local" / "share" / "pandoc" / "templates"
    matches = sorted(xdg.glob("**/eisvogel.latex"))
    if matches:
        return str(matches[-1])
    return "eisvogel.latex"  # assume on PATH


# Section order as specified
SECTION_ORDER = [
    "context-engineering",
    "instructions",
    "agent-design",
    "multi-agent",
    "tool-engineering",
    "verification",
    "anti-patterns",
    "security",
    "observability",
    "human",
    "fallacies",
    "code-review",
    "frameworks",
    "workflows",
    "standards",
    "emerging",
]

# Root files to prepend
ROOT_FILES = ["index.md", "concepts.md", "patterns.md"]


def parse_pages_nav(nav_list: List[Any], section_dir: Path) -> List[str]:
    """
    Parse .pages nav list. Handles:
    - Simple file entries: 'file.md'
    - Nested dicts: {'Category': [files]}
    - Wildcard '...' - insert remaining files alphabetically
    """
    files = []
    remaining = None

    for item in nav_list:
        if isinstance(item, str):
            if item == "...":
                # Placeholder for remaining files
                remaining = True
            else:
                # Simple file entry
                full_path = section_dir / item
                if full_path.exists():
                    files.append(str(full_path))
        elif isinstance(item, dict):
            # Nested category - extract files recursively
            for category_name, subitems in item.items():
                if isinstance(subitems, list):
                    for subitem in subitems:
                        if isinstance(subitem, str):
                            full_path = section_dir / subitem
                            if full_path.exists():
                                files.append(str(full_path))
                        elif isinstance(subitem, dict):
                            # Deeper nesting
                            for _, subsubitems in subitem.items():
                                if isinstance(subsubitems, list):
                                    for item2 in subsubitems:
                                        if isinstance(item2, str):
                                            full_path = section_dir / item2
                                            if full_path.exists():
                                                files.append(str(full_path))

    # If wildcard was found, add remaining .md files alphabetically
    if remaining:
        explicit_files = set(Path(f).name for f in files)
        all_md_files = sorted(f.name for f in section_dir.glob("*.md"))
        for md_file in all_md_files:
            if md_file not in explicit_files:
                full_path = section_dir / md_file
                if full_path.exists():
                    files.append(str(full_path))

    return files


def collect_section_files(section_name: str, repo_path: Path) -> List[str]:
    """
    Collect .md files from a section directory using its .pages file.
    """
    section_dir = repo_path / section_name
    pages_file = section_dir / ".pages"

    if not section_dir.exists():
        return []

    files = []

    # Load .pages if it exists
    if pages_file.exists():
        try:
            with open(pages_file) as f:
                pages_data = yaml.safe_load(f) or {}
            nav = pages_data.get("nav", [])
            if nav:
                files = parse_pages_nav(nav, section_dir)
        except Exception as e:
            print(f"Warning: Failed to parse {pages_file}: {e}", file=sys.stderr)

    # If no .pages or no nav, fallback to all .md files sorted
    if not files:
        files = sorted(str(f) for f in section_dir.glob("*.md"))

    return files


def collect_all_files(repo_path: Path) -> Dict[str, List[str]]:
    """
    Collect all .md files from all sections in nav order.
    Returns dict: {section_name: [absolute_paths]}
    """
    all_files = {}

    for section in SECTION_ORDER:
        files = collect_section_files(section, repo_path)
        all_files[section] = files

    return all_files


def prepend_root_files(repo_path: Path) -> List[str]:
    """
    Prepend root files (index.md, concepts.md, patterns.md) if they exist.
    """
    root_files = []
    for fname in ROOT_FILES:
        fpath = repo_path / fname
        if fpath.exists():
            root_files.append(str(fpath))
    return root_files


def write_pandoc_defaults(
    output_path: Path,
    metadata_path: Path,
    template_path: Path,
    pdf_output: Path,
    root_files: List[str],
    section_files: Dict[str, List[str]],
) -> int:
    """
    Write pandoc-defaults.yaml with all input files and options.
    Returns total file count.
    """
    input_files = root_files.copy()
    total_count = len(root_files)

    # Flatten section files and print counts
    for section in SECTION_ORDER:
        files = section_files.get(section, [])
        input_files.extend(files)
        count = len(files)
        total_count += count
        if count > 0:
            print(f"{section}: {count} files")

    print(f"Total: {total_count} files\n")

    # Build defaults dict
    defaults = {
        "defaults": {
            "input-files": input_files,
            "metadata-file": str(metadata_path),
            "from": "markdown+raw_html",
            "to": "pdf",
            "pdf-engine": "xelatex",
            "template": str(template_path),
            "toc": True,
            "toc-depth": 2,
            "number-sections": True,
            "top-level-division": "chapter",
            "highlight-style": "tango",
            "file-scope": True,
            "output": str(pdf_output),
        }
    }

    # Write YAML
    with open(output_path, "w") as f:
        yaml.dump(defaults, f, default_flow_style=False, sort_keys=False)

    print(f"Wrote: {output_path}")
    return total_count


def main():
    parser = argparse.ArgumentParser(
        description="Collect .md files from agentpatterns-ai/website in nav order"
    )
    parser.add_argument(
            "--repo",
            default=str(Path.home() / "repos" / "github.com" / "agentpatterns-ai" / "website"),
            help="Path to cloned agentpatterns-ai/website repo",
        )
    parser.add_argument(
        "--out",
        default=".",
        help="Output directory for pandoc-defaults.yaml (default: current dir)",
    )
    parser.add_argument(
            "--pdf",
            default=str(Path.home() / "Downloads" / "agentpatterns-cookbook.pdf"),
            help="Output PDF path",
        )
    parser.add_argument(
            "--template",
            default=_find_eisvogel(),
            help="Path to Eisvogel template (auto-detected from pandoc user dir)",
        )
    parser.add_argument(
        "--metadata",
        default="metadata.yaml",
        help="Metadata file name (default: metadata.yaml)",
    )

    args = parser.parse_args()

    # Resolve paths
    repo_path = Path(args.repo).resolve()
    out_dir = Path(args.out).resolve()
    template_path = Path(args.template).resolve()
    pdf_path = Path(args.pdf).resolve()
    metadata_path = out_dir / args.metadata

    # Validate
    if not repo_path.exists():
        print(f"Error: Repo not found: {repo_path}", file=sys.stderr)
        sys.exit(1)

    if not template_path.exists():
        print(f"Error: Template not found: {template_path}", file=sys.stderr)
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)

    # Collect files
    root_files = prepend_root_files(repo_path)
    section_files = collect_all_files(repo_path)

    # Write defaults
    defaults_path = out_dir / "pandoc-defaults.yaml"
    total = write_pandoc_defaults(
        defaults_path, metadata_path, template_path, pdf_path, root_files, section_files
    )

    print(f"{total} files ready for pandoc")


if __name__ == "__main__":
    main()
