# -*- coding: utf-8 -*-
"""生成 电商/亚马逊词库.tsv、电商/Ozon词库.tsv、电商/其他词库.tsv。

来源见 AGENT.md「电商词库」节与各库说明：亚马逊卖家术语表与官方帮助中心、
Ozon 官方卖家帮助中心（FBO/FBS/realFBS、报告字段、费用构成）、Temu/TikTok
Shop/Shopee/美客多等平台公开术语整理，以及跨境物流与合规通用术语。

划分原则：平台专有词归各自库，跨境通用词（头程、清关、汇率等）统一归
「其他词库」，三库之间不出现同名词面。词面纯汉字为主；英文缩写与平台名按
仓库惯例逐字符空格分隔（ASIN → A S I N）。拼音人工核定，多音字专名走
OVERRIDES。
"""
import io
import os
import re
import sys
import glob

from pypinyin import Style, lazy_pinyin, pinyin

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUTDIR = os.path.join(REPO, "电商")

HAN = re.compile(r"^[\u3400-\u9fff]+$")
ASCII = re.compile(r"^[A-Za-z0-9+\-.]$")

AMAZON = [
    ("平台与站点", 900, """
亚马逊 美国站 欧洲站 日本站 北美站 澳洲站 中东站 新加坡站 印度站
加拿大站 墨西哥站 巴西站 英国站 德国站 法国站 意大利站 西班牙站
荷兰站 波兰站 瑞典站 比利时站 土耳其站 阿联酋站 沙特站
全球开店 亚马逊物流 亚马逊自营 亚马逊全球收款
品牌注册 品牌备案 亚马逊品牌 亚马逊全球物流 卖家大学 卖家支持
亚马逊广告 亚马逊商城 亚马逊品牌分析
"""),
    ("账号与审核", 875, """
账户健康 绩效通知 二审 视频验证 账号关联 关联封店 小红旗 白帽 黑帽
刷单 真人测评 留评 索评 刷评 恶意差评 恶意跟卖 侵权投诉 恶意投诉
暂停销售 账户审核 资质审核 账单验证 供应链审核 发票验证 违规申诉
申诉信 行动计划 扫号 猎杀 黑科技 灰色服务商 KYC审核 品牌白名单
授权品牌 版权投诉 专利投诉 政策警告 账户状况评级 挂店
计划政策 商品真伪 假货投诉
"""),
    ("商品页面", 865, """
商品页面 详情页 五点描述 产品描述 父体 子体 变体主题 合并变体
拆分变体 变体滥用 品牌旗舰店 品牌故事 商品视频 后端关键词 埋词
长尾词 大词 新品期 页面浏览 商品草稿 关键属性 类目节点 商品编码
主图白底 商品要点 搜索词 后台搜索词 变体关系 商品标题
"""),
    ("广告与推广", 855, """
商品推广 品牌推广 展示型推广 自动投放 手动投放 否词 否定关键词
精准匹配 词组匹配 广泛匹配 关键词排名 广告排名 黄金购物车
购物车占有率 会员专享折扣 黑五 网一 会员日 七天促销 优惠叠加
广告位 广告架构 分时调价 竞价加价 广告活动 广告组 广告报告
搜索词报告 品牌分析 虚拟捆绑 订购省 广告活动预算 商品定位
品类定位 展示量 无效点击 广告归因 归因周期 竞价策略 动态竞价 首页首位
自动定向 广告表现 品牌加速器
"""),
    ("仓储与配送", 845, """
亚马逊物流仓储 库容 库存绩效指标 长期仓储费 月度仓储费
配送费 移除订单 弃置 换标 贴标 箱唛 托盘 预约入仓 卡派 快递派
入仓 到仓 分拨中心 库容限制 货件 入库计划 补货限制
亚马逊合作承运人 头程入仓 旺季附加费 FBA头程 头程运输 入库配置
分仓 合仓 货件差异 仓储利用率 旺季仓储费 退货处理
"""),
    ("运营与绩效", 835, """
推荐费 佣金率 月租 订单缺陷率 迟发率 有效追踪率 卖家反馈
账户余额 收款账户 第三方收款 回款周期 费用明细 星级 评论数
库存绩效分数 绩效指标 缺陷率 卖家评级 取消率 回复时限 卖家绩效
评论管理 请求评论 气候友好承诺 供应链服务 亚马逊企业购
亚马逊生鲜 亚马逊药房 亚马逊低价商城
"""),
    ("选品与供应链", 825, """
铺货 精铺 白牌 自有品牌 起订量 打样 关键词反查 竞品分析
类目分析 数据选品 利润测算 仿品 侵权风险 铺货党 精铺党
精品路线 无货源 有货源 大卖 小卖 美国商标 品牌保护 铺货模式
精品模式 精铺模式 新品扶持 品牌工具 工厂验厂 验厂 出货检验
大货样品 旺季备货 美国本土店 欧洲本土店 供应链服务商
"""),
    ("运营黑话", 810, """
李思婷 测评单 螺旋广告 一拖多 僵尸链接 蹭流量 跟卖狗
测评群 孵化 培训机构 变狗 申诉不过 静默期 一星
"""),
    ("缩写与代码", 860, """
ASIN FNSKU MSKU UPC EAN ISBN FBA FBM PPC ACOS TACOS ROAS CPM
BSR ODR IPI EORI KYC TRO DDP DDU A+页面 亚马逊的选择
"""),
]

OZON = [
    ("平台与后台", 900, """
Ozon 个人中心 商品卡 富内容 合并卡片 商品检查 提货单
搜索查询 买家画像 索引错误 商品状态 准备开售 商品标识 视频封面
标题字符 图片规范 商品特征 类目属性 商品评级 店铺名称 商品模板 批量上传 接口上传 价格管理 库存管理
仓库优先级 索引 商品图片 商品问答 分析工具 销售漏斗
利基市场 Ozon分析 商品需求 关键词竞价 广告工具 评价管理 数据报告
"""),
    ("履约模式", 890, """
FBO FBS realFBS rFBS FBP 跨境直发 大件商品 超大件 区域仓 边境仓
前置仓 白关 灰关 清关行 物流单号 运单 追踪号 平台仓 自有仓 集货仓 揽收 自送
预约取件 分拣中心 提货点 自提点 货架 分布式仓库 出库 拣货
快递员 OGL 揽收率 履约时效 逾期发货 无人认领 最后一公里 揽收点
"""),
    ("费用与结算", 880, """
类目佣金 物流费 收单费 提现费 相互结算 对账单 电子钱包 结算货币
卢布 增值税 附加服务 入仓费 仓储费 跨区附加费 价格分档 费率
保证金 注册费 年费 免仓租 佣金减免 应计额 佣金政策
动态佣金 退货损耗 采购空间 提现门槛 结算余额 类目费率 佣金费率
月结 已结算 结算日 应付款
"""),
    ("营销与流量", 870, """
大促销 活动价 积分价 绿标价 划线价 平台积分 会员价 促销申请
营销申请 价格锁定 推荐价格 竞品价格 定价模板 价格带 搜索查询量
搜索权重 加权 报名活动 免费配送 折扣空间 流量扶持 新店扶持
促销活动 平台活动 品牌日 商品广告 搜索广告 展示广告 广告预算
曝光量 点击量 心愿单 收藏量
"""),
    ("合规与标识", 860, """
强制标识 诚信标识 俄罗斯联邦税务局 无证商品 禁售 商品合规 合规标签 报关单 证书 声明 联邦税务局 俄文标签 俄语说明书 认证证书 声明书
俄罗斯商标 Ozon卡 Ozon银行
"""),
    ("店铺运营", 850, """
试穿 回复率 入驻 结算账户 收款渠道 考核指标 订单报告
销售报告 质量把控 违约 处罚 卖家协议 店铺评分
服务评分 卖家评分 节点考核 店铺评级 卖家等级 发货时限 仓库设置
退货点 买家退货 卖家取消 订单处理时间
"""),
    ("俄罗斯市场", 840, """
俄罗斯 莫斯科 圣彼得堡 叶卡捷琳堡 新西伯利亚 喀山
物流集群 本地化 俄语 本土店 新年季 采购价 汇率波动 卢布结算
白俄罗斯 哈萨克斯坦 亚美尼亚 乌兹别克斯坦 吉尔吉斯斯坦
"""),
    ("缩写与代码", 855, """
EAC OzonID OzonGlobal
"""),
]

OTHER = [
    ("通用电商术语", 900, """
跨境电商 出海 外贸 店铺 站点 类目 上架 下架 曝光 点击 点击率
转化率 转化 客单价 复购 复购率 动销 滞销 爆款 选品 测款 新品
老品 起量 冷启动 打新 备货 补货 断货 清仓 库存 库存周转
供销 采购 供应商 工厂 供应链 供货价 议价 核价 比价
定价 折扣 促销 优惠券 秒杀 满减 买赠 捆绑销售 组合购买 优惠码
折扣码 评分 评论 好评 差评 口碑 退款 退款率
售后 客诉 仲裁 索赔 订单量 爆单 毛利 净利 ROI 投入产出比
广告花费 支付成功率 退货率 日均单量 店铺流水
利润率 盈亏平衡 GMV ARPU 周转率 动销率 广告占比 流量 访客
停留时长 跳出率 支付转化 加购 收藏 收藏率
"""),
    ("平台与市场", 895, """
Temu SHEIN TikTokShop Shopee Lazada 速卖通 eBay 沃尔玛 美客多 Coupang
Wildberries 野莓 YandexMarket Joom eMAG Allegro Miravia 独立站 Shopify
B2B B2C C2C 跨境店 个人店 企业店 多站点 新兴市场 拉美
俄罗斯市场 欧洲市场 北美市场 平台佣金 平台规则
阿里国际站 中国制造网 敦煌网 Flipkart MercadoLibre Shopline BigCommerce
WooCommerce Etsy Wayfair Zalando Bol
商家后台 招商 资质 营业执照 店铺权重 官方账号 渠道账号 卖家中心
卖家后台 子账号 主账号 官方旗舰店 代运营 招商经理 卖家平台 服务商
"""),
    ("托管与备货模式", 885, """
全托管 半托管 JIT VMI 备货单 紧急备货单 竞价 首单 虚拟库存
罚款 国内仓 出单 供货 平台代运营 供货模式 平台采购 账期 佣金结算 备货模式 平台核价
议价空间 最低价 妥投 免运 集运 直邮 本地化履约 备货仓 卖家仓
"""),
    ("内容电商", 875, """
达人 达人邀约 精选联盟 橱窗 小黄车 直播带货 短视频带货
挂车 场观 直播 主播 达人佣金 寄样 置换 短视频 千次观看成交
MCN TSP TAP 商城 推荐页 流量池 矩阵 账号矩阵 养号 群控 云控
内容去重 混剪 口播 无人直播 半无人直播 推流 拉流 直播伴侣 弹幕
工会 短视频权重 完播率 直播间 橱窗带货 达人广场 达人分销
达人矩阵 直播切片 商品讲解 直播话术 直播脚本 平台补贴 挂链
爆款视频 短视频素材 直播间场景 内容账号 私域引流
站外达人 内容分销 直播间流量
"""),
    ("东南亚平台", 865, """
SLS 优选卖家 金牌卖家 南宁仓 聊聊 店铺装修 粉丝 关注礼 闪购
店铺券 商品券 运费险 大促 返点 服务费 交易手续费 免运项目
"""),
    ("拉美平台", 860, """
全仓 MercadoPago MercadoEnvios 声誉 绿色声誉 每日促销
订单缺陷 处理时效 州增值税 南共市编码 巴西税号 每日特惠
免息分期 声誉等级
"""),
    ("独立站与站外", 855, """
建站 自建站 模板 落地页 转化漏斗 联盟营销 邮件营销 弃购挽回
支付网关 收款通道 订阅 会员制 网红营销 内容营销 社媒 广告投放
再营销 受众 素材 广告账户 单页 结账 购物车 私域 站外测评
弃单 加购率 结账率 站外推广 红人营销 折扣站 测评
"""),
    ("跨境物流", 845, """
头程 尾程 海外仓 一件代发 代发 小包 专线 双清 包税 派送 清关
报关 退税 结汇 收单 第三方支付 物流商 货代 订舱 拖车 截单 甩柜
爆舱 抛货 计抛 体积重 实重 敏感货 普货 退运 滞港
查验 关税 完税 免税 原产地 装箱单 发票 形式发票 采购单 中转仓
保税仓 头程海运 商检 报关员 海外仓退货 换标服务 打托 贴标服务
海外仓系统 空派 海运专线
回款 提现 汇率 空运 海运 卡航 铁路 双清包税 集货 分拨 收货人
发货人 提货 派送时效 物流轨迹 面单号 清关资料
"""),
    ("合规与认证", 835, """
侵权 认证 包装法 欧代 英代 海牙认证 商标 专利 律师函 冻结 封店
品牌授权 商标注册 专利检索 版权登记 产品合规 检测报告 安全认证
强制认证 海关编码 出口退税 外汇 收汇 结汇额度 查验率 查验放行
侵权判定 知识产权 VAT 授权书 合规 美国代理人 电池法 塑料税
碳关税 海关估价 原产地证 商会认证 CE认证 FCC认证 EPR注册
WEEE注册 欧盟代表 产品责任险
"""),
]

TARGETS = [
    ("亚马逊词库.tsv", AMAZON),
    ("Ozon词库.tsv", OZON),
    ("其他词库.tsv", OTHER),
]

OVERRIDES = {
    # 铺 pū 为「铺开」，pù 为「店铺」；铺货、精铺读 pū
    "铺货": "pu1 huo4", "铺货党": "pu1 huo4 dang3",
    "精铺": "jing1 pu1", "精铺党": "jing1 pu1 dang3",
    # 曝光读 bào guāng，非 pù
    "曝光": "bao4 guang1", "曝光量": "bao4 guang1 liang4",
    # 标识读 biāo zhì，非 biāo shí
    "标识": "biao1 zhi4", "商品标识": "shang1 pin3 biao1 zhi4",
    "诚信标识": "cheng2 xin4 biao1 zhi4", "强制标识": "qiang2 zhi4 biao1 zhi4",
    # 调价读 tiáo jià，非 diào
    "分时调价": "fen1 shi2 tiao2 jia4", "降价比": "jiang4 jia4 bi3",
    # 载 zài
    "下载": "xia4 zai4",
    # 知识读 zhī shi（轻声）
    "知识产权": "zhi1 shi5 chan3 quan2",
    # 铺货的铺读 pū（铺开），非 pù（店铺）
    "铺货模式": "pu1 huo4 mo2 shi4", "精铺模式": "jing1 pu1 mo2 shi4",
    # 清关行指报关行，行读 háng
    "清关行": "qing1 guan1 hang2",
    # 亚马逊的选择是 Amazon's Choice 的中文名，的读 de5
    "亚马逊的选择": "ya4 ma3 xun4 de5 xuan3 ze2",
    # 差异读 chā yì
    "货件差异": "huo4 jian4 cha1 yi4",
    # 切片读 qiē piàn
    "直播切片": "zhi2 bo1 qie1 pian4",
    # 子在本仓库术语里读本调 zi3（子账号、子体、电子钱包）
    "子账号": "zi3 zhang4 hao4", "子体": "zi3 ti3",
    "电子钱包": "dian4 zi3 qian2 bao1",
    # 长尾读 cháng wěi
    "长尾词": "chang2 wei3 ci2",
    # 券 quàn
    "优惠券": "you1 hui4 quan4", "店铺券": "dian4 pu4 quan4",
    "商品券": "shang1 pin3 quan4",
}


def syl_of_han(word):
    syls = lazy_pinyin(word, style=Style.TONE3, neutral_tone_with_five=True,
                       v_to_u=False, errors=lambda x: list(x))
    return syls


def pinyin_of(word):
    if word in OVERRIDES:
        return OVERRIDES[word]
    if HAN.match(word):
        syls = syl_of_han(word)
        if len(syls) != len(word):
            return None
        for s in syls:
            if not re.fullmatch(r"[a-z]+[1-5]", s):
                return None
        return " ".join(syls)
    # 含英文/数字：逐字符，ASCII 原样占一个音节
    out = []
    run = ""
    for ch in word:
        if ASCII.match(ch):
            if run:
                sub = syl_of_han(run)
                if len(sub) != len(run) or any(
                        not re.fullmatch(r"[a-z]+[1-5]", s) for s in sub):
                    return None
                out.extend(sub)
                run = ""
            out.append(ch)
        else:
            run += ch
    if run:
        sub = syl_of_han(run)
        if len(sub) != len(run) or any(
                not re.fullmatch(r"[a-z]+[1-5]", s) for s in sub):
            return None
        out.extend(sub)
    return " ".join(out)


def existing_words():
    """判重集：排除派生文件与语料型大库。

    主题型词库不能拿 文学作品/文学作品词库.tsv（97 万条古典诗文语料）判重：
    它偶然收录了大量通用词（店铺、促销、折扣、库存），据它判重会把电商核心词
    全数剔除，主题库只剩冷僻词、失去自洽。派生文件（综合库、合集）同理排除，
    否则重跑时会把上次输出当成既有库，写出空文件。
    """
    seen = {}
    skip_files = {"综合词库.qj", "综合词库.tsv", "游戏词库合集.qj",
                  "文学作品词库.tsv"}
    for p in glob.glob(os.path.join(REPO, "**", "*.tsv"), recursive=True):
        rel = os.path.relpath(p, REPO)
        if rel.startswith("电商" + os.sep):
            continue
        if os.path.basename(p) in skip_files:
            continue
        with io.open(p, encoding="utf-8") as fh:
            for line in fh:
                w = line.split("\t")[0].strip()
                if w:
                    seen.setdefault(w.lower(), rel)
    return seen


def build():
    existing = existing_words()
    owner = {}
    out = []
    problems = []
    overlap = []

    for fname, groups in TARGETS:
        rows = []
        selfdup = []
        for group, base, blob in groups:
            for i, w in enumerate(blob.split()):
                if w != w.strip() or " " in w or "\t" in w:
                    problems.append(("词面含空白", w))
                    continue
                if w.lower() in owner:
                    problems.append(("跨库/库内重复", "%s 已在 %s" % (w, owner[w.lower()])))
                    continue
                if len(w) < 2:
                    problems.append(("单字词", w))
                    continue
                py = pinyin_of(w)
                if not py:
                    problems.append(("拼音不可用", w))
                    continue
                if len(py.split(" ")) != len(w):
                    problems.append(("音节点数不符", "%s %s" % (w, py)))
                    continue
                freq = max(base - min(i // 6, 6) * 10, base - 60)
                owner[w.lower()] = fname
                if w.lower() in existing:
                    # 既有源词库已收，按仓库「新词库不与既有词库重复」规则剔除
                    overlap.append((w, fname, existing[w.lower()]))
                    continue
                rows.append((w, py, freq))
        rows.sort(key=lambda r: (-r[2], r[1], r[0]))
        out.append((fname, rows))

    return out, problems, overlap


def main():
    out, problems, overlap = build()
    if problems:
        print("异常 %d 条：" % len(problems))
        for p in problems:
            print("  %s: %s" % p)
        return 1
    total = 0
    for fname, rows in out:
        if not rows:
            print("%s 词条为 0，拒绝写出" % fname, file=sys.stderr)
            return 1
        path = os.path.join(OUTDIR, fname)
        os.makedirs(OUTDIR, exist_ok=True)
        with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
            for w, py, fr in rows:
                fh.write("%s\t%s\t%d\n" % (w, py, fr))
        total += len(rows)
        print("写出 %s：%d 条，词频 %d—%d" % (
            fname, len(rows), min(r[2] for r in rows), max(r[2] for r in rows)))
    print("合计 %d 条" % total)
    if overlap:
        print("与既有源库同名 %d 条：" % len(overlap))
        for w, fname, src in overlap:
            print("  %s (%s) ← %s" % (w, fname, src))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
