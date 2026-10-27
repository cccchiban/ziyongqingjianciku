"""抓取维基条目首段，跟随一次重定向；缓存到 sec0/ 同名文件。

跟随重定向后取目标条目的首段；文件首行写入 `#REDIRECTED <目标标题>`，
便于生成时把原词面识别为「别名重定向」（正名之外的俗称）。
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from step3_fetch_sec0 import cache_path  # noqa: E402
from wfetch import sec0  # noqa: E402

REDIR = re.compile(r'^\s*#\s*(?:REDIRECT|重定向)\s*\[\[([^\]|]+)', re.I)


def follow(title):
    raw = sec0(title)
    if raw in ('MISSING', 'ERROR'):
        return raw
    m = REDIR.match(raw)
    if not m:
        return raw
    target = m.group(1).strip()
    if target == title:
        return raw
    second = sec0(target)
    if second in ('MISSING', 'ERROR'):
        return raw
    if REDIR.match(second):
        return second
    return f'#REDIRECTED {target}\n' + second


if __name__ == '__main__':
    titles = sys.argv[1:]
    for t in titles:
        p = cache_path(t)
        txt = follow(t)
        open(p, 'w', encoding='utf-8').write(txt)
        first = txt.splitlines()[0][:60] if txt else ''
        print(t, len(txt), first)
