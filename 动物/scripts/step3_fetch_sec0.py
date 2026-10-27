import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

from wfetch import sec0

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = os.path.join(HERE, 'data')
CACHE = os.path.join(FILES, 'sec0')
os.makedirs(CACHE, exist_ok=True)


def cache_path(title):
    safe = urllib_safe(title)
    return os.path.join(CACHE, safe + '.txt')


def urllib_safe(s):
    out = []
    for ch in s:
        if ch.isalnum() or ch in '-_':
            out.append(ch)
        else:
            out.append('%%%02X' % ord(ch))
    return ''.join(out)[:120]


def get(title):
    p = cache_path(title)
    if os.path.exists(p):
        # ERROR 占位的条目下次重新尝试
        if open(p, encoding='utf-8').read() != 'ERROR':
            return
    txt = sec0(title)
    open(p, 'w', encoding='utf-8').write(txt)


def main(titles):
    with ThreadPoolExecutor(int(os.environ.get('WORKERS', '32'))) as ex:
        list(ex.map(get, titles))


if __name__ == '__main__':
    items = json.load(open(os.path.join(FILES, 'names_sci.json'), encoding='utf-8'))
    titles = [n for _, n, _ in items]
    if len(sys.argv) > 1:
        titles = titles[: int(sys.argv[1])]
    todo = [t for t in titles if not os.path.exists(cache_path(t))
            or open(cache_path(t), encoding='utf-8').read() == 'ERROR']
    print('todo', len(todo))
    main(todo)
    print('done, cached', len(os.listdir(CACHE)))
