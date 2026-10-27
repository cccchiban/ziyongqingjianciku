"""生成 动物/动物.tsv：中文名 \t 学名 \t 俗名（「、」分隔，缺则 -）。"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aliases import extract  # noqa: E402
from sciname import T2S, scientific  # noqa: E402
from step3_fetch_sec0 import cache_path  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = os.path.join(HERE, 'data')
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))

# 俗名里的残留前缀（触发词被切分后的尾巴）
LEAD_NOISE = ('者', '之', '为', '爲', '称', '稱', '叫', '作', '亦', '也', '古', '又',
              '又名', '又称', '又稱', '别名', '別名', '别称', '別稱', '俗称', '俗稱', '俗名',
              '通称', '通稱', '也称', '也稱', '亦称', '亦稱', '简称', '簡稱', '旧称', '舊稱',
              '也称为', '也稱為', '又被称', '又被稱為', '被称作', '被稱作', '亦称为', '亦稱為')
# 叙述片段而非名称
NOISE_SUB = ('学者', '渔民', '语中', '等地', '一带', '自治区', '海域', '现已', '可达', '相若',
             '历史上', '活动于', '亚种', '亚科', '种下的', '反映', '误会', '概称', '山区',
             '拉丁', '常见于', '者西', '分布', '产生', '俗称', '古称', '通称', '亦称', '也称',
             '又名', '又称', '别名', '别称', '湾俗称', '港俗称', '可以指', '重定向', '广泛',
             '闽南语', '客语', '印度北部', '尼泊尔', '石栖鸟', '译音', '名称', '种加词',
             '称之', '古代称', '称', '稱', '种', '属', '科', '目', '纲', '门', '甚多',
             '动物分类学', '一般指', '包括', '除极地', '岛屿外', '取', '源于', '族群', '下游',
             '江苏', '上海', '广东', '福建', '台湾', '朝鲜', '日本', '香港', '澳门', '中国',
             '称其', '取其', '鬣蜥科', '同', '大多', '等', '与', '和', '及')


def clean_alias(a):
    a = a.strip('、。 ，,')
    a = re.sub(r'[（(][^)）]*[)）]', '', a)
    changed = True
    while changed:
        changed = False
        for lead in LEAD_NOISE:
            if a.startswith(lead) and len(a) > len(lead) + 1:
                a = a[len(lead):]
                changed = True
    while a.endswith('等') and len(a) > 2:
        a = a[:-1]
    if not a or len(a) < 1 or len(a) > 6:
        return None
    if not re.fullmatch(r'[\u3400-\u9fff]+', a):
        return None
    for s in NOISE_SUB:
        if s in a:
            return None
    if a in ('俗名', '别名', '别称', '学名', '又名', '又称', '俗称', '通称', '其他', '等等'):
        return None
    if re.search(r'(生活|栖息|分布|主要|属于|位于|广泛|是指|包括)', a):
        return None
    return a


def aliases_for(name):
    p = cache_path(name)
    if not os.path.exists(p):
        return []
    raw = open(p, encoding='utf-8').read()
    out = []
    for a in extract(raw, name):
        a = clean_alias(a)
        if a and a != name and a not in out:
            out.append(a)
    return out


def main():
    rows = json.load(open(os.path.join(FILES, 'names_sci.json'), encoding='utf-8'))
    data = []          # (中文名, 学名, [俗名])
    seen = set()
    for kind, name, sci in rows:
        if name in seen:
            continue
        seen.add(name)
        data.append([name, sci, aliases_for(name)])
    msci = {}
    for fn in ('manual_sci.tsv', 'manual_sci2.tsv'):
        for raw in open(os.path.join(FILES, fn), encoding='utf-8'):
            raw = raw.rstrip('\n')
            if raw and '\t' in raw:
                n, v = raw.split('\t', 1)
                msci[n.strip()] = v.strip()

    extra = []
    for fn in ('extra_names.txt', 'extra_names2.txt', 'extra_names3.txt'):
        extra += [l.strip() for l in open(os.path.join(FILES, fn), encoding='utf-8') if l.strip()]
    for name in dict.fromkeys(extra):
        if name in seen:
            continue
        p = cache_path(name)
        if not os.path.exists(p):
            continue
        raw = open(p, encoding='utf-8').read()
        sci = msci.get(name) or scientific(raw)
        if not sci:
            continue
        seen.add(name)
        data.append([name, sci, aliases_for(name)])

    manual = {}
    mp = os.path.join(FILES, 'manual_aliases.tsv')
    for raw in open(mp, encoding='utf-8'):
        raw = raw.rstrip('\n')
        if not raw or '\t' not in raw:
            continue
        n, a = raw.split('\t', 1)
        vals = manual.setdefault(n.strip(), [])
        for x in a.split('、'):
            if x and x not in vals:
                vals.append(x)

    # 人工核定表优先：常见动物的俗名以词典口径为准，抓取结果作补充
    lines = []
    data.sort(key=lambda x: x[0])
    merged = {}
    for name, sci, al in data:
        name = T2S.convert(name)
        ali = [T2S.convert(a) for a in dict.fromkeys(manual.get(name, [])) if a != name]
        for a in al:
            a = T2S.convert(a)
            if a != name and a not in ali:
                ali.append(a)
        ali = [a for a in ali if a != name][:4]
        cell = '、'.join(ali) if ali else '-'
        if name not in merged or (merged[name][1] == '-' and cell != '-'):
            merged[name] = (sci, cell)
    for name in sorted(merged):
        sci, cell = merged[name]
        lines.append((name, sci, cell))
    out = os.path.join(ROOT, '动物', '动物.tsv')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        for name, sci, ali in lines:
            f.write(f'{name}\t{sci}\t{ali}\n')
    print('wrote', out, len(lines))
    json.dump(lines, open(os.path.join(FILES, 'final_rows.json'), 'w', encoding='utf-8'), ensure_ascii=False)


if __name__ == '__main__':
    main()
