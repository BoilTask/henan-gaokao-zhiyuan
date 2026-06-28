"""
匹配河小阳爬取数据到志愿表，生成更新后的数据文件
"""
import json, re, difflib

# 一分一段表
SRM = {
    "2025": {710:12,700:108,690:416,682:961,680:1146,670:2579,666:3387,664:3603,660:4874,650:8281,640:12870,630:18923,620:26385,610:35524,600:45887,590:57947,580:71205,570:85847,560:101279,550:117829,540:135096,535:143976,530:153170,520:171586,510:190228,500:209695,490:229094,480:248687,470:268081,460:287531,450:306451,440:324967,427:348358},
    "2024": {709:10,700:52,690:215,680:573,670:1246,660:2272,650:3784,640:5855,630:8810,620:12607,610:17519,600:23638,590:30887,580:39605,570:49566,560:60745,550:73108,540:86324,530:100737,520:115830,511:130195,500:147838,490:164286,480:181368,470:198702,460:216209,450:234011,440:251873,430:269913,420:287723,410:305325,400:322650},
    "2023": {710:11,700:74,690:219,680:546,670:1089,660:1934,650:3275,640:5126,630:7810,620:11310,610:15925,600:21690,590:28881,580:37479,570:47216,560:58304,550:70991,540:84884,530:99673,520:115516,514:125465,500:149644,490:167514,480:185833,470:204468,460:223738,450:243094,440:262241,430:281485,420:300076,410:318459,400:336219},
}

def rank_from_score(score, year):
    s = int(score)
    keys = sorted(SRM.get(year, {}).keys(), reverse=True)
    for k in keys:
        if s >= k:
            return SRM[year][k]
    return None

def fuzzy_match(a, b):
    """模糊匹配两个字符串"""
    a = a.strip().replace(" ", "").replace("（", "(").replace("）", ")")
    b = b.strip().replace(" ", "").replace("（", "(").replace("）", ")")
    if a == b:
        return True
    # 包含关系
    if a in b or b in a:
        return True
    # 相似度
    return difflib.SequenceMatcher(None, a, b).ratio() > 0.7

with open("../data/all_schools_data.json", encoding="utf-8") as f:
    school_data = json.load(f)

with open("../data/volunteer_data_current.json", encoding="utf-8") as f:
    volunteer = json.load(f)

uncertain = []
updated_groups = 0
updated_majors = 0

for g in volunteer["groups"]:
    name = g["schoolName"]
    scode = g["config"].get("nationalCode", "")

    if not scode or scode not in school_data:
        continue

    sd = school_data[scode]
    gc_user = g["groupCode"]  # 用户填的专业组代码，如 "101", "G01"

    # 为每个年份收集匹配的数据
    group_history = []  # [{year, rank, score}]

    for year in ["2025", "2024", "2023"]:
        ydata = sd["years"].get(year, {})
        if not ydata:
            continue

        # 尝试匹配专业组
        best_match = None
        best_score = None

        # 精确匹配: 专业组代码一致
        if gc_user in ydata:
            gdata = ydata[gc_user]
            if gdata["min_score"]:
                best_match = gc_user
                best_score = gdata["min_score"]
        else:
            # 模糊匹配
            for gc_api, gdata in ydata.items():
                if gc_api == "_none":
                    # 2024/2023 通常无专业组，直接取院校最低分
                    if gdata["min_score"]:
                        best_match = gc_api
                        best_score = gdata["min_score"]
                elif fuzzy_match(gc_user, gc_api):
                    if gdata["min_score"]:
                        best_match = gc_api
                        best_score = gdata["min_score"]
                        break

        if best_score is not None:
            rank = rank_from_score(best_score, year)
            group_history.append({
                "year": year,
                "score": str(best_score),
                "rank": str(rank) if rank else "",
                "matched_group": best_match
            })

    # 取最近3年，按年份降序
    group_history.sort(key=lambda x: x["year"], reverse=True)
    group_history = group_history[:3]

    if group_history:
        # 更新 config.history
        g["config"]["history"] = [
            {"year": h["year"], "rank": h["rank"], "score": h["score"]}
            for h in group_history
        ]
        updated_groups += 1

    # --- 匹配专业级数据 ---
    for year in ["2025", "2024", "2023"]:
        ydata = sd["years"].get(year, {})
        if not ydata:
            continue

        # 找到匹配的专业组数据
        matched_gc = None
        if gc_user in ydata:
            matched_gc = gc_user
        else:
            for gc_api in ydata:
                if fuzzy_match(gc_user, gc_api):
                    matched_gc = gc_api
                    break

        if not matched_gc:
            continue

        api_majors = ydata[matched_gc]["majors"]

        for m in g["majors"]:
            # 尝试匹配专业代码
            mcode = m.get("code", "")
            mname = m.get("name", "")

            best_am = None
            for am in api_majors:
                if am["code"] and am["code"] == mcode:
                    best_am = am
                    break

            if not best_am:
                for am in api_majors:
                    if fuzzy_match(mname, am["name"]):
                        best_am = am
                        break

            if best_am and best_am.get("score_min"):
                # 初始化或更新专业级 history
                if not m.get("history"):
                    m["history"] = []

                # 检查是否已有该年份数据
                existing = [h for h in m["history"] if h.get("year") == year]
                if not existing:
                    rank = rank_from_score(best_am["score_min"], year)
                    m["history"].append({
                        "year": year,
                        "rank": str(rank) if rank else "",
                        "score": best_am["score_min"]
                    })
                    updated_majors += 1

    # 标记不确定的匹配
    if not group_history:
        uncertain.append(f"{name} {gc_user}: 无匹配的录取数据")

# 保存
with open("../data/volunteer_data_updated.json", "w", encoding="utf-8") as f:
    json.dump(volunteer, f, ensure_ascii=False, indent=2)

print(f"Updated: {updated_groups} groups, {updated_majors} majors")
if uncertain:
    print("\n=== 需要确认的匹配 ===")
    for u in uncertain:
        print(f"  ⚠ {u}")

# 打印每个学校的匹配详情
print("\n=== 匹配详情 ===")
school_names = {}
for g in volunteer["groups"]:
    name = g["schoolName"]
    if name not in school_names:
        hist = g["config"].get("history", [])
        hstr = " | ".join(f"{h.get('year','?')}:{h.get('score','?')}分/{h.get('rank','?')}位" for h in hist)
        print(f"  {name:20s} 组{g['groupCode']:6s}: {hstr or '无数据'}")
        school_names[name] = True
