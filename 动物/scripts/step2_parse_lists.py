import re
import os

FILES = {
    'mammal': '中国哺乳动物列表.txt',
    'bird': '中国鸟类列表.txt',
    'reptile': '中国爬行动物列表.txt',
    'amphibian': '中国两栖动物列表.txt',
    'fish': '中国鱼类列表.txt',
}

LINK = re.compile(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]')
SCI = r"''\s*([A-Z][a-z]+(?:[ ][a-z\-]+){1,2})\s*''"


def clean_label(s):
    s = LINK.sub(lambda m: m.group(2) or m.group(1), s)
    s = re.sub(r"''+", '', s)
    s = re.sub(r"\{\{[^{}]*\}\}", '', s)
    s = re.sub(r"<[^>]+>", '', s)
    s = s.replace('（', '(').replace('）', ')')
    s = re.sub(r'[\s\u3000]+', '', s)
    return s.strip()


def parse_line_list(line, out, bare=False):
    """[[中文名]]（''学名''） 结构；bare=True 时接受不带括号的 [[名]] ''学名''"""
    for m in LINK.finditer(line):
        name = clean_label(m.group(2) or m.group(1))
        rest = line[m.end():]
        s = re.match(r"\s*[（(]\s*" + SCI, rest) if not bare else (
            re.match(r"\s*" + SCI, rest) or re.match(r"\s*[（(]\s*" + SCI, rest))
        if not s:
            continue
        sci = s.group(1).strip()
        if len(name) < 1 or not re.fullmatch(r'[\u3400-\u9fff]{1,}', name):
            continue
        out.append((name, sci))


def parse_table(line, out):
    """| 编号 || ''学名''||[[中文名]]|| ... 结构"""
    cells = [c.strip() for c in line.strip().lstrip('|').split('||')]
    sci = None
    name = None
    for c in cells:
        m = re.fullmatch(SCI, c)
        if m and sci is None:
            sci = m.group(1).strip()
            continue
        m2 = re.fullmatch(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]', c.replace(' ', ''))
        if m2 and name is None:
            name = clean_label(m2.group(2) or m2.group(1))
    if sci and name and re.fullmatch(r'[\u3400-\u9fff]{2,}', name):
        out.append((name, sci))


def parse(kind, path):
    text = open(path, encoding='utf-8').read()
    out = []
    for line in text.splitlines():
        if not re.search(SCI, line):
            continue
        parse_line_list(line, out, bare=True)
        parse_table(line, out)
    # 去重保序
    seen = set()
    uniq = []
    for name, sci in out:
        if name in seen:
            continue
        seen.add(name)
        uniq.append((name, sci))
    return uniq


if __name__ == '__main__':
    root = os.path.join(os.path.dirname(__file__), 'data', 'raw')
    total = []
    for kind, fn in FILES.items():
        items = parse(kind, os.path.join(root, fn))
        print(kind, len(items))
        for it in items[:2]:
            print('   ', it)
        total += [(kind,) + it for it in items]
    print('all', len(total))
    names = {}
    for k, n, s in total:
        names.setdefault(n, []).append((k, s))
    dup = {n: v for n, v in names.items() if len(v) > 1}
    print('unique names', len(names), 'dup', len(dup))
    for n, v in list(dup.items())[:15]:
        print(' dup', n, v)
    import json
    json.dump(total, open(os.path.join(os.path.dirname(__file__), '..', 'files', 'names_sci.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
