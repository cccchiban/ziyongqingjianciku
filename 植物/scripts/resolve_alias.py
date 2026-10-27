"""解析 iPlant 的「您是否要找」重定向，把口性别名映射到正式收录的正名。

用法：python resolve_alias.py 桂花 榴莲 火龙果 …
输出：别名 \\t 正名 \\t 学名（每行一条，未匹配到输出别名 \\t - \\t -）
"""
import re
import sys
import urllib.parse

import fetch_plant_names as F

REDIR = re.compile(r"您是否要找：(.*?)</div>", re.S)
LINK = re.compile(r"<a href='/info/([^']+?)'(?:\?[^']*)?>(.*?)</a>", re.S)


def page_words(name):
    """返回 (正名, 学名, 出现过的重定向候选 [(中文名, 拉丁名)])。"""
    h = F.http("https://www.iplant.cn/info/" + urllib.parse.quote(name))
    cn = re.search(r'var spcname = "([^"]*)"', h)
    la = re.search(r'var latin2 = "([^"]*)"', h)
    cands = []
    m = REDIR.search(h)
    if m:
        for latin, text in LINK.findall(m.group(1)):
            t = re.sub(r"<[^>]+>", "", text).strip()
            t = re.sub(r"\s+", " ", t)
            parts = t.split(" ", 1)
            cn2 = parts[0]
            la2 = parts[1] if len(parts) > 1 else latin.split("?")[0]
            cands.append((cn2, la2))
    return (cn.group(1) if cn else ""), (la.group(1) if la else ""), cands


def main(names):
    for n in names:
        cn, la, cands = page_words(n)
        if la:
            print("%s\t%s\t%s" % (n, cn or n, la))
        elif cands:
            t, latin = cands[0]
            print("%s\t%s\t%s\tn=%d" % (n, t, latin, len(cands)))
        else:
            print("%s\t-\t-\t" % n)


if __name__ == "__main__":
    main(sys.argv[1:])
