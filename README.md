# 自用青简词库

青简输入法自用词库，覆盖番剧名称、国际新闻、网络热梗与国内舆论事件。

## 目录内容

| 文件 | 词条数 | 内容 |
| --- | ---: | --- |
| `综合词库.qj` | 14065 | 四个源词库去重合并（TSV 内容，`.qj` 后缀） |
| `日番名称词库.tsv` | 8289 | 日本动画番剧中文名 |
| `国际新闻事件词库.tsv` | 4471 | 2021—2026 国际事件新闻词：国家、城市、人物、组织、事件、术语 |
| `国内舆论事件词库.tsv` | 1265 | 国内舆论事件相关词 |
| `国番名称词库.tsv` | 891 | 国产动画番剧名：TV 动画、网络动画、泡面番、子供向系列，不含院线动画电影 |
| `网络热梗缩略词库.tsv` | 489 | 网络热梗与缩略语 |

## 文件格式

每行一条词条，三个字段以 Tab 分隔。

```
青简	qing jian	100
```

- 第一列 词面：词内不含空格。
- 第二列 拼音：逐音节以空格分隔，可带数字声调（`ni3 hao3`），轻声写 5 或 0。
- 第三列 词频：正整数，按常用度分档。

拼音中 ü 写作 `v`，写成 `lue` / `nue` 的同样识别。文件为 UTF-8 编码、`\n` 行尾，末行保留换行。

## 综合词库

`综合词库.qj` 由源词库按词面去重合并：词频取各源最大值，排序为词频降序、同频按拼音升序、再按词面。当前版本合并的是日番、国际新闻、国番、网络热梗四个源库，尚未包含 `国内舆论事件词库.tsv`。

## 许可证

MIT License

Copyright (c) 2026 cccchiban

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
