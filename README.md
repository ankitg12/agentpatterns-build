# Agent Patterns PDF Build

Build an O'Reilly-style PDF from the agentpatterns-ai/website repository.

## Requirements

- Python 3.10+, pyyaml (`pip install pyyaml`)
- pandoc 3.0+
- xelatex (MiKTeX on Windows: `scoop install miktex`)
- Eisvogel template (auto-detected from pandoc user dir)
- mmdc / mermaid-cli (`npm install -g @mermaid-js/mermaid-cli`)

## Print the book

```powershell
cd path/to/agentpatterns-build
python build.py
# → ~/Downloads/agentpatterns-encyclopedia.pdf  (~10 min for full corpus, ~234 pages/section)
```

Single section (fast, for testing):
```powershell
python build.py --sections anti-patterns
```

Typst engine (faster, no colored headings):
```powershell
python build.py --engine typst
```

## Update content then reprint

```powershell
cd path/to/agentpatterns-ai/website
git pull
cd path/to/agentpatterns-build
python build.py
```

## Options

| Flag | Default | Notes |
|------|---------|-------|
| `--repo` | `~/repos/.../agentpatterns-ai/website` | Source repo |
| `--pdf` | `~/Downloads/agentpatterns-encyclopedia.pdf` | Output path |
| `--sections` | all 16 | Comma-separated subset |
| `--engine` | `xelatex` | `xelatex` (colored headings) or `typst` (faster) |

## Customization

- **Colors / fonts**: `metadata.yaml`
- **Section order**: `collect.py` → `SECTION_ORDER`
- **Mermaid cache**: `mermaid-cache/` (auto-created, safe to delete to force re-render)
