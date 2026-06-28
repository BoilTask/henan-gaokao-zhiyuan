"""最终匹配：河小阳数据 → 志愿表，使用完整一分一段表"""
import json, difflib

# 完整一分一段表
SRM = {"2025": {}, "2024": {}, "2023": {}}
# 2025 (from score_rank_map.js)
s2025 = "710:12,709:19,708:23,707:27,706:33,705:41,704:52,703:66,702:82,701:91,700:108,699:122,698:151,697:186,696:213,695:241,694:272,693:313,692:339,691:380,690:416,689:461,688:511,687:566,686:627,685:695,684:779,683:857,682:961,681:1047,680:1146,679:1277,678:1380,677:1509,676:1624,675:1763,674:1917,673:2061,672:2230,671:2395,670:2579,669:2741,668:2939,667:3171,666:3387,665:3614,664:3838,663:4084,662:4316,661:4578,660:4874,659:5147,658:5456,657:5758,656:6120,655:6441,654:6779,653:7144,652:7511,651:7914,650:8281,649:8687,648:9130,647:9537,646:9989,645:10445,644:10886,643:11370,642:11842,641:12353,640:12870,639:13404,638:13941,637:14500,636:15066,635:15727,634:16357,633:16998,632:17632,631:18242,630:18923,629:19599,628:20262,627:20939,626:21686,625:22450,624:23204,623:23980,622:24764,621:25561,620:26385,619:27239,618:28088,617:28989,616:29930,615:30812,614:31705,613:32607,612:33569,611:34569,610:35524,609:36486,608:37473,607:38498,606:39518,605:40609,604:41663,603:42712,602:43771,601:44843,600:45887,599:47010,598:48131,597:49305,596:50521,595:51684,594:52849,593:54059,592:55298,591:56625,590:57947,589:59240,588:60488,587:61718,586:63025,585:64425,584:65709,583:67120,582:68439,581:69871,580:71205,579:72674,578:74079,577:75584,576:76951,575:78368,574:79867,573:81337,572:82802,571:84302,570:85847,569:87297,568:88775,567:90232,566:91732,565:93269,564:94843,563:96460,562:98064,561:99681,560:101279,559:102928,558:104553,557:106110,556:107719,555:109314,554:110951,553:112668,552:114348,551:116078,550:117829,549:119532,548:121209,547:122973,546:124772,545:126477,544:128153,543:129826,542:131568,541:133317,540:135096,539:136912,538:138722,537:140429,536:142192,535:143976"
s2024 = "709:10,708:13,707:17,706:21,705:23,704:28,703:33,702:38,701:43,700:52,699:64,698:75,697:81,696:94,695:111,694:128,693:150,692:174,691:193,690:215,689:239,688:274,687:304,686:341,685:369,684:408,683:444,682:491,681:521,680:573,679:608,678:684,677:746,676:812,675:881,674:958,673:1024,672:1095,671:1180,670:1246,669:1318,668:1410,667:1509,666:1604,665:1714,664:1823,663:1942,662:2051,661:2157,660:2272,659:2405,658:2546,657:2662,656:2809,655:2955,654:3120,653:3287,652:3441,651:3608,650:3784,649:3955,648:4153,647:4332,646:4551,645:4744,644:4966,643:5177,642:5385,641:5635,640:5855,639:6120,638:6413,637:6669,636:6965,635:7249,634:7548,633:7831,632:8139,631:8444,630:8810,629:9133,628:9498,627:9839,626:10188,625:10592,624:10962,623:11363,622:11767,621:12204,620:12607,619:13028,618:13475,617:13941,616:14396,615:14891,614:15402,613:15913,612:16488,611:16982,610:17519,609:18059,608:18642,607:19256,606:19869,605:20456,604:21039,603:21656,602:22336,601:22963,600:23638,599:24309,598:25049,597:25762,596:26465,595:27214,594:27919,593:28637,592:29369,591:30123,590:30887,589:31680,588:32528,587:33383,586:34230,585:35066,584:35948,583:36841,582:37744,581:38682,580:39605,579:40541,578:41509,577:42445,576:43459,575:44463,574:45456,573:46513,572:47548,571:48594,570:49566,569:50642,568:51686,567:52721,566:53909,565:55035,564:56189,563:57281,562:58400,561:59579,560:60745,559:61939,558:63132,557:64313,556:65558,555:66810,554:68050,553:69342,552:70602,551:71851,550:73108,549:74409,548:75686,547:77002,546:78339,545:79655,544:80952,543:82340,542:83672,541:84991,540:86324,539:87758,538:89194,537:90628,536:92030,535:93451,534:94894,533:96379,532:97837,531:99299,530:100737,529:102211,528:103674,527:105160,526:106610,525:108197,524:109654,523:111166,522:112738,521:114271,520:115830,519:117381,518:118997,517:120583,516:122158,515:123701,514:125279,513:126985,512:128582,511:130195,510:131720,509:133259,508:134903,507:136483,506:138119,505:139708,504:141292,503:142935,502:144581,501:146167,500:147838"
s2023 = "710:11,709:12,708:16,707:21,706:28,705:34,704:40,703:45,702:55,701:63,700:74,699:80,698:94,697:98,696:109,695:127,694:147,693:163,692:170,691:198,690:219,689:239,688:270,687:297,686:327,685:358,684:394,683:431,682:481,681:518,680:546,679:585,678:621,677:682,676:738,675:784,674:852,673:914,672:969,671:1031,670:1089,669:1165,668:1232,667:1319,666:1407,665:1482,664:1571,663:1652,662:1741,661:1842,660:1934,659:2043,658:2159,657:2272,656:2390,655:2514,654:2672,653:2804,652:2956,651:3116,650:3275,649:3414,648:3581,647:3746,646:3921,645:4102,644:4301,643:4496,642:4712,641:4934,640:5126,639:5359,638:5568,637:5800,636:6059,635:6311,634:6603,633:6878,632:7185,631:7493,630:7810,629:8100,628:8437,627:8771,626:9098,625:9462,624:9823,623:10186,622:10580,621:10964,620:11310,619:11731,618:12162,617:12626,616:13053,615:13508,614:13937,613:14404,612:14902,611:15415,610:15925,609:16466,608:17028,607:17545,606:18105,605:18689,604:19248,603:19849,602:20418,601:21021,600:21690,599:22358,598:23029,597:23710,596:24444,595:25156,594:25874,593:26587,592:27318,591:28052,590:28881,589:29681,588:30481,587:31315,586:32135,585:33012,584:33845,583:34767,582:35635,581:36540,580:37479,579:38365,578:39314,577:40252,576:41196,575:42149,574:43114,573:44106,572:45094,571:46132,570:47216,569:48276,568:49343,567:50409,566:51529,565:52597,564:53716,563:54864,562:55999,561:57115,560:58304,559:59481,558:60657,557:61944,556:63193,555:64505,554:65789,553:67050,552:68278,551:69662,550:70991,549:72337,548:73607,547:74961,546:76354,545:77768,544:79143,543:80568,542:81975,541:83430,540:84884,539:86255,538:87738,537:89231,536:90770,535:92225,534:93677,533:95116,532:96633,531:98157,530:99673,529:101260,528:102802,527:104360,526:105904,525:107463,524:109013,523:110642,522:112300,521:113938,520:115516,519:117138,518:118760,517:120414,516:122128,515:123771,514:125465,513:127155,512:128863,511:130500,510:132206,509:133928,508:135648,507:137351,506:139053,505:140854,504:142648,503:144399,502:146079,501:147888,500:149644"

for pair in s2025.split(","):
    s,r = pair.split(":")
    SRM["2025"][int(s)] = int(r)
for pair in s2024.split(","):
    s,r = pair.split(":")
    SRM["2024"][int(s)] = int(r)
for pair in s2023.split(","):
    s,r = pair.split(":")
    SRM["2023"][int(s)] = int(r)

def rank_from_score(score, year):
    s = int(score)
    keys = sorted(SRM.get(year, {}).keys(), reverse=True)
    for k in keys:
        if s >= k:
            return SRM[year][k]
    return None

# Load data
with open("/tmp/all_schools_data.json", encoding="utf-8") as f:
    school_data = json.load(f)
with open("/home/gaokao/volunteer_data.json", encoding="utf-8") as f:
    volunteer = json.load(f)

# Also re-scrape missing 2025 data for 人大/山大/吉大/北师大
# These have 2025 data but filter_physics might have been too strict
import requests, re
HEADERS = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}
API = "https://www.gaokao.haedu.cn/api"

fix_schools = {
    "中国人民大学": ("10002", "1735"),
    "山东大学": ("10422", "1530"),
    "吉林大学": ("10183", "1605"),
    "北京师范大学": ("10027", "1445"),
}

for sname, (code, cat) in fix_schools.items():
    if code in school_data and "2025" in school_data[code]["years"] and school_data[code]["years"]["2025"]:
        continue  # already has 2025 data
    print(f"Re-fetching 2025 for {sname}...")
    try:
        resp = requests.post(f"{API}/zy_admission/index", json={
            "page":1, "page_size":50, "category":1,
            "gb_code": code, "year": "2025",
            "batch_code":"", "first_choice_code":"",
            "category_code": cat, "keyword":""
        }, headers=HEADERS, timeout=15)
        data = resp.json()
        if data.get("code") == 1:
            records = data.get("data", {}).get("data", [])
            phys = [r for r in records if "物理" in str(r.get("first_choice","")) or "理科" in str(r.get("first_choice",""))]
            if phys:
                groups = {}
                for r in phys:
                    gc = r.get("major_group_code") or "_none"
                    if gc not in groups:
                        groups[gc] = {"scores": [], "majors": []}
                    s = r.get("admission_score_min","")
                    if s: groups[gc]["scores"].append(int(s))
                    groups[gc]["majors"].append({
                        "code": r.get("major_enrollment_code",""),
                        "name": r.get("major_name",""),
                        "score_min": r.get("admission_score_min",""),
                        "score_max": r.get("admission_score_max",""),
                        "score_avg": r.get("admission_score_average",""),
                        "plan": r.get("major_plan",""),
                        "enrolled": r.get("admission_num",""),
                        "require": r.get("major_optional_require",""),
                    })
                for gc, gdata in groups.items():
                    if gdata["scores"]:
                        min_s = min(gdata["scores"])
                        gdata["min_score"] = min_s
                        gdata["min_rank"] = rank_from_score(min_s, "2025")
                school_data[code]["years"]["2025"] = groups
                print(f"  Got {len(phys)} records in {len(groups)} groups")
            else:
                print(f"  No physics data (first_choice values: {set(r.get('first_choice','') for r in records)})")
        else:
            print(f"  API error: {data}")
    except Exception as e:
        print(f"  Exception: {e}")

# Now match
def fuzzy_match(a, b):
    a = a.strip().replace(" ","").replace("（","(").replace("）",")")
    b = b.strip().replace(" ","").replace("（","(").replace("）",")")
    if a == b: return True
    if a in b or b in a: return True
    return difflib.SequenceMatcher(None, a, b).ratio() > 0.7

uncertain = []
updated_groups = 0
updated_majors = 0

for g in volunteer["groups"]:
    name = g["schoolName"]
    scode = g["config"].get("nationalCode", "")
    if not scode or scode not in school_data:
        continue

    sd = school_data[scode]
    gc_user = g["groupCode"]
    group_history = []

    for year in ["2025", "2024", "2023"]:
        ydata = sd["years"].get(year, {})
        if not ydata: continue

        best_score = None
        if gc_user in ydata:
            gdata = ydata[gc_user]
            if gdata.get("min_score"):
                best_score = gdata["min_score"]
        else:
            for gc_api, gdata in ydata.items():
                if gc_api == "_none" and gdata.get("min_score"):
                    best_score = gdata["min_score"]
                elif fuzzy_match(gc_user, gc_api) and gdata.get("min_score"):
                    best_score = gdata["min_score"]
                    break

        if best_score is not None:
            rank = rank_from_score(best_score, year)
            group_history.append({"year": year, "score": str(best_score), "rank": str(rank) if rank else ""})

    group_history.sort(key=lambda x: x["year"], reverse=True)
    group_history = group_history[:3]

    if group_history:
        g["config"]["history"] = [{"year": h["year"], "rank": h["rank"], "score": h["score"]} for h in group_history]
        updated_groups += 1

    # Major-level matching
    for year in ["2025", "2024", "2023"]:
        ydata = sd["years"].get(year, {})
        if not ydata: continue
        matched_gc = None
        if gc_user in ydata: matched_gc = gc_user
        else:
            for gc_api in ydata:
                if fuzzy_match(gc_user, gc_api):
                    matched_gc = gc_api
                    break
        if not matched_gc: continue
        api_majors = ydata[matched_gc]["majors"]
        for m in g["majors"]:
            mcode = m.get("code","")
            mname = m.get("name","")
            best_am = None
            for am in api_majors:
                if am["code"] and am["code"] == mcode:
                    best_am = am; break
            if not best_am:
                for am in api_majors:
                    if fuzzy_match(mname, am["name"]):
                        best_am = am; break
            if best_am and best_am.get("score_min"):
                if not m.get("history"): m["history"] = []
                existing = [h for h in m["history"] if h.get("year") == year]
                if not existing:
                    rank = rank_from_score(best_am["score_min"], year)
                    m["history"].append({"year": year, "rank": str(rank) if rank else "", "score": best_am["score_min"]})
                    updated_majors += 1

    if not g["config"].get("history"):
        uncertain.append(f"{name} 组{gc_user}: 完全没有匹配到录取数据")

# Save updated volunteer data
with open("/tmp/volunteer_updated.json", "w", encoding="utf-8") as f:
    json.dump(volunteer, f, ensure_ascii=False, indent=2)

# Print summary
print(f"\nUpdated: {updated_groups} groups, {updated_majors} majors")
for u in uncertain:
    print(f"  ! {u}")

print("\n=== 匹配结果 ===")
seen = set()
for g in volunteer["groups"]:
    key = (g["schoolName"], g["groupCode"])
    if key not in seen:
        seen.add(key)
        hist = g["config"].get("history", [])
        hstr = " | ".join(f"{h.get('year','?')}:{h.get('score','?')}分/{h.get('rank','?')}位" for h in hist[:3])
        print(f"  {g['schoolName']:20s} {g['groupCode']:6s} | {hstr or '无数据'}")

print(f"\nTotal: {len(seen)} group combinations")
