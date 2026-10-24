"""scel 解析：0x120 组数 → 0x1540 拼音表 → 重码组（每组多词，词后带扩展字段）。"""


def parse_scel(data):
    import struct

    def u16(p):
        return struct.unpack_from("<H", data, p)[0]

    def u32(p):
        return struct.unpack_from("<I", data, p)[0]

    total_groups = u32(0x120)
    pos = 0x1540
    py_count = u16(pos)
    pos += 4
    table = {}
    extra = 0
    for _ in range(py_count):
        idx = u16(pos)
        ln = u16(pos + 2)
        pos += 4
        table[idx] = data[pos:pos + ln].decode("utf-16-le", "replace")
        pos += ln
    order = sorted(table)
    for k, idx in enumerate(order):
        if idx != k:
            extra = max(order) + 1
            break
    if extra:
        for i in range(extra):
            table[extra + i] = chr(97 + i)
    py_table_max = max(table) + 1

    words = []
    for _ in range(total_groups):
        if pos + 2 > len(data):
            break
        repeat = u16(pos)
        pos += 2
        py_size = u16(pos)
        pos += 2
        syl = []
        for _ in range(py_size // 2):
            the = u16(pos)
            pos += 2
            if the >= py_table_max:
                syl.append(chr(the - py_table_max + 97))
            else:
                syl.append(table.get(the, "?"))
        pinyin = " ".join(syl)
        for _ in range(repeat):
            wl = u16(pos)
            pos += 2
            word = data[pos:pos + wl].decode("utf-16-le", "replace")
            pos += wl
            ext = u16(pos)
            pos += 2 + ext
            words.append((word, pinyin))
    return words, pos, len(data)
