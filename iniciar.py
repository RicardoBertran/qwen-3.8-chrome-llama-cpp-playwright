"""Arranca una sesion independiente de Llama UI y Chrome."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys

ROOT = Path(__file__).resolve().parent

def main():
    config = ROOT / 'local.json'
    if not config.exists():
        raise ValueError('Copia config.example.json a local.json. Consulta el README.')
    c = json.loads(config.read_text(encoding='utf-8-sig'))
    server = (ROOT / c['server']).resolve()
    model = (ROOT / c['model']).resolve()
    chrome = next((p for base in ('PROGRAMFILES', 'PROGRAMFILES(X86)', 'LOCALAPPDATA')
                   if os.environ.get(base)
                   for p in [Path(os.environ[base]) / 'Google/Chrome/Application/chrome.exe']
                   if p.is_file()), None)
    for p in (server, model, ROOT / 'runtime/playwright-mcp/node_modules/@playwright/mcp/cli.js'):
        if not p.is_file():
            raise ValueError(f'No se encuentra: {p}')
    if not chrome or not shutil.which('node'):
        raise ValueError('Instala Chrome y Node.js; despues abre otra terminal.')
    help_text = subprocess.run([str(server), '--help'], capture_output=True, text=True, encoding='utf-8', errors='replace', check=True).stdout
    for flag in ('--mcp-servers-config', '--no-agent', '--jinja', '--fit', '--cors-origins'):
        if flag not in help_text:
            raise ValueError(f'Esta version de llama.cpp no incluye {flag}. Consulta el README.')
    port = int(c.get('port', 8080))
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', port))
    mcp = {'mcpServers': {'playwright': {
        'command': sys.executable, 'args': ['-B', str(ROOT / 'playwright_guard.py')],
        'cwd': str(ROOT), 'env': {'QWEN_CHROME': str(chrome)}, 'timeout_ms': 120000}}}
    session = ROOT / 'session-mcp.json'
    session.write_text(json.dumps(mcp, indent=2), encoding='utf-8')
    cmd = [str(server), '-m', str(model), '-c', str(int(c.get('context',8192))),
           '--jinja', '--fit', 'on', '--parallel', '1', '--host', '127.0.0.1',
           '--port', str(port), '--no-agent', '--cors-origins', 'localhost',
           '--mcp-servers-config', str(session)]
    if '--check' in sys.argv:
        print('Archivos, Chrome, Node, opciones y puerto: correctos. No se ha cargado el modelo.')
        return
    print(f'Espera a que cargue el modelo y abre http://127.0.0.1:{port}/')
    print('Para terminar, pulsa Ctrl+C en esta ventana.')
    proc = subprocess.Popen(cmd, cwd=ROOT)
    try:
        return proc.wait()
    except KeyboardInterrupt:
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.terminate()
            proc.wait()

if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as e:
        print(f'No se puede iniciar: {e}', file=sys.stderr)
        sys.exit(1)
