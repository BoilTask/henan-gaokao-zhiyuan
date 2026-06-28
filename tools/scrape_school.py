"""
河小阳 (gaokao.haedu.cn) 录取数据抓取工具
从服务端渲染的 HTML 中提取历年专业录取分数、位次数据

用法: python3 scrape_school.py <学校国标代码>
示例: python3 scrape_school.py 10006   # 北京航空航天大学
      python3 scrape_school.py 10055   # 南开大学
"""
import requests, re, json, sys

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def extract_history_list(html):
    """从 HTML 中提取 history_list JS 数组"""
    start = html.find("history_list:")
    if start < 0:
        return []
    bracket_start = html.find("[", start)
    if bracket_start < 0:
        return []
    # 追踪嵌套括号
    depth = 0
    pos = bracket_start
    in_string = False
    while pos < len(html):
        c = html[pos]
        if c == "'" and (pos == 0 or html[pos-1] != '\\'):
            in_string = not in_string
        elif not in_string:
            if c == '[':
                depth += 1
            elif c == ']':
                depth -= 1
                if depth == 0:
                    raw = html[bracket_start:pos+1]
                    break
        pos += 1
    else:
        return []

    # Parse JS objects
    results = []
    pos = 0
    while pos < len(raw):
        brace_start = raw.find("{", pos)
        if brace_start < 0:
            break
        depth = 0
        p = brace_start
        in_string = False
        while p < len(raw):
            c = raw[p]
            if c == "'" and (p == 0 or raw[p-1] != '\\'):
                in_string = not in_string
            elif not in_string:
                if c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        obj_str = raw[brace_start+1:p]
                        obj = {}
                        for k, v in re.findall(r"(\w+)\s*:\s*'([^']*)'", obj_str):
                            obj[k] = v
                        if obj.get("major_name"):
                            results.append(obj)
                        pos = p + 1
                        break
            p += 1
        else:
            break
    return results

def get_total_pages(html):
    """提取 total 记录数"""
    m = re.search(r'total:\s*(\d+)', html)
    return int(m.group(1)) if m else 0

def scrape_school(school_code, category_id=269):
    """抓取一个学校的所有录取数据"""
    all_records = []
    page = 1

    while True:
        url = f"https://{school_code}.gaokao.haedu.cn/score/cutoff/list_{category_id}_{page}.html"
        print(f"Fetching: {url}")
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"  -> HTTP {resp.status_code}, stopping")
            break

        html = resp.text
        records = extract_history_list(html)
        total = get_total_pages(html)

        if not records:
            print(f"  -> No records found on page {page}")
            break

        all_records.extend(records)
        print(f"  -> Page {page}: {len(records)} records (total announced: {total})")

        if len(all_records) >= total:
            break
        page += 1

    return all_records

def summarize(records):
    """按年份+专业组汇总"""
    groups = {}
    for r in records:
        year = r.get("year", "?")
        batch = r.get("batch", "?")
        gc = r.get("major_group_code", "?")
        key = f"{year}|{batch}|{gc}"
        if key not in groups:
            groups[key] = {"majors": [], "min_scores": [], "year": year, "batch": batch, "group_code": gc}
        groups[key]["majors"].append(r["major_name"])
        s = r.get("admission_score_min", "")
        if s:
            groups[key]["min_scores"].append(int(s))

    print(f"\n{'='*80}")
    print(f"Total: {len(records)} records across {len(groups)} year/batch/group combinations")
    print(f"{'='*80}")

    for key in sorted(groups.keys()):
        d = groups[key]
        lo = min(d["min_scores"]) if d["min_scores"] else "?"
        hi = max(d["min_scores"]) if d["min_scores"] else "?"
        print(f"\n{d['year']} | {d['batch']} | 专业组 {d['group_code']} | {len(d['majors'])}个专业 | 最低分 {lo}~{hi}")
        for m in d["majors"]:
            print(f"  - {m}")

    return groups


if __name__ == "__main__":
    school_code = sys.argv[1] if len(sys.argv) > 1 else "10006"
    records = scrape_school(school_code)
    if not records:
        print("No data found!")
        sys.exit(1)

    summarize(records)

    # Output JSON
    out_file = f"school_{school_code}_scores.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"\nJSON saved to: {out_file}")
