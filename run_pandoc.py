import subprocess
from pathlib import Path

OUT  = Path('C:/Users/angaur/tmp/agentpatterns-build')
TMPL = 'C:/Users/angaur/AppData/Roaming/pandoc/templates/Eisvogel-3.4.0/eisvogel.latex'
PDF  = 'C:/Users/angaur/Downloads/agentpatterns-cookbook.pdf'
LOG  = OUT / 'pandoc.log'

files = (OUT / 'filelist.txt').read_text(encoding='utf-8').splitlines()

cmd = [
    'pandoc',
    '--metadata-file', str(OUT / 'metadata.yaml'),
    '--template', TMPL,
    '--pdf-engine', 'xelatex',
    '--toc', '--toc-depth=2',
    '--number-sections',
    '--top-level-division=chapter',
    '--highlight-style', 'tango',
    '--file-scope',
    '-o', PDF,
] + files

with open(LOG, 'w') as log:
    log.write(f'Running pandoc on {len(files)} files\n')
    log.flush()
    result = subprocess.run(cmd, stdout=log, stderr=log)
    log.write(f'\nReturn code: {result.returncode}\n')
    log.write('DONE\n' if result.returncode == 0 else 'FAILED\n')
