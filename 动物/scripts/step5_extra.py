"""抓取补充清单（无脊椎与家养动物）的首段，跟随重定向。"""
import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from step3_fetch_sec0 import cache_path  # noqa: E402
from step3b_follow import follow  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = os.path.join(HERE, 'data')


def one(title):
    p = cache_path(title)
    if os.path.exists(p):
        txt = open(p, encoding='utf-8').read()
        if txt and txt != 'ERROR':
            return title, 'cached'
    txt = follow(title)
    open(p, 'w', encoding='utf-8').write(txt)
    return title, 'MISSING' if txt == 'MISSING' else ('ERROR' if txt == 'ERROR' else 'ok')


if __name__ == '__main__':
    names = [l.strip() for l in open(os.path.join(FILES, os.environ.get('EXTRA', 'extra_names.txt')), encoding='utf-8') if l.strip()]
    names = list(dict.fromkeys(names))
    with ThreadPoolExecutor(12) as ex:
        res = list(ex.map(one, names))
    from collections import Counter
    print(Counter(s for _, s in res))
    print('missing:', [t for t, s in res if s == 'MISSING'])
