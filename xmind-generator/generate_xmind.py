#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate XMind mind map."""

import zipfile
import os
import uuid
import sys

def escape(s):
    if isinstance(s, str):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    return s

class Topic:
    def __init__(self, title):
        self.id = str(uuid.uuid4())
        self.title = title
        self.children = []

    def add(self, title):
        t = Topic(title)
        self.children.append(t)
        return t

    def add_leaf(self, title):
        return self.add(title)

    def to_xml(self):
        inner = f"<title>{escape(self.title)}</title>"
        if self.children:
            child_tags = "".join(c.to_xml() for c in self.children)
            inner += f"<children><topics type=\"attached\">{child_tags}</topics></children>"
        return f'<topic id="{self.id}">{inner}</topic>'

def build_tree():
    root = Topic("MVCC底层原理剖析")

    # ===== 第一章：MVCC概念 =====
    ch1 = root.add("一、MVCC概念")

    c = ch1.add("是什么")
    c.add_leaf("MVCC：Multi-Version Concurrency Control，多版本并发控制")
    c.add_leaf("通过隐藏字段 + Undo Log 版本链 + Read View 维护数据多个版本")

    c = ch1.add("解决什么问题")
    c.add_leaf("让普通读能读到符合可见性规则的历史版本")
    c.add_leaf("解决读写互斥问题，极大提升数据库读写并发效率")
    c.add_leaf("应用于 RC 和 RR 隔离级别，是 InnoDB 高并发的核心")

    # ===== 第二章：undo日志版本链 =====
    ch2 = root.add("二、undo日志版本链")

    c = ch2.add("核心原理")
    c.add_leaf("一行数据被多个事务依次修改后，保留修改前的 undo 回滚日志")
    c.add_leaf("用隐藏字段把 undo 日志串联成历史记录版本链")

    c = ch2.add("两个隐藏字段")
    c.add_leaf("trx_id：最后修改该行的事务 ID")
    c.add_leaf("roll_pointer：指向上一个版本的 undo 日志指针")

    c = ch2.add("两个隐藏列")
    c.add_leaf("DB_TRX_ID：最近修改该行的事务 ID")
    c.add_leaf("DB_ROLL_PTR：指向 undo log 中该行旧版本的回滚指针")

    c = ch2.add("快照读与版本链")
    c.add_leaf("SELECT 快照读时通过 Read View 判断版本链中哪个版本可见")

    # ===== 第三章：read view机制详解 =====
    ch3 = root.add("三、read view机制详解")

    c = ch3.add("一致性视图（快照）")
    c.add_leaf("记录所有未提交事务 id 数组（最小为 min_id）和最大事务 id（max_id）")
    c.add_leaf("查询结果从版本链最新数据逐条与 read-view 比对得到快照结果")

    c = ch3.add("RR vs RC 的 read-view 差异")
    c.add_leaf("RC：每次执行查询都生成新快照，能看到刚提交的新数据")
    c.add_leaf("RR：只在第一次 SELECT 生成快照并在事务期复用，始终一致")

    c = ch3.add("RR vs RC MVCC 实现对比")
    c.add_leaf("read-view 生成时机：RR 第一次查询 vs RC 每次查询")
    c.add_leaf("可见性基准：RR 事务期不变 vs RC 每次最新状态")
    c.add_leaf("解决幻读：RR 通过 MVCC + 间隙锁，RC 不行")

    # ===== 第四章：版本链可见性比对规则 =====
    ch4 = root.add("四、版本链可见性比对规则")

    c = ch4.add("比对流程")
    c.add_leaf("从版本链最新数据开始，逐条与 read-view 比对")

    c = ch4.add("trx_id < min_id")
    c.add_leaf("版本由已提交事务生成，可见")

    c = ch4.add("trx_id > max_id")
    c.add_leaf("版本由将来启动的事务生成，不可见（自己事务除外）")

    c = ch4.add("min_id <= trx_id <= max_id")
    c.add_leaf("trx_id 在视图数组中：未提交事务生成，不可见（自己事务除外）")
    c.add_leaf("trx_id 不在视图数组中：已提交事务生成，可见")

    # ===== 第五章：删除数据的特殊处理 =====
    ch5 = root.add("五、删除数据的特殊处理")

    c = ch5.add("实现方式")
    c.add_leaf("删除视为 update 的特殊情况，复制版本链最新数据")
    c.add_leaf("修改 trx_id 为删除事务 ID，并在头信息 deleted_flag 标记 true")
    c.add_leaf("查询到 deleted_flag 为 true 的记录则不返回数据")

    # ===== 第六章：普通读 vs 当前读 =====
    ch6 = root.add("六、普通读 vs 当前读")

    c = ch6.add("普通读（快照读）")
    c.add_leaf("基于 MVCC 读取事务开始时刻的数据快照")
    c.add_leaf("不加锁，读写互不阻塞，并发性能极高")
    c.add_leaf("可能读到旧数据，标准 SELECT 语句")

    c = ch6.add("当前读（Current Read）")
    c.add_leaf("强制读取最新已提交数据并加锁")
    c.add_leaf("SELECT ... FOR UPDATE 加排他锁")
    c.add_leaf("SELECT ... LOCK IN SHARE MODE 加共享锁（8.0 用 FOR SHARE）")
    c.add_leaf("UPDATE / DELETE / INSERT 都是当前读")

    c = ch6.add("两者对比")
    c.add_leaf("本质：读历史版本 vs 读最新版本")
    c.add_leaf("实现：MVCC + Undo Log vs 锁机制")
    c.add_leaf("性能：普通读高、当前读较低")

    # ===== 第七章：RC与RR隔离级别下的快照差异 =====
    ch7 = root.add("七、RC与RR隔离级别下的快照差异")

    c = ch7.add("RC：语句级快照")
    c.add_leaf("每条 SQL 执行时重新生成 Read View，同事务不同 SQL 可能读到不同版本")

    c = ch7.add("RR：事务级快照")
    c.add_leaf("整个事务使用同一个 Read View，保证事务内所有 SQL 看到的数据一致")

    # ===== 第八章：全文总结 =====
    ch8 = root.add("📋 全文总结")

    c = ch8.add("MVCC 实现原理")
    c.add_leaf("undo 日志版本链 + read-view 可见性比对 = MVCC")
    c.add_leaf("RR 下 read-view 事务内不变，RC 下每次查询重新生成")

    c = ch8.add("快照读 vs 当前读")
    c.add_leaf("快照读（SELECT）：读历史版本，不加锁")
    c.add_leaf("当前读（UPDATE/DELETE/FOR UPDATE）：读最新版本，加锁")

    c = ch8.add("RC 与 RR 的快照差异")
    c.add_leaf("RC：语句级快照，每次 SQL 刷新 Read View")
    c.add_leaf("RR：事务级快照，整个事务一个 Read View")

    c = ch8.add("关键 SQL 速记")
    c.add_leaf("普通读：SELECT ...（不加锁）")
    c.add_leaf("当前读：SELECT ... FOR UPDATE / LOCK IN SHARE MODE")

    return root

def create_xmind(output_path):
    root = build_tree()

    content_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<xmap-content xmlns="urn:xmind:xmap:xmlns:content:2.0" xmlns:fo="http://www.w3.org/1999/XSL/Format" xmlns:svg="http://www.w3.org/2000/svg" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xn="urn:xmind:xmap:xmlns:content:2.0" timestamp="1751270400000" version="2.0">
<sheet id="''' + str(uuid.uuid4()) + '''" timestamp="1751270400000">
''' + root.to_xml() + '''
</sheet>
</xmap-content>'''

    meta_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<meta xmlns="urn:xmind:xmap:xmlns:meta:2.0" version="2.0">
<Author><Name>Claude Code</Name></Author>
<Create><Time>1751270400</Time></Create>
</meta>'''

    manifest_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<manifest xmlns="urn:xmind:xmap:xmlns:manifest:1.0">
<file-entry full-path="content.xml" media-type="text/xml"/>
<file-entry full-path="meta.xml" media-type="text/xml"/>
</manifest>'''

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('content.xml', content_xml.encode('utf-8'))
        zf.writestr('meta.xml', meta_xml.encode('utf-8'))
        zf.writestr('META-INF/manifest.xml', manifest_xml.encode('utf-8'))

    file_size = os.path.getsize(output_path)
    print(f"[OK] XMind file generated!")
    print(f"   Path: {output_path}")
    print(f"   Size: {file_size:,} bytes")
    print(f"   Done.")

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        output_dir = sys.argv[1]
        filename = sys.argv[2] if len(sys.argv) >= 3 else "思维导图.xmind"
    else:
        output_dir = os.path.dirname(os.path.abspath(__file__))
        filename = "思维导图.xmind"
    output_path = os.path.join(output_dir, filename)
    create_xmind(output_path)
