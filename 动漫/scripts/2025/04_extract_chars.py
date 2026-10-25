# -*- coding: utf-8 -*-
"""从缓存的维基条目纯文本里抽取角色名。

维基角色条目的典型写法（中文维基，提取纯文本后）：
    球球 （ タマ ，声： 畠中祐 、 杉山里穗 〔猫〕 ）
    爱莉亚 （ アリア ，声： 矢野妃菜喜 ）
    苍井春人 （ あおい はると ，声： 千叶翔也 ）
故锚点是「（…，声：」，其左侧紧邻的短串即角色中文名。

需过滤的非角色条目：
    美波和正树的母亲 / 三线屋的店主 / 旁白 / 比嘉的祖母
这类是关系描述而非人名，特征是含「的母亲/的父亲/的祖母/的爷爷/的店主」或
以「旁白」「解说」等身份词结尾。
"""
import pathlib
import re
import sys

WORK = pathlib.Path(__file__).parent.parent / ".omnicrawl_work"
RAW = WORK / "char_raw"

# 锚点：（…，声：
CHAR = re.compile(u"([^\\s（(，、。；：!？]{2,16})\\s*[（(]\\s*([^（）()]{0,50}?)[，,]\\s*声[：:]")
# 关系/身份描述，不是人名
NOT_NAME = re.compile(u"(的母亲|的父亲|的祖母|的祖父|的爷爷|的奶奶|的姐姐|的妹妹|的哥哥"
                      u"|的弟弟|的店主|的女儿|的儿子|的妻子|的丈夫|的恋人"
                      u"|旁白|解说| narrat|主人公|主角|主角群)$")
# 非中文人名的残留：纯英文、含数字
BAD = re.compile(u"^[A-Za-z0-9\\s\\.\\-]+$")
CJK = re.compile(u"[\\u3400-\\u9fff]")


def extract(text):
    out = []
    for m in CHAR.finditer(text):
        name = m.group(1).strip()
        jp = m.group(2).strip()
        if not name or NOT_NAME.search(name):
            continue
        if not CJK.search(name) or BAD.match(name):
            continue
        if len(name) < 2 or len(name) > 14:
            continue
        # 括号里的日文名：若为空或与中文名相同，跳过判重无用
        out.append((name, jp))
    return out


def main():
    files = [p for p in sorted(RAW.glob("*.txt")) if p.stat().st_size > 1024]
    print(u"可用条目 %d" % len(files))
    total = 0
    seen = {}
    for p in files:
        text = p.read_text(encoding="utf-8")
        for name, jp in extract(text):
            seen.setdefault(name, 0)
            seen[name] += 1
            total += 1
    print(u"抽到 %d 条记录，%d 个唯一角色名" % (total, len(seen)))
    multi = {k: v for k, v in seen.items() if v > 1}
    print(u"跨作品重复出现 %d 个（同名角色/常见名）" % len(multi))
    for k, v in list(sorted(multi.items(), key=lambda x: -x[1]))[:15]:
        print(u"  %s ×%d" % (k, v))
    print(u"\n抽样 40 个：")
    for k in list(seen)[:40]:
        print(u"  " + k)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
