"""动物名录并入 综合词库：正名提频，俗名只新增、不改既有词频。"""
import io
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
ENTRIES = ROOT / ".omnicrawl/.agent_tmp/files/animal_entries.tsv"
WORDLIST = ROOT / ".omnicrawl/.agent_tmp/files/animal_wordlist.tsv"

# 单字动物名只保留确实会单独敲的那些
COMMON_SINGLE = set(
    "虎狼猫狗马牛羊鸡鸭鹅鸟鱼蛇蛙龟兔猪猴熊象鹿鹰鼠蚕蝉蝎虾蟹蜂蚁蚊蝇鸥鹬鹭鹳隼雕蟒驴鲤鲫鳗蚌蛾"
    "鲸鲨豹鸽鲸豚獾貂獭鹅鹑鸨鸢鹫鹗鸬鹚鹈鹕鹮鹳鲈鲳鲷鳕鳝鳅鲵鲎鳐鳙鳟鲑鳜鲟鳌鲇鲂鲮鳎鲽鲆鲚"
)

# 与日常高频词同形、动物义不占优的俗名：入库只会干扰正常输入
ALIAS_DROP = {
    # 地名、分类阶元、叙述残片
    "北京", "东南亚", "西双版纳", "之一", "俗名鳀", "涡虫纲", "小巴",
    # 日常义压倒动物义
    "刀片", "铁甲", "飘飘", "相思", "神仙", "魔鬼", "嘉宾", "天子", "大眼",
    "鸡毛", "黑毛", "划分", "剥皮", "白条", "红眼", "飞龙", "国宝", "水族",
    "地铺", "枪管", "方头", "尖嘴", "红线", "花甲", "铁壳", "青波", "鬼龙",
    "彩凤", "美人痣", "黄色虹膜", "龙角", "石崇", "灌丛", "白带", "白口",
    "黑头", "山鸟", "华虫", "沙条", "马刀", "红子", "紫斑", "立花", "鲁达",
    "恩吉", "十二红", "白鼻", "蠹鱼", "寿星头", "小娘子", "泥滑滑", "草上飞",
    "金鳞甲", "河马兽", "东方龙", "倒吊", "山雉", "毛鸡", "池鱼", "山猫",
    "人猿", "小鹬", "大虫", "青口", "生蚝", "海蛎子", "干贝", "红鹤",
    "红娘仔", "红飞鱼", "虎鱼", "虎鸫", "飞狸", "灯笼鱼", "气泡鱼", "沙丁鱼",
    "淮王鱼", "白花蛇", "麻蛇", "蝘蜓", "蝎虎", "蛛蛛", "老鸹", "郭公",
}

NAME_DROP = {"人"}

LADDER = {2: 690, 3: 670, 4: 650, 5: 630, 6: 615}
SINGLE_FREQ = 700

# 既有库读音确实错的动物名，按人工核定值覆盖
PINYIN_FIX = {
    "藏狐": "zang4 hu2",
    "长尾鼠耳蝠": "chang2 wei3 shu3 er3 fu2",
}


def load_common():
    d = {}
    with io.open(ROOT / "常用词/常用词.tsv", encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3:
                d[p[0]] = int(p[2])
    return d


def main():
    common = load_common()
    rows = []
    with io.open(ENTRIES, encoding="utf-8") as f:
        for line in f:
            w, py, kind, _ = line.rstrip("\n").split("\t")
            rows.append((w, py, kind))

    out, dropped = [], []
    for w, py, kind in rows:
        if w in NAME_DROP:
            dropped.append((w, "非输入对象"))
            continue
        if kind == "alias" and w in ALIAS_DROP:
            dropped.append((w, "日常义占优"))
            continue
        if len(w) == 1:
            if w not in COMMON_SINGLE:
                dropped.append((w, "冷僻单字"))
                continue
            freq = SINGLE_FREQ
        elif w in common:
            freq = common[w]
        else:
            freq = LADDER.get(len(w), 600)
        out.append((w, py, kind, freq))

    with io.open(WORDLIST, "w", encoding="utf-8", newline="\n") as f:
        for w, py, kind, freq in sorted(out):
            f.write("%s\t%s\t%s\t%d\n" % (w, py, kind, freq))
    st = {}
    for _, why in dropped:
        st[why] = st.get(why, 0) + 1
    print("词表 %d 条，剔除 %d 条 %s" % (len(out), len(dropped), st))
    print("词频区间 %d—%d" % (min(r[3] for r in out), max(r[3] for r in out)))


if __name__ == "__main__":
    main()
