import requests, json, sys, re

HEADERS = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}
API = "https://www.gaokao.haedu.cn/api"

# 一分一段表 (分数→位次)
SRM = {
    "2025": {710:12,700:108,690:416,682:961,680:1146,670:2579,666:3387,664:3603,660:4874,650:8281,640:12870,630:18923,620:26385,610:35524,600:45887,590:57947,580:71205,570:85847,560:101279,550:117829,540:135096,535:143976,530:153170,520:171586,510:190228,500:209695,490:229094,480:248687,470:268081,460:287531,450:306451,440:324967,427:348358,420:360436,410:377411,400:393449},
    "2024": {709:10,700:52,690:215,680:573,670:1246,660:2272,650:3784,640:5855,630:8810,620:12607,610:17519,600:23638,590:30887,580:39605,570:49566,560:60745,550:73108,540:86324,530:100737,520:115830,511:130195,510:131720,500:147838,490:164286,480:181368,470:198702,460:216209,450:234011,440:251873,430:269913,420:287723,410:305325,400:322650,396:329573},
    "2023": {710:11,700:74,690:219,680:546,670:1089,660:1934,650:3275,640:5126,630:7810,620:11310,610:15925,600:21690,590:28881,580:37479,570:47216,560:58304,550:70991,540:84884,530:99673,520:115516,514:125465,510:132206,500:149644,490:167514,480:185833,470:204468,460:223738,450:243094,440:262241,430:281485,420:300076,410:318459,409:320263,400:336219},
}

def rank_from_score(score, year):
    s = int(score)
    keys = sorted(SRM.get(year, {}).keys(), reverse=True)
    for k in keys:
        if s >= k:
            return SRM[year][k]
    return None

def discover_cat_code(national_code):
    """从学校首页发现 category_code"""
    try:
        r = requests.get(f"https://{national_code}.gaokao.haedu.cn/", headers=HEADERS, timeout=8)
        m = re.search(r"score/cutoff/list_(\d+)_1\.html", r.text)
        if m:
            r2 = requests.get(f"https://{national_code}.gaokao.haedu.cn/score/cutoff/list_{m.group(1)}_1.html", headers=HEADERS, timeout=8)
            cc = re.search(r"category_code[:\s]*`?(\d+)`?", r2.text)
            if cc:
                return cc.group(1)
    except:
        pass
    return None

def fetch_year_data(national_code, cat_code, year):
    """获取某年录取数据"""
    try:
        resp = requests.post(f"{API}/zy_admission/index", json={
            "page":1, "page_size":50, "category":1,
            "gb_code": national_code, "year": year,
            "batch_code":"", "first_choice_code":"",
            "major_enrollment_code":"", "major_name":"",
            "category_code": cat_code, "keyword":""
        }, headers=HEADERS, timeout=15)
        data = resp.json()
        if data.get("code") == 1:
            return data.get("data", {}).get("data", [])
    except:
        pass
    return []

def filter_physics(records):
    """筛选物理/理科记录"""
    return [r for r in records if (r.get("first_choice","")).find("物理")>=0 or (r.get("first_choice","")).find("理科")>=0]

def summarize_groups(records):
    """按专业组汇总: 每组的最低分、最低位次、专业列表"""
    groups = {}
    for r in records:
        gc = r.get("major_group_code") or "_none"
        if gc not in groups:
            groups[gc] = {"scores": [], "majors": []}
        s = r.get("admission_score_min", "")
        if s:
            groups[gc]["scores"].append(int(s))
        groups[gc]["majors"].append({
            "code": r.get("major_enrollment_code", ""),
            "name": r.get("major_name", ""),
            "score_min": r.get("admission_score_min", ""),
            "score_max": r.get("admission_score_max", ""),
            "score_avg": r.get("admission_score_average", ""),
            "plan": r.get("major_plan", ""),
            "enrolled": r.get("admission_num", ""),
            "require": r.get("major_optional_require", ""),
        })
    return groups

# 学校列表 (从数据文件获取)
SCHOOLS = {
    "北京航空航天大学": "10006",
    "中国人民大学": "10002",
    "北京理工大学": "10007",
    "西安交通大学": "10698",
    "东南大学": "10286",
    "北京邮电大学": "10013",
    "电子科技大学": "10614",
    "武汉大学": "10486",
    "南开大学": "10055",
    "西北工业大学": "10699",
    "山东大学": "10422",
    "哈尔滨工业大学(威海)": "19213",
    "重庆大学": "10611",
    "华南理工大学": "10561",
    "吉林大学": "10183",
    "北京师范大学": "10027",
    "北京交通大学": "10004",
    "华东师范大学": "10269",
    "四川大学": "10610",
    "厦门大学": "10384",
    "湖南大学": "10532",
    "南京理工大学": "10288",
    "北京科技大学": "10008",
    "哈尔滨工程大学": "10217",
    "北京师范大学(珠海校区)": "19027",
}

all_results = {}

for name, code in SCHOOLS.items():
    print(f"\n=== {name} ({code}) ===")
    cat = discover_cat_code(code)
    if not cat:
        print(f"  FAIL: no category_code")
        continue

    school_data = {"name": name, "national_code": code, "years": {}}
    for year in ["2025", "2024", "2023"]:
        records = fetch_year_data(code, cat, year)
        phys = filter_physics(records)
        if phys:
            groups = summarize_groups(phys)
            # 计算每组最低分和位次
            for gc, gdata in groups.items():
                if gdata["scores"]:
                    min_s = min(gdata["scores"])
                    gdata["min_score"] = min_s
                    gdata["min_rank"] = rank_from_score(min_s, year)
                else:
                    gdata["min_score"] = None
                    gdata["min_rank"] = None
            school_data["years"][year] = groups
            print(f"  {year}: {sum(len(g['majors']) for g in groups.values())} majors in {len(groups)} groups")
        else:
            print(f"  {year}: no physics data")

    all_results[code] = school_data

with open("all_schools_data.json", "w", encoding="utf-8") as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)
print(f"\nDone. {len(all_results)} schools saved to all_schools_data.json")
