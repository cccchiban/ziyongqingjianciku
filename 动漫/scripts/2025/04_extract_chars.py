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
                      u"|旁白|主人公|主角群)$")
# 维基角色表里「已知亲属有母亲（鈴木の母，声：…）、父亲（鈴木の父，声：…）」
# 这类条目：带「已知亲属」前缀，或整条只是「…的母亲/父亲」，都不成词条。
FAMILY_DESC = re.compile(u"(已知亲属|主要亲属|亲属有|家族有|关系者)")
# 非中文人名的残留：纯英文、含数字
BAD = re.compile(u"^[A-Za-z0-9\\s\\.\\-]+$")
CJK = re.compile(u"[\\u3400-\\u9fff]")
KANA = re.compile(u"[ぁ-んァ-ヶー]")


def extract(text):
    out = []
    for m in CHAR.finditer(text):
        name = m.group(1).strip()
        jp = m.group(2).strip()
        if not name or NOT_NAME.search(name) or FAMILY_DESC.search(name):
            continue
        if not CJK.search(name) or BAD.match(name):
            continue
        if len(name) < 2 or len(name) > 14:
            continue
        # 维基角色条目的标准格式是「中文名（日文原名，声：…）」，括号内必含假名。
        # 不含假名的「（…，声：…）」是正文叙述里偶然出现的结构，左侧短串是普通
        # 名词而非角色名——`老鸨`（猫猫被老鸨打得头破血流）、`皇帝`、`占卜师`、
        # `女骑士`、`组长` 都是这样被误抽的。实测 1489 条记录里 155 条属此类。
        if not KANA.search(jp):
            continue
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
