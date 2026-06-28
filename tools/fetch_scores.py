"""
河小阳 (gaokao.haedu.cn) 录取分数数据获取工具
从 SSR HTML + API 获取院校历年专业录取数据

用法: python3 fetch_scores.py <学校国标代码> [学校国标代码...]
示例: python3 fetch_scores.py 10006 10055 10002
"""
import requests, re, json, sys

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Content-Type": "application/json"
}
API = "https://www.gaokao.haedu.cn/api"


def discover_category_code(school_code):
    """从学校首页发现 category_code 和 category_id"""
    # 先访问学校首页，找到 score/cutoff/list_X_1.html 链接
    try:
        home_url = f"https://{school_code}.gaokao.haedu.cn/"
        html = requests.get(home_url, headers=HEADERS, timeout=10).text
        m = re.search(r"score/cutoff/list_(\d+)_1\.html", html)
        if m:
            cid = m.group(1)
            # 访问该页面获取 category_code
            score_url = f"https://{school_code}.gaokao.haedu.cn/score/cutoff/list_{cid}_1.html"
            html2 = requests.get(score_url, headers=HEADERS, timeout=10).text
            cc = re.search(r"category_code[:\s]*`?(\d+)`?", html2)
            if cc:
                return cc.group(1), cid
    except:
        pass
    return None, None


def get_school_info(school_code):
    """从 SSR 页面获取学校基本信息"""
    url = f"https://{school_code}.gaokao.haedu.cn/score/cutoff/list_269_1.html"
    try:
        html = requests.get(url, headers=HEADERS, timeout=10).text
        name_m = re.search(r"<h2>([^<]+)</h2>", html)
        enroll_m = re.search(r'招生代码[^<]*</el-tooltip>\s*<span>\s*(\d+)', html)
        return {
            "school_name": name_m.group(1) if name_m else "",
            "enroll_code": enroll_m.group(1) if enroll_m else "",
        }
    except:
        return {}


def fetch_page(school_code, category_code, year, fc_code, batch_code, page):
    """获取单页数据"""
    params = {
        "gb_code": school_code, "category": 1, "year": year,
        "category_code": category_code, "page": page, "page_size": 10,
    }
    if fc_code:
        params["first_choice_code"] = fc_code
    if batch_code:
        params["batch_code"] = batch_code

    resp = requests.post(f"{API}/zy_admission/index", json=params, headers=HEADERS, timeout=15)
    if resp.status_code != 200:
        return [], 0
    d = resp.json()
    if d.get("code") != 1:
        return [], 0
    return d.get("data", {}).get("data", []), d.get("data", {}).get("nums", 0)


def fetch_all_pages(school_code, category_code, year, fc_code, batch_code):
    """获取所有分页数据"""
    all_records = []
    page = 1
    while True:
        records, total = fetch_page(school_code, category_code, year, fc_code, batch_code, page)
        if not records:
            break
        all_records.extend(records)
        if len(all_records) >= total:
            break
        page += 1
    return all_records


def scrape_school(school_code):
    """抓取一个学校的所有年份录取数据"""
    info = get_school_info(school_code)
    cat_code, _ = discover_category_code(school_code)
    if not cat_code:
        return None

    name = info.get("school_name", school_code)
    print(f"\n{'='*60}")
    print(f"  {name} (国标: {school_code}, 招生代码: {info.get('enroll_code','?')})")
    print(f"{'='*60}")

    s = requests.Session()
    s.headers.update(HEADERS)
    all_data = {}

    for year in ["2025", "2024", "2023"]:
        try:
            r = s.post(f"{API}/zy_admission/batch",
                       json={"gb_code": school_code, "category": 1, "year": year,
                             "category_code": cat_code}, timeout=10)
            batches = r.json().get("data", [])
        except:
            continue

        for batch in batches:
            batch_name = batch["batch"]
            batch_code = batch["batch_code"]

            try:
                r = s.post(f"{API}/zy_admission/subject",
                           json={"gb_code": school_code, "category": 1, "year": year,
                                 "category_code": cat_code, "batch_code": batch_code}, timeout=10)
                subjects = r.json().get("data", [])
            except:
                subjects = []

            if not subjects:
                records = fetch_all_pages(school_code, cat_code, year, None, batch_code)
                if records:
                    key = f"{year}|{batch_name}"
                    all_data[key] = records
                    print(f"  {key}: {len(records)} records")
            else:
                for subj in subjects:
                    subj_name = subj["first_choice"]
                    subj_code = subj["first_choice_code"]
                    if subj_name not in ["物理", "理科"]:
                        continue  # 只抓物理/理科
                    records = fetch_all_pages(school_code, cat_code, year, subj_code, batch_code)
                    if records:
                        key = f"{year}|{batch_name}|{subj_name}"
                        all_data[key] = records
                        print(f"  {key}: {len(records)} records")

    return {"info": info, "data": all_data}


def print_summary(result):
    data = result["data"]
    info = result["info"]
    name = info.get("school_name", "?")

    for key in sorted(data.keys()):
        records = data[key]
        parts = key.split("|")
        year, batch = parts[0], parts[1]
        subj = parts[2] if len(parts) > 2 else ""

        # 按专业组分组
        groups = {}
        for r in records:
            gc = r.get("major_group_code") or "_none"
            if gc not in groups:
                groups[gc] = {"majors": [], "scores": []}
            groups[gc]["majors"].append(r)
            s = r.get("admission_score_min", "")
            if s:
                groups[gc]["scores"].append(int(s))

        print(f"\n--- {year} {batch} {subj} ---")
        for gc, g in sorted(groups.items()):
            lo = min(g["scores"]) if g["scores"] else "?"
            hi = max(g["scores"]) if g["scores"] else "?"
            gc_label = f"专业组 {gc}" if gc != "_none" else "院校级"
            print(f"  {gc_label}: {len(g['majors'])}条 最低分 {lo}~{hi}")

            for m in g["majors"][:8]:  # 最多显示8个
                mn = m.get("major_name") or "(院校总体)"
                lo_s = m.get("admission_score_min", "")
                hi_s = m.get("admission_score_max", "")
                plan = m.get("major_plan", "")
                enrolled = m.get("admission_num", "")
                score_str = f"最低{lo_s} 最高{hi_s}" if lo_s else "分数未公布"
                code = m.get("major_enrollment_code", "")
                code_str = f"[{code}]" if code else ""
                print(f"    {code_str} {mn}: {score_str} | 计划{plan} 录取{enrolled}")
            if len(g["majors"]) > 8:
                print(f"    ... 还有 {len(g['majors'])-8} 个专业")


if __name__ == "__main__":
    schools = sys.argv[1:] if len(sys.argv) > 1 else ["10006"]
    for code in schools:
        result = scrape_school(code)
        if result:
            print_summary(result)
        else:
            print(f"\nWARNING: Cannot fetch data for {code}")
