"""Expose browser interaction only; never expose code, installers or file tools."""
import json
import os
from pathlib import Path
import subprocess
import sys
import shutil
import threading
from urllib.parse import urlsplit

ALLOWED = frozenset({
    'browser_navigate', 'browser_navigate_back', 'browser_snapshot',
    'browser_click', 'browser_hover', 'browser_type', 'browser_fill_form',
    'browser_press_key', 'browser_select_option', 'browser_wait_for',
    'browser_tabs', 'browser_close', 'browser_resize', 'browser_drag',
})


def main():
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    folder = Path(__file__).resolve().parent
    root = Path(os.environ.get('QWEN_MCP_RUNTIME', str(folder / 'runtime' / 'playwright-mcp'))).resolve()
    cli = root / 'node_modules' / '@playwright' / 'mcp' / 'cli.js'
    env = dict(os.environ, PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD='1')
    proc = subprocess.Popen([
        shutil.which('node') or 'node', str(cli),
        '--executable-path', os.environ['QWEN_CHROME'],
        '--isolated', '--no-webmcp', '--codegen', 'none', '--ignore-roots',
        '--output-dir', str(root / 'artifacts'), '--output-max-size', '10485760',
    ] + (['--headless'] if os.environ.get('QWEN_HEADLESS') == '1' else []), cwd=root, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
       text=True, encoding='utf-8', bufsize=1)
    lock = threading.Lock()
    list_ids = set()

    def emit(message):
        with lock:
            print(json.dumps(message, ensure_ascii=False), flush=True)

    def responses():
        for line in proc.stdout:
            message = json.loads(line)
            with lock:
                is_list = message.get('id') in list_ids
                if is_list:
                    list_ids.discard(message['id'])
            if is_list and 'result' in message:
                message['result']['tools'] = [
                    t for t in message['result'].get('tools', []) if t['name'] in ALLOWED]
            emit(message)
        # Fail closed if the MCP child dies while the client is still connected.
        os._exit(proc.wait() or 0)

    threading.Thread(target=responses, daemon=True).start()
    try:
        for line in sys.stdin:
            message = json.loads(line)
            method = message.get('method')
            if method == 'tools/list':
                with lock:
                    list_ids.add(message['id'])
            if method == 'tools/call':
                params = message.get('params', {})
                args = params.get('arguments', {})
                reason = None
                if params.get('name') not in ALLOWED:
                    reason = 'Tool disabled: only browser interaction is allowed.'
                elif any(k.lower() in {'filename', 'path', 'paths', 'code', 'function'} for k in args):
                    reason = 'Code execution and file output are disabled.'
                elif params.get('name') == 'browser_navigate' and urlsplit(args.get('url', '')).scheme not in {'https', 'http'}:
                    reason = 'Only HTTP and HTTPS navigation is allowed.'
                if reason:
                    emit({'jsonrpc': '2.0', 'id': message['id'], 'result': {
                        'isError': True, 'content': [{'type': 'text', 'text': reason}]}})
                    continue
            elif method not in {'initialize', 'notifications/initialized', 'notifications/cancelled',
                                'tools/list', 'ping'}:
                if 'id' in message:
                    emit({'jsonrpc': '2.0', 'id': message['id'], 'error': {
                        'code': -32601, 'message': 'Method disabled by browser guard'}})
                continue
            proc.stdin.write(json.dumps(message) + '\n')
            proc.stdin.flush()
    finally:
        proc.stdin.close()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.terminate()


if __name__ == '__main__':
    main()
