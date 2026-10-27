import re

import opencc

T2S = opencc.OpenCC('t2s')

CLEAN = r"\{\{[^{}]*\}\}|''|\[\[|\]\]|<[^>]+>"


def _valuable(v):
    v = re.sub(CLEAN, '', v).strip()
    v = re.sub(r'\s+', ' ', v)
    return v


def _taxon_from_box(t):
    m = re.search(r'\|\s*taxon\s*=\s*([^\n|}]+)', t, re.I)
    if m:
        v = _valuable(m.group(1))
        if re.fullmatch(r'[A-Z][a-z]+(?: [a-z\-]+)?', v):
            return v
    g = re.search(r'\|\s*genus\s*=\s*([A-Za-z\-]+)', t)
    s = re.search(r'\|\s*species\s*=\s*([A-Za-z\-]+)', t)
    if g and s:
        return f'{g.group(1)} {s.group(1)}'
    b = re.search(r'\|\s*binomial\s*=\s*([^\n|}]+)', t, re.I)
    if b:
        v = _valuable(b.group(1))
        if re.fullmatch(r'[A-Z][a-z]+(?: [a-z\-]+)?', v):
            return v
    return None


def scientific(text):
    """种级优先（Genus species），否则回退到分类框里的高阶元拉丁名。"""
    if not text or text in ('MISSING', 'ERROR'):
        return None
    t = T2S.convert(text)
    v = _taxon_from_box(t)
    if v:
        return v
    for key in ('parent', 'taxon'):
        a = re.search(key + r'\s*=\s*([A-Z][a-z]+)', t, re.I)
        if a:
            return a.group(1)
    m = re.search(r'学名[：:]\s*(?:\{\{lang[^|}]*\|)?\s*' + r"''?", t)
    if m:
        seg = _valuable(t[m.end(): m.end() + 60])
        mm = re.match(r'([A-Z][a-z]+(?: [a-z\-]+)?)', seg)
        if mm:
            return mm.group(1)
    return None


if __name__ == '__main__':
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from step3_fetch_sec0 import cache_path
    for t in ['蜘蛛', '虾', '螃蟹', '家猫', '赤狐', '中华蜜蜂', '鲎']:
        p = cache_path(t)
        raw = open(p, encoding='utf-8').read() if os.path.exists(p) else ''
        print(t, '|', scientific(raw))
