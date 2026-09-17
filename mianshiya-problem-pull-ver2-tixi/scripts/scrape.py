"""
面试鸭题库爬虫 — 调用后端 API 拉取题目，只输出 JSON 数据（供后续知识体系分类）
用法：
    python scrape.py <bank_url> [output_dir]

示例：
    python scrape.py https://www.mianshiya.com/bank/1791003439968264194 ./output

API: POST https://api.mianshiya.com/api/question_bank/list_question
难度映射: 1=简单, 3=中等, 5=困难
输出: <主题名>·题目数据.json（含 id/title/difficulty/questionNum/url）
"""

import json
import re
import sys
import argparse
from pathlib import Path
from typing import List, Dict

import requests

API_URL = "https://api.mianshiya.com/api/question_bank/list_question"
DIFFICULTY_MAP = {1: "简单", 3: "中等", 5: "困难"}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Content-Type": "application/json",
    "Origin": "https://www.mianshiya.com",
    "Referer": "https://www.mianshiya.com/",
}


def extract_bank_id(url: str) -> str:
    """从面试鸭题库 URL 中提取 bank_id"""
    m = re.search(r"/bank/(\d+)", url)
    if m:
        return m.group(1)
    raise ValueError(f"无法从 URL 中提取题库 ID: {url}")


def fetch_topic_name(bank_id: str) -> str:
    """从页面标题提取主题名称，如 'MySQL 面试题'"""
    try:
        url = f"https://www.mianshiya.com/bank/{bank_id}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        m = re.search(r"<title>([^<]+)</title>", resp.text)
        if m:
            return m.group(1).split(" - ")[0].strip()
    except Exception:
        pass
    return "面试题清单"


def fetch_questions(bank_id: str) -> List[Dict]:
    """通过 API 获取全部题目"""
    payload = {
        "current": "1",
        "pageSize": "200",
        "questionBankId": bank_id,
        "tagList": [],
    }

    resp = requests.post(API_URL, json=payload, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != 0:
        raise RuntimeError(f"API 返回错误: {data.get('message', 'unknown')}")

    records = data["data"]["records"]
    total = int(data["data"]["total"])
    print(f"  API 返回: total={total}, 实际获取={len(records)}")
    return records


def build_question_list(records: List[Dict], bank_id: str) -> List[Dict]:
    """将 API 记录转为题目列表"""
    questions = []
    for r in records:
        diff_num = r.get("difficulty", 3)
        difficulty = DIFFICULTY_MAP.get(diff_num, "中等")
        questions.append({
            "id": r["id"],
            "title": r["title"],
            "difficulty": difficulty,
            "questionNum": r.get("questionNum", ""),
            "url": f"https://www.mianshiya.com/bank/{bank_id}/question/{r['id']}",
        })
    return questions


def main():
    parser = argparse.ArgumentParser(description="面试鸭题库爬虫（仅输出 JSON）")
    parser.add_argument("url", help="面试鸭题库 URL，如 https://www.mianshiya.com/bank/123456")
    parser.add_argument("output_dir", nargs="?", default=".", help="输出目录（默认当前目录）")
    args = parser.parse_args()

    bank_id = extract_bank_id(args.url)
    topic_name = fetch_topic_name(bank_id)
    output_path = Path(args.output_dir)

    print(f"题库 ID: {bank_id}")
    print(f"主题名称: {topic_name}")

    records = fetch_questions(bank_id)
    questions = build_question_list(records, bank_id)
    print(f"共获取 {len(questions)} 道题目")

    stats = {"简单": 0, "中等": 0, "困难": 0}
    for q in questions:
        stats[q["difficulty"]] += 1
    print(f"简单: {stats['简单']} | 中等: {stats['中等']} | 困难: {stats['困难']}")

    output_path.mkdir(parents=True, exist_ok=True)
    json_file = output_path / f"{topic_name}·题目数据.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

    print(f"\nJSON 数据: {json_file.resolve()}")


if __name__ == "__main__":
    main()
