import re

import opencc

T2S = opencc.OpenCC('t2s')

TRIGGER = re.compile(
    r'(?:又名|又称|又稱|别名|別名|别称|別稱|俗称|俗稱|简称|簡稱|通称|通稱|也称|也稱|也叫|亦名|亦称|亦稱|旧称|舊稱|土名|俗名|也称为|也稱為|也称为|又被称|又被稱為|被称作|被稱作|亦称为|亦稱為)')
STOP = re.compile(r'[。；;！!？?\n]|是|为|爲|属于|屬於|分布|分佈|原产|原產|因|由于|由於')
ZH = re.compile(r'[\u3400-\u9fff]+')
BAD = {'一种', '一種', '一些', '一类', '一類', '某些', '其他', '一种动物', '之类', '等等', '同上'}


def strip_markup(s):
    s = re.sub(r'<ref[^>/]*?/>', '', s)
    s = re.sub(r'<ref.*?</ref>', '', s, flags=re.S)
    s = re.sub(r'\{\{lang[a-z-]*\|[^|}]*\|', '', s, flags=re.I)
    s = re.sub(r'\{\{notetag\|([^{}]*)\}\}', r' \1 ', s, flags=re.I)
    s = re.sub(r'\{\{[^{}]*\}\}', '', s)

    def conv(m):
        body = m.group(1)
        for key in ('zh-cn', 'zh-hans', 'zh'):
            mm = re.search(key + r'\s*:\s*([^;}|]+)', body)
            if mm:
                return mm.group(1)
        return re.split(r'[;]', body)[0].split(':')[-1]

    s = re.sub(r'-\{([^{}]*)\}-', conv, s)
    s = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', s)
    s = re.sub(r'\[\[([^\]]+)\]\]', r'\1', s)
    s = re.sub(r"'{2,}", '', s)
    s = re.sub(r'<[^>]+>', '', s)
    s = re.sub(r'&#\d+;|&\w+;', '', s)
    return T2S.convert(s)


def extract(text, title):
    if not text or text == 'MISSING':
        return []
    t = strip_markup(text)
    out = []
    for m in TRIGGER.finditer(t):
        seg = t[m.end(): m.end() + 60]
        cut = STOP.search(seg)
        if cut:
            seg = seg[: cut.start()]
        for part in re.split(r'[、,，/／]|及|和|或', seg):
            p = re.sub(r'\s+', '', part.strip(' ()（）“”"\'：: 　'))
            if not p or p == title or p in out:
                continue
            if p in BAD or not ZH.fullmatch(p):
                continue
            if len(p) < 2 or len(p) > 10:
                continue
            if p.startswith('一种') or p.startswith('一种'):
                continue
            out.append(p)
    return out


if __name__ == '__main__':
    import glob
    import os
    import sys
    files = sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'files', 'sec0', '*.txt')))
    tot = hit = 0
    for f in files[:400]:
        name = os.path.basename(f)[:-4]
        a = extract(open(f, encoding='utf-8').read(), name)
        tot += 1
        if a:
            hit += 1
            print(name, a)
    print('files', tot, 'with alias', hit)
