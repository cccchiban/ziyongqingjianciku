import collections
import re
import sys

path = '动物/动物.tsv'
raw = open(path, 'rb').read()
assert raw[:3] != b'\xef\xbb\xbf', 'BOM'
assert b'\r' not in raw, 'CRLF'
assert raw.endswith(b'\n'), 'no trailing newline'
text = raw.decode('utf-8')
rows = [l.split('\t') for l in text.split('\n') if l]
errors = []
if any(len(r) != 3 for r in rows):
    errors.append('列数不为 3')
names = [r[0] for r in rows]
if len(set(names)) != len(names):
    errors.append('词面有重复')
if names != sorted(names):
    errors.append('未按词面排序')
for n, s, a in rows:
    if not re.fullmatch(r'[\u3400-\u9fff\U00020000-\U0003FFFF]{1,}', n):
        errors.append('名称不合规: ' + n)
    if not re.fullmatch(r'[A-Z][a-z]+(?: [a-z\-]+)?', s):
        errors.append('学名不合规: ' + s)
    if a != '-':
        if not re.fullmatch(r'[\u3400-\u9fff\U00020000-\U0003FFFF]+(?:、[\u3400-\u9fff\U00020000-\U0003FFFF]+)*', a):
            errors.append('俗名不合规: ' + a)
        parts = a.split('、')
        if len(parts) != len(set(parts)):
            errors.append('俗名重复: ' + a)
        if n in parts:
            errors.append('俗名含正名: ' + n)
dist = collections.Counter(len(r[2].split('、')) if r[2] != '-' else 0 for r in rows)
print('行数', len(rows))
print('俗名数分布', sorted(dist.items()))
print('有俗名', sum(v for k, v in dist.items() if k))
print('学名唯一数', len({r[1] for r in rows}))
print('错误', len(errors))
for e in errors[:15]:
    print('  ', e)
sys.exit(1 if errors else 0)
