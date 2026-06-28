import requests, re, json

url = "https://10006.gaokao.haedu.cn/score/cutoff/list_269_1.html"
html = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"}).text

# Extract history_list from JS
match = re.search(r"history_list:\s*(\[.*?\])\s*,", html, re.DOTALL)
if not match:
    print("Not found")
    exit()

raw = match.group(1)
items = re.findall(r"\{([^}]+)\}", raw)
results = []
for item in items:
    obj = {}
    pairs = re.findall(r"(\w+)\s*:\s*'([^']*)'", item)
    for k, v in pairs:
        obj[k] = v
    if obj:
        results.append(obj)

print(f"Total: {len(results)} records\n")
for r in results:
    print(f"{r.get('year','')}|{r.get('batch','')}|{r.get('first_choice','')}|"
          f"组{r.get('major_group_code','')}|{r.get('major_name','')}|"
          f"计划{r.get('major_plan','')}|录取{r.get('admission_num','')}|"
          f"最低{r.get('admission_score_min','-')}|最高{r.get('admission_score_max','-')}|"
          f"平均{r.get('admission_score_average','-')}|选科{r.get('major_optional_require','')}")

# Group by major_group
groups = {}
for r in results:
    gc = r.get("major_group_code","")
    groups.setdefault(gc, []).append(r)

print("\n=== Group Summary ===")
for gc, items in groups.items():
    scores = [r["admission_score_min"] for r in items if r.get("admission_score_min")]
    lo = min(scores) if scores else "?"
    hi = max(scores) if scores else "?"
    print(f"Group {gc}: {len(items)} majors, score range {lo}~{hi}")
