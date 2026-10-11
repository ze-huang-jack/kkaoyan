#!/usr/bin/env python3
"""
滚动复习追踪器 —— 读「复习登记.md」，算出哪些章该复习了，生成「00复习清单.md」。

核心逻辑：
    上次复习日期  来自 复习登记.md（你手工维护，唯一数据源）
    初次学习日期  来自 git 最后提交时间（自动，不用你管）
    间距天数       = 今天 - max(上次复习, 初次学习)
    排序权重       = 间距天数 × 科目系数（系数反映复习一章要花多久）
                   → 耗时短的科目排在前面，让你能用碎片时间先清掉一批

用法：
    python3 scripts/review.py                  # 重新生成 00复习清单.md
    python3 scripts/review.py mark "第5章 树与二叉树" --count 3
                                               # 复习完某章，记一笔
    python3 scripts/review.py --dry-run        # 只看结果，不写文件
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

# ─────────────────────────── 配置 ───────────────────────────

VAULT = Path(__file__).resolve().parent.parent
LEDGER = VAULT / "复习登记.md"
OUTPUT = VAULT / "00复习清单.md"

# 扫描哪些目录（政治、英语目前是空的，将来有笔记会自动被带上）
SCAN_DIRS = ["01政治", "02english", "03math", "04专业课408"]
SKIP_FILES = {"未命名.md", "placeholder.md", "notes.md", ".DS_Store"}
# 这些文件夹不进追踪：工具缓存、图片、封面
SKIP_DIRNAMES = {".obsidian", ".claudian", "pics", "Excalidraw", "子文件夹-封面"}
# 不按考纲要求掌握的内容，不占用复习位
SKIP_DIRS = {"数学竞赛"}

# 科目系数：复习一章大概要花多久。
#   系数大 = 遗忘更快 / 复习更贵 → 同样天数下排更前面
#   数据结构一章要写代码刷题，3 小时起步，故意压低，免得天天堵在清单最上面
#   改这里就能调整你每天的复习重心
SUBJECT_WEIGHT = {
    "数据结构": 0.6,
    "计算机组成原理": 1.0,
    "操作系统": 1.0,
    "计算机网络": 1.0,
    "高等数学": 1.3,
    "线性代数": 1.1,
    "概率论": 1.0,
    "政治": 0.8,
    "英语": 0.7,
}

# 天数分档
URGENT_DAYS = 14   # 超过这个天数没碰 → 紧急
DUE_DAYS = 7       # 超过这个天数没碰 → 该复习了

# 章级笔记：「第1章 极限」「第二章 一元函数微分学」「第3.2节 xxx」
CHAPTER_RE = re.compile(r"^第\s*[0-9一二三四五六七八九十]+\s*章")
SECTION_RE = re.compile(r"^第\s*[0-9]+\.[0-9]+\s*节")
# 复盘类笔记单独作为学习节点：「极值点 复盘」
REVIEW_NOTE_RE = re.compile(r"复盘$")


# ─────────────────────────── 工具 ───────────────────────────

def today() -> date:
    return date.today()


def days_between(a: date, b: date) -> int:
    return (a - b).days


def fmt(d: date | None) -> str:
    return d.isoformat() if d else "—"


def pretty_unit(unit_raw: str) -> str:
    """单元显示名：先剥掉文件夹排序前缀（01_、02-），再把英文目录名换中文。"""
    s = unit_raw.replace("_", " ").strip()
    s = re.sub(r"^\d+\s*[-.、]?\s*", "", s)      # "01 高等数学" → "高等数学"
    for eng, zh in (("data structures and algorithm", "数据结构"),
                    ("computer organization and architechture", "计组"),
                    ("computer organization and architecture", "计组"),
                    ("computer operating system", "操作系统")):
        s = re.sub(re.escape(eng), zh, s, flags=re.IGNORECASE)
    return re.sub(r"\s*·\s*", "·", s).strip("·")


def subject_of(rel_path: str) -> str | None:
    """把笔记路径映射到科目名。"""
    p = rel_path.replace("\\", "/")
    if p.startswith("03math/"):
        if "线性代数" in p:
            return "线性代数"
        if "概率论" in p:
            return "概率论"
        if "高等数学" in p:
            return "高等数学"
        return "高等数学"
    if p.startswith("04专业课408/"):
        if "data_structures" in p:
            return "数据结构"
        if "computer_organization" in p:
            return "计算机组成原理"
        if "operating_system" in p:
            return "操作系统"
        if "computer_network" in p or "network" in p:
            return "计算机网络"
        return "408其他"
    if p.startswith("01政治/"):
        return "政治"
    if p.startswith("02english/"):
        return "英语"
    return None


def git_last_commit(rel_path: str) -> date | None:
    """某文件最后一次被提交的日期。git 没记录则返回 None。"""
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%ad", "--date=short", "--", rel_path],
            cwd=VAULT, capture_output=True, text=True, timeout=10,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    s = out.stdout.strip()
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None


# ─────────────────────────── 登记表读写 ───────────────────────────

LEDGER_HEADER = """---
created: {created}
tags:
  - 复习
  - 复盘
---

# 复习登记

> **这是整个复习系统的唯一数据源，也是你每天唯一需要动手改的文件。**
> 复习完一章，把它的「最后复习」改成今天，完事（约 10 秒）。
>
> 命令行更快一档（推荐）：
> ```
> python3 scripts/review.py mark "第5章 树与二叉树"
> ```
> 不习惯命令行就直接在下面表格里改日期，效果完全一样。
>
> **首次学习日期** 不用你填——脚本自动读 git 提交历史。新学的章，第一次复习前
> 「最后复习」留 `—` 就行。

"""


def parse_ledger() -> dict[str, dict]:
    """
    读 复习登记.md，返回 {单元键: {subject, display, last_review, count}}。
    科目从 `## 科目名` 标题推断——表格里只有 3 列。
    """
    if not LEDGER.exists():
        return {}
    entries: dict[str, dict] = {}
    subject = ""
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        h = re.match(r"^##\s+(.+?)\s*$", line)
        if h:
            subject = h.group(1).strip()
            continue
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        content, last, cnt = cells[0], cells[1], cells[2]
        if not content or content in ("复习单元", "内容"):
            continue
        if set(content) <= set("-: "):   # 分隔行 | --- | --- | --- |
            continue
        entries[content] = {
            "subject": subject,
            "display": content,
            "last_review": parse_date_cell(last),
            "count": int(cnt) if cnt.isdigit() else 0,
        }
    return entries


def parse_date_cell(s: str) -> date | None:
    s = s.strip().strip("`")
    if not s or s in ("—", "-", "未学", "未复习"):
        return None
    m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def write_ledger(entries: dict[str, dict], created: str) -> None:
    """按科目分段重写登记表，保持 Markdown 表格格式（Obsidian 友好）。"""
    # 防呆：登记表里有内容却一条都没解析出来 → 说明格式变了，宁可不写
    if LEDGER.exists() and not entries:
        if any(l.strip().startswith("|") for l in LEDGER.read_text(encoding="utf-8").splitlines()):
            raise RuntimeError(
                f"拒绝覆盖 {LEDGER.name}：文件里有表格行，但解析出 0 条。"
                f"多半是表格格式被改动过，先确认再重跑。"
            )

    by_subject: dict[str, dict[str, dict]] = {}
    for content, e in entries.items():
        by_subject.setdefault(e["subject"], {})[content] = e

    order = list(SUBJECT_WEIGHT.keys())
    subjects = [s for s in order if s in by_subject] + \
               [s for s in by_subject if s not in order]

    parts = [LEDGER_HEADER.format(created=created)]
    for subj in subjects:
        parts.append(f"\n## {subj}\n\n")
        parts.append("| 复习单元 | 最后复习 | 次数 |\n")
        parts.append("| --- | --- | --- |\n")
        for content in sorted(by_subject[subj]):
            e = by_subject[subj][content]
            last = fmt(e["last_review"]) if e["last_review"] else "—"
            disp = e.get("display") or content
            parts.append(f"| {disp} | {last} | {e['count']} |\n")
    LEDGER.write_text("".join(parts), encoding="utf-8")


# ─────────────────────────── 扫描笔记 ───────────────────────────

def scan_notes() -> list[dict]:
    """
    扫描笔记，划分「复习单元」。粒度原则：
        章级笔记（第N章 / 第N.M节 / xxx复盘）→ 每篇一个单元
        主题文件夹（工具箱、基础公式…）      → 整个文件夹一个单元
        科目目录下散落的零散笔记             → 合成「知识点」一个单元
    返回 {subject, unit, unit_raw, rel, first_learn}
    """
    items = []
    for d in SCAN_DIRS:
        root = VAULT / d
        if not root.exists():
            continue
        for f in sorted(root.rglob("*.md")):
            rel_parts = f.relative_to(root).parts
            if any(p.startswith(".") or p in SKIP_DIRNAMES for p in rel_parts):
                continue
            if any(p in SKIP_DIRS for p in rel_parts):
                continue
            if f.name in SKIP_FILES or f.name.startswith("."):
                continue
            rel = str(f.relative_to(VAULT))
            subj = subject_of(rel)
            if not subj:
                continue
            base = f.stem
            if len(rel_parts) > 2:
                # 科目容器 → 主题文件夹 → 笔记：整个主题文件夹当一个复习单元
                unit_raw = rel_parts[1]
                unit = f"{rel_parts[0]}·{unit_raw}"
            elif CHAPTER_RE.match(base) or SECTION_RE.match(base) or REVIEW_NOTE_RE.search(base):
                # 章级 / 节级 / 复盘笔记：自己就是一个复习单元
                unit_raw = base
                unit = base
            else:
                # 散落的零散知识点：合成一个单元
                unit_raw = f"{subj}·知识点"
                unit = unit_raw
            items.append({
                "subject": subj,
                "unit": unit,
                "unit_raw": unit_raw,
                "rel": rel,
                "first_learn": git_last_commit(rel),
            })
    return items


def build_rows() -> list[dict]:
    """把笔记聚合成追踪单元，再用登记表补上「上次复习」。"""
    notes = scan_notes()
    ledger = parse_ledger()

    units: dict[str, dict] = {}
    for n in notes:
        u = units.setdefault(n["unit"], {
            "name": n["unit"],
            "raw": n["unit_raw"],
            "subject": n["subject"],
            "files": [],
            "first_learn": None,
        })
        u["files"].append(n["rel"])
        fl = n["first_learn"]
        if fl and (u["first_learn"] is None or fl > u["first_learn"]):
            u["first_learn"] = fl

    rows = []
    for key, u in units.items():
        e = ledger.get(key, {})
        last_review = e.get("last_review")
        count = e.get("count", 0)
        ref = max([d for d in (last_review, u["first_learn"]) if d], default=None)
        gap = days_between(today(), ref) if ref else None
        weight = SUBJECT_WEIGHT.get(u["subject"], 1.0)
        pretty = pretty_unit(u["raw"])
        rows.append({
            "name": key,
            "display": pretty if pretty.startswith(u["subject"]) else f"{u['subject']}·{pretty}",
            "subject": u["subject"],
            "files": u["files"],
            "first_learn": u["first_learn"],
            "last_review": last_review,
            "count": count,
            "gap": gap,
            "score": (gap * weight) if gap is not None else 9999,
            "registered": key in ledger,
        })

    # 排序：权重分高的在前；同分时复习次数少的在前（更生疏）
    rows.sort(key=lambda r: (-r["score"], r["count"]))
    return rows


# ─────────────────────────── 生成清单 ───────────────────────────

def tier(gap: int | None) -> tuple[str, str]:
    if gap is None:
        return "待学", "还没有 git 记录，或尚未开始"
    if gap >= URGENT_DAYS:
        return "紧急", f"已经 {gap} 天没碰了"
    if gap >= DUE_DAYS:
        return "该复习", f"{gap} 天没碰"
    return "掌握中", f"{gap} 天前刚碰过"


def render_dashboard(rows: list[dict], t: date) -> str:
    urgent = [r for r in rows if r["gap"] is not None and r["gap"] >= URGENT_DAYS]
    due = [r for r in rows if r["gap"] is not None and DUE_DAYS <= r["gap"] < URGENT_DAYS]
    fresh = [r for r in rows if r["gap"] is not None and r["gap"] < DUE_DAYS]
    unreg = [r for r in rows if not r["registered"] and r["gap"] is None]

    out = []
    out.append("---\n")
    out.append(f"updated: {t.isoformat()}\n")
    out.append("tags:\n  - 复习\n---\n\n")
    out.append(f"# 今日复习清单 · {t.isoformat()}\n\n")
    out.append("> [!tip] 这一页每天打开库第一眼看。\n")
    out.append("> 从上往下做，复习完记一笔：\n")
    out.append('> `python3 scripts/review.py mark "单元名"`\n')
    out.append("> 或者直接改 [[复习登记]] 里的日期。\n\n")
    out.append("> [!note] 排序规则：`距今天数 × 科目系数`。系数大 = 复习这章更费时间，"
               "所以是从「碎片时间能清掉的」排到「要留整块时间的」。"
               "「上次复习」为空时，天数按**初次学习**算——"
               "所以第一次打开会看到一片红，那是正常的，"
               "复习一轮标一轮，之后才开始准。\n\n")

    def table(items: list[dict]) -> str:
        lines = ["| 科目 | 复习单元 | 上次复习 | 初次学习 | 距今天数 | 次数 | 篇数 |\n",
                 "| --- | --- | --- | --- | --- | --- | --- |\n"]
        for r in items:
            disp = r["display"]
            if len(r["files"]) >= 20:
                disp += f"（{len(r['files'])} 篇）"
            link = f"[[{Path(r['files'][0]).stem}|{disp}]]" if r["files"] else disp
            last = fmt(r["last_review"]) if r["last_review"] else "—"
            first = fmt(r["first_learn"]) if r["first_learn"] else "—"
            gap = f"**{r['gap']}**" if r["gap"] >= URGENT_DAYS else str(r["gap"])
            lines.append(
                f"| {r['subject']} | {link} | {last} | {first} | {gap} | "
                f"{r['count']} | {len(r['files'])} |\n"
            )
        return "".join(lines) + "\n"

    if urgent:
        out.append(f"## 🔴 紧急（{URGENT_DAYS} 天以上没碰）· {len(urgent)} 章\n\n")
        out.append(table(urgent))
    if due:
        out.append(f"## 🟡 该复习（{DUE_DAYS}–{URGENT_DAYS - 1} 天）· {len(due)} 章\n\n")
        out.append(table(due))
    if fresh:
        out.append(f"## 🟢 刚碰过（{DUE_DAYS} 天内）· {len(fresh)} 章\n\n")
        out.append(table(fresh))

    if unreg:
        out.append(f"## ⚪ 未登记 · {len(unreg)} 项\n\n")
        out.append("这些笔记还没进 [[复习登记]]，补一行就能纳入追踪：\n\n")
        out.append("| 科目 | 内容 |\n| --- | --- |\n")
        for r in unreg:
            out.append(f"| {r['subject']} | {r['name']} |\n")
        out.append("\n")

    out.append("---\n\n")
    out.append("## 怎么用\n\n")
    out.append("**每天**：打开这一页，从最上面挑 1–3 个单元复习，完了记一笔。\n\n")
    out.append("**记一笔**（二选一）：\n")
    out.append('- 命令行：`python3 scripts/review.py mark "数据结构·第5章 树与二叉树"`\n')
    out.append("  （单元名写不全也行，能唯一匹配就认）\n")
    out.append("- 或者打开 [[复习登记]]，把那行的日期改成今天，次数加一\n\n")
    out.append("**清单会刷新**——每次 mark 之后自动重算，不需要手动跑。\n\n")
    out.append("**新学的章**：学完不用管，git 提交后它会自动出现在清单里，"
               "「初次学习」取的就是提交日期。\n\n")
    out.append("**想调复习节奏**：改 `scripts/review.py` 顶部的 `SUBJECT_WEIGHT`，"
               "系数越大排得越靠前。\n\n")
    out.append("**想让某个主题单独追踪**：在科目目录下建个子文件夹放进去，"
               "脚本会自动把它当成一个独立单元（现在高数的工具箱、思想by pika 就是这么分的）。\n")
    return "".join(out)


# ─────────────────────────── 命令 ───────────────────────────

def cmd_mark(name: str, count: int | None, when: date | None, learn: bool) -> int:
    rows = build_rows()
    ledger = parse_ledger()

    # 支持三种写法：登记表键名、显示名（高数·工具箱）、文件名
    key = None
    for r in rows:
        if name in (r["name"], r["display"]) or name in [
            Path(f).stem for f in r["files"]
        ]:
            key = r["name"]
            break
    if key is None:
        near = [r["display"] for r in rows if name in r["display"] or name in r["name"]]
        if len(near) == 1:
            key = next(r["name"] for r in rows if r["display"] == near[0])
        elif len(near) > 1:
            print(f"「{name}」匹配到多个，写完整一点：", file=sys.stderr)
            for n in near:
                print(f"  - {n}", file=sys.stderr)
            return 1
        else:
            print(f"没找到「{name}」。跑一次 `python3 scripts/review.py` "
                  f"看清单里的准确名字。", file=sys.stderr)
            return 1

    row = next(r for r in rows if r["name"] == key)
    e = ledger.get(key) or {"subject": row["subject"], "last_review": None, "count": 0}
    e["subject"] = row["subject"]
    e["display"] = row["display"]

    if learn:
        e["last_review"] = None
        e["count"] = 0
        print(f"✓ {row['display']}：标记为新学（尚未复习过）")
    else:
        e["last_review"] = when or today()
        e["count"] = (count if count is not None else e.get("count", 0) + 1)
        print(f"✓ {row['display']}：{fmt(e['last_review'])}，累计 {e['count']} 次")
    ledger[key] = e

    created = today().isoformat()
    if LEDGER.exists():
        m = re.search(r"created:\s*(\S+)", LEDGER.read_text(encoding="utf-8"))
        if m:
            created = m.group(1)
    write_ledger(ledger, created)
    cmd_report()
    return 0


def cmd_report(dry_run: bool = False) -> int:
    rows = build_rows()
    t = today()
    md = render_dashboard(rows, t)
    if dry_run:
        print(md)
        return 0
    OUTPUT.write_text(md, encoding="utf-8")
    urgent = sum(1 for r in rows if r["gap"] is not None and r["gap"] >= URGENT_DAYS)
    due = sum(1 for r in rows if r["gap"] is not None and DUE_DAYS <= r["gap"] < URGENT_DAYS)
    print(f"已生成 {OUTPUT.name}：🔴 紧急 {urgent} 章 · 🟡 该复习 {due} 章")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="滚动复习追踪器")
    ap.add_argument("--dry-run", action="store_true",
                    help="只打印结果，不写文件（等价于 report --dry-run）")
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("report", help="重新生成清单（默认行为）")
    p.add_argument("--dry-run", action="store_true")

    p = sub.add_parser("mark", help="记一笔复习")
    p.add_argument("name", help="章名或笔记名，如 \"第5章 树与二叉树\"")
    p.add_argument("--count", type=int, default=None, help="累计复习次数")
    p.add_argument("--date", default=None, help="复习日期 YYYY-MM-DD，默认今天")
    p.add_argument("--new", action="store_true", help="标记为新学（次数归零）")

    p = sub.add_parser("init", help="生成空的复习登记.md")
    p.add_argument("--force", action="store_true")

    args = ap.parse_args()

    if args.cmd == "mark":
        when = parse_date_cell(args.date) if args.date else None
        return cmd_mark(args.name, args.count, when, args.new)
    if args.cmd == "init":
        if LEDGER.exists() and not args.force:
            print(f"{LEDGER.name} 已存在，加 --force 覆盖", file=sys.stderr)
            return 1
        write_ledger({}, today().isoformat())
        print(f"已生成 {LEDGER.name}")
        return 0
    dry = args.dry_run or getattr(args, "dry_run", False)
    return cmd_report(dry)


if __name__ == "__main__":
    raise SystemExit(main())
