"""Prints 1h, 5m, none or unknown: the prompt-cache TTL this chat's main thread writes with.

none = the transcript read fine but carries no cache_creation data yet — no reply has
landed, the normal early-chat state, not a failure.
unknown = detection itself failed: no transcript file, or it could not be read or parsed.

Run with --selftest to check classify() without touching the filesystem.
"""
import glob, json, os, sys


def classify(lines: list) -> str:
    parsed_any = False
    for line in reversed(lines):
        try:
            j = json.loads(line)
        except Exception:
            continue
        parsed_any = True
        if j.get('type') != 'assistant' or j.get('isSidechain'):
            continue
        cc = ((j.get('message') or {}).get('usage') or {}).get('cache_creation') or {}
        if (cc.get('ephemeral_1h_input_tokens') or 0) > 0:
            return '1h'
        if (cc.get('ephemeral_5m_input_tokens') or 0) > 0:
            return '5m'
    if lines and not parsed_any:
        return 'unknown'
    return 'none'


def main(sid: str) -> str:
    paths = glob.glob(os.path.expanduser(f'~/.claude/projects/*/{sid}.jsonl')) if sid else []
    if not paths:
        return 'unknown'
    try:
        with open(paths[0], 'rb') as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 3_000_000))
            tail = f.read().decode('utf-8', 'ignore').splitlines()[1:]
    except OSError:
        return 'unknown'
    return classify(tail)


def _selftest():
    assert classify(['not json']) == 'unknown'
    assert classify([]) == 'none'
    assert classify([json.dumps({'type': 'user'})]) == 'none'
    assert classify([json.dumps({'type': 'assistant', 'message': {'usage': {'cache_creation': {'ephemeral_1h_input_tokens': 5}}}})]) == '1h'
    assert classify([json.dumps({'type': 'assistant', 'message': {'usage': {'cache_creation': {'ephemeral_5m_input_tokens': 5}}}})]) == '5m'
    print('ok')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--selftest':
        _selftest()
    else:
        print(main(sys.argv[1] if len(sys.argv) > 1 else ''))
