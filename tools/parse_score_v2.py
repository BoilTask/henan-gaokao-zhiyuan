import requests, re, json

url = "https://10006.gaokao.haedu.cn/score/cutoff/list_269_1.html"
html = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"}).text

# Find the history_list array more carefully
# It starts after "history_list:" and ends before the next top-level "}," or "],"
start = html.find("history_list:")
if start < 0:
    print("history_list not found")
    exit()

# Find the opening bracket
bracket_start = html.find("[", start)
if bracket_start < 0:
    print("no opening bracket")
    exit()

# Track nested brackets to find matching close
depth = 0
pos = bracket_start
while pos < len(html):
    if html[pos] == '[':
        depth += 1
    elif html[pos] == ']':
        depth -= 1
        if depth == 0:
            break
    pos += 1

raw = html[bracket_start:pos+1]
print(f"history_list length: {len(raw)} chars")

# Parse JS object literals manually (handle nested braces)
results = []
pos = 0
while pos < len(raw):
    # Find next opening brace
    brace_start = raw.find("{", pos)
    if brace_start < 0:
        break
    # Find matching close brace
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
                    pairs = re.findall(r"(\w+)\s*:\s*'([^']*)'", obj_str)
                    for k, v in pairs:
                        obj[k] = v
                    if obj:
                        results.append(obj)
                    pos = p + 1
                    break
        p += 1
    else:
        break

print(f"Total records parsed: {len(results)}\n")

# Show unique combinations
years = set(r.get("year","") for r in results)
batches = set(r.get("batch","") for r in results)
groups = set(r.get("major_group_code","") for r in results)
print(f"Years: {years}")
print(f"Batches: {batches}")
print(f"Major groups: {groups}")
print()

# Print detail table
print(f"{'Year':<6} {'Batch':<8} {'Subject':<6} {'Group':<6} {'Major':<40} {'Plan':>4} {'Enrolled':>6} {'Min':>5} {'Max':>5} {'Avg':>6}")
print("-" * 120)
for r in results:
    print(f"{r.get('year','?'):<6} {r.get('batch','?'):<8} {r.get('first_choice','?'):<6} "
          f"{r.get('major_group_code','?'):<6} {r.get('major_name','?'):<40} "
          f"{r.get('major_plan','?'):>4} {r.get('admission_num','?'):>6} "
          f"{r.get('admission_score_min','?'):>5} {r.get('admission_score_max','?'):>5} "
          f"{r.get('admission_score_average','?'):>6}")

# Summary per group
print(f"\n=== Per-Group Summary ===")
group_data = {}
for r in results:
    gc = r.get("major_group_code","")
    if gc not in group_data:
        group_data[gc] = {"majors": [], "min_scores": [], "max_scores": []}
    group_data[gc]["majors"].append(r.get("major_name",""))
    s = r.get("admission_score_min","")
    if s:
        group_data[gc]["min_scores"].append(int(s))
    s = r.get("admission_score_max","")
    if s:
        group_data[gc]["max_scores"].append(int(s))

for gc, d in group_data.items():
    lo = min(d["min_scores"]) if d["min_scores"] else "?"
    hi = max(d["max_scores"]) if d["max_scores"] else "?"
    print(f"  Group {gc}: {len(d['majors'])} majors, score {lo}~{hi}")
