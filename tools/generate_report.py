#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成志愿分析HTML报告 — 欧阳天柱 657分/3471位 河南物理类 2026"""

import json
import os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── 加载数据 ──
with open('data/volunteer_data_current.json', 'r', encoding='utf-8') as f:
    vdata = json.load(f)
with open('Code_20260628002009(1).json', 'r', encoding='utf-8') as f:
    cdata = json.load(f)
with open('data/all_schools_data.json', 'r', encoding='utf-8') as f:
    sdata = json.load(f)

student = {"score": 657, "rank": 3471, "subject": "物理", "province": "河南", "year": 2026}

# ── 学校映射 ──
nc_to_name = {}
for nc, info in sdata.items():
    nc_to_name[nc] = info.get('name', nc)

# 省码 → 校名 (from Code JSON)
pc_to_name = {}
for g in cdata.get('groups', []):
    sc = g.get('schoolCode', '')
    sn = g.get('schoolName', '')
    if sc and sc not in pc_to_name:
        pc_to_name[sc] = sn

# 国标 → 省码
nc_to_pc = {}
for g in cdata.get('groups', []):
    nc = g.get('config', {}).get('nationalCode', '')
    sc = g.get('schoolCode', '')
    if nc and sc and nc not in nc_to_pc:
        nc_to_pc[nc] = sc

# ── CS 专业分级关键词 ──
CS_TIER = {
    1: ['计算机科学与技术', '软件工程'],
    2: ['人工智能'],
    3: ['信息安全', '网络空间安全', '数据科学', '大数据', '信息对抗'],
    4: ['电子信息', '通信工程', '自动化', '智能科学', '微电子', '集成电路',
        '机器人', '智能感知', '智能医学', '信息工程', '电子科学', '光电信息',
        '电磁场', '测控技术'],
    5: ['数学', '统计学', '信息与计算科学', '应用物理'],
}

def get_cs_tier(major_name):
    """判断专业的CS相关等级, 0=不相关"""
    for tier in [1, 2, 3, 4, 5]:
        for kw in CS_TIER[tier]:
            if kw in major_name:
                return tier
    return 0

def get_cs_tier_label(tier):
    labels = {0: '非CS', 1: 'T1-计算机核心', 2: 'T2-人工智能', 3: 'T3-安全/数据',
              4: 'T4-电子信息', 5: 'T5-数学/物理'}
    return labels.get(tier, '未知')

def classify_risk(latest_rank, student_rank=3471):
    """冲/稳/保分类"""
    if latest_rank == 0:
        return 'unknown'
    if student_rank < latest_rank * 0.85:
        return '冲'
    elif student_rank < latest_rank * 1.15:
        return '稳'
    else:
        return '保'

# ── 分析每组 ──
groups_analysis = []
for i, g in enumerate(vdata.get('groups', [])):
    config = g.get('config', {})
    nc = config.get('nationalCode', '?')
    sn = nc_to_name.get(nc, f'未知({nc})')
    pc = nc_to_pc.get(nc, '?')
    strategy = config.get('strategy', g.get('strategy', ''))
    group_code = g.get('groupCode', '?')
    group_name = g.get('groupName', '?')
    enrollment = g.get('groupEnrollment', '?')
    obey = config.get('obeyAdjust', g.get('obeyAdjust', True))
    note = config.get('note', '')

    # 历史投档线
    hist = config.get('history', [])
    latest_rank = int(hist[0].get('rank', 0)) if hist else 0
    latest_score = int(hist[0].get('score', 0)) if hist else 0
    hist_items = []
    for h in hist[:3]:
        hist_items.append({'year': h.get('year', '?'), 'score': h.get('score', '?'),
                           'rank': h.get('rank', '?')})

    # 专业分析
    majors = g.get('majors', [])
    cs_majors_detail = []
    non_cs_count = 0
    tier_counts = {1:0,2:0,3:0,4:0,5:0,0:0}

    for m in majors:
        mname = m.get('name', '')
        mcode = m.get('code', '?')
        menr = m.get('enrollment', '?')
        mhist = m.get('history', [])
        mlatest_rank = int(mhist[0].get('rank', 0)) if mhist else 0
        mlatest_score = int(mhist[0].get('score', 0)) if mhist else 0

        tier = get_cs_tier(mname)
        tier_counts[tier] += 1
        if tier > 0:
            cs_majors_detail.append({
                'name': mname, 'code': mcode, 'enrollment': menr,
                'tier': tier, 'rank': mlatest_rank, 'score': mlatest_score
            })
        else:
            non_cs_count += 1

    # CS分数
    total_majors = len(majors)
    cs_count = sum(tier_counts[t] for t in [1,2,3,4,5])
    cs_ratio = cs_count / total_majors * 100 if total_majors > 0 else 0

    # 最高CS tier
    best_tier = 6
    for t in [1,2,3,4,5]:
        if tier_counts[t] > 0:
            best_tier = t
            break

    # 风险评估
    risk = classify_risk(latest_rank) if latest_rank > 0 else 'unknown'
    risk_label = {'冲': '🔴 冲 (位次差距较大)', '稳': '🟡 稳 (位次接近)',
                  '保': '🟢 保 (位次充裕)', 'unknown': '⚪ 无历史数据'}

    # 排名差距
    rank_gap = latest_rank - student['rank'] if latest_rank > 0 else 99999

    groups_analysis.append({
        'index': i + 1,
        'nc': nc,
        'pc': pc,
        'school_name': sn,
        'strategy': strategy,
        'group_code': group_code,
        'group_name': group_name,
        'enrollment': enrollment,
        'obey': obey,
        'latest_rank': latest_rank,
        'latest_score': latest_score,
        'rank_gap': rank_gap,
        'hist_items': hist_items,
        'total_majors': total_majors,
        'cs_count': cs_count,
        'cs_ratio': cs_ratio,
        'best_tier': best_tier,
        'tier_counts': tier_counts,
        'cs_majors_detail': cs_majors_detail,
        'risk': risk,
        'risk_label': risk_label.get(risk, '?'),
        'note': note[:300] + '...' if len(note) > 300 else note,
    })

# ── 全局统计 ──
risk_counts = {'冲': 0, '稳': 0, '保': 0, 'unknown': 0}
for ga in groups_analysis:
    risk_counts[ga['risk']] += 1

# ── 建议排序评分 ──
# 综合打分: CS专业质量 + 录取可行性 + 学校档次
def calc_score(ga):
    score = 0
    # CS 匹配度 (40分)
    if ga['best_tier'] == 1: score += 40
    elif ga['best_tier'] == 2: score += 35
    elif ga['best_tier'] == 3: score += 28
    elif ga['best_tier'] == 4: score += 20
    elif ga['best_tier'] == 5: score += 12

    # CS 占比 (20分)
    score += min(ga['cs_ratio'] / 5, 20)

    # 录取可行性 (30分)
    if ga['risk'] == '保': score += 30
    elif ga['risk'] == '稳': score += 22
    elif ga['risk'] == '冲': score += 10
    else: score += 15

    # 学校档次 bonus (10分) - C9/985/211
    c9_schools = ['北京大学', '清华大学', '复旦大学', '上海交通大学', '浙江大学',
                  '南京大学', '中国科学技术大学', '哈尔滨工业大学', '西安交通大学']
    top985 = ['北京航空航天大学', '北京理工大学', '中国人民大学', '武汉大学',
              '华中科技大学', '南开大学', '同济大学', '东南大学', '北京师范大学']

    sn = ga['school_name']
    if any(s in sn for s in c9_schools): score += 10
    elif any(s in sn for s in top985): score += 7
    elif '大学' in sn: score += 4

    return round(score, 1)

for ga in groups_analysis:
    ga['score'] = calc_score(ga)

# 生成调整建议
def generate_suggestions():
    suggestions = []

    # 按当前顺序检查问题
    for i, ga in enumerate(groups_analysis):
        issues = []

        # 问题1: 冲的组CS专业不匹配
        if ga['strategy'] == '冲' and ga['best_tier'] > 3:
            issues.append(f"标记为「冲」但最佳CS专业仅为{get_cs_tier_label(ga['best_tier'])}，冲高风险但CS回报不高")

        # 问题2: CS占比低但仍然靠前
        if ga['cs_ratio'] < 30 and i < 20:
            issues.append(f"CS专业占比仅{ga['cs_ratio']:.0f}%，但排位靠前(#{i+1})")

        # 问题3: 投档线远高于当前
        if ga['latest_rank'] > 0 and student['rank'] < ga['latest_rank'] * 0.6:
            issues.append(f"投档位次{ga['latest_rank']}远高于考生{student['rank']}位，冲高概率极低")

        # 问题4: 同校多组连排
        if i > 0 and ga['school_name'] == groups_analysis[i-1]['school_name']:
            pass  # 同校连续可能是合理的

        if issues:
            suggestions.append({
                'group_index': ga['index'],
                'school': ga['school_name'],
                'group_code': ga['group_code'],
                'issues': issues
            })

    return suggestions

suggestions = generate_suggestions()

# ── 生成HTML ──
def escape_html(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

def tier_badge(tier):
    colors = {1:'#d32f2f', 2:'#e65100', 3:'#f57c00', 4:'#1976d2', 5:'#388e3c'}
    labels = {1:'CS核心', 2:'AI', 3:'安全/数据', 4:'电子信息', 5:'数学'}
    c = colors.get(tier, '#999')
    l = labels.get(tier, '其他')
    return f'<span style="background:{c};color:#fff;padding:1px 7px;border-radius:4px;font-size:11px;margin:0 2px">{l}</span>'

def risk_icon(risk):
    icons = {'冲': '🔴', '稳': '🟡', '保': '🟢', 'unknown': '⚪'}
    return icons.get(risk, '?')

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>河南2026高考志愿分析报告 · 欧阳天柱</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{
  font-family:"Noto Sans SC","PingFang SC","Microsoft YaHei",-apple-system,sans-serif;
  background:#f0f2f5;color:#1a1a2e;line-height:1.6;
}}
.container{{max-width:1400px;margin:0 auto;padding:20px}}

/* Hero */
.hero{{
  background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%);
  color:#fff;padding:48px 40px;border-radius:20px;margin-bottom:24px;
  position:relative;overflow:hidden;
}}
.hero::before{{
  content:'';position:absolute;top:-50%;right:-20%;width:500px;height:500px;
  background:radial-gradient(circle,rgba(233,69,96,.15),transparent 70%);
  border-radius:50%;
}}
.hero h1{{font-size:36px;font-weight:900;margin-bottom:8px;position:relative}}
.hero .subtitle{{font-size:15px;opacity:.7;margin-bottom:24px;position:relative}}
.hero-cards{{display:flex;gap:16px;position:relative}}
.hero-card{{
  background:rgba(255,255,255,.1);backdrop-filter:blur(10px);
  border:1px solid rgba(255,255,255,.15);border-radius:14px;
  padding:18px 28px;text-align:center;min-width:120px;
}}
.hero-card .num{{font-size:34px;font-weight:900;font-family:"Fraunces","Georgia",serif}}
.hero-card .num.gold{{color:#ffd700}}
.hero-card .lab{{font-size:11px;opacity:.6;letter-spacing:2px;text-transform:uppercase;margin-top:4px}}

/* Section */
.section{{margin-bottom:24px}}
.section-title{{
  font-size:22px;font-weight:800;color:#1a1a2e;
  padding-bottom:14px;border-bottom:2px solid #e0e0e0;
  margin-bottom:20px;display:flex;align-items:center;gap:10px;
}}
.section-title .icon{{font-size:28px}}

/* Stats grid */
.stats-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}}
.stat-card{{
  background:#fff;border-radius:14px;padding:22px;
  box-shadow:0 2px 8px rgba(0,0,0,.06);text-align:center;
}}
.stat-card .num{{font-size:30px;font-weight:900;color:#0f3460}}
.stat-card .lab{{font-size:13px;color:#888;margin-top:4px}}
.stat-card.warn .num{{color:#e65100}}
.stat-card.good .num{{color:#2e7d32}}

/* Suggestions */
.suggestions{{
  background:#fff;border-radius:14px;padding:24px;
  box-shadow:0 2px 8px rgba(0,0,0,.06);margin-bottom:24px;
}}
.suggestion-item{{
  padding:14px 18px;margin-bottom:10px;border-radius:10px;
  border-left:4px solid #e53935;background:#fff5f5;
}}
.suggestion-item.warn{{border-left-color:#ff9800;background:#fff8e1}}
.suggestion-item.info{{border-left-color:#1976d2;background:#e3f2fd}}
.suggestion-item h4{{font-size:14px;color:#333;margin-bottom:4px}}
.suggestion-item p{{font-size:13px;color:#666}}

/* Table */
.table-wrap{{
  background:#fff;border-radius:14px;overflow:hidden;
  box-shadow:0 2px 8px rgba(0,0,0,.06);
}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
thead{{background:#f8f9fa}}
th{{
  padding:12px 10px;text-align:left;font-weight:700;color:#555;
  border-bottom:2px solid #e0e0e0;white-space:nowrap;font-size:12px;
}}
td{{padding:10px;border-bottom:1px solid #f0f0f0;vertical-align:top}}
tr:hover{{background:#f8f9ff}}
tr.highlight{{background:#fffde7}}
tr.warn-row{{background:#fff5f5}}

/* Badges */
.badge{{
  display:inline-block;padding:2px 10px;border-radius:12px;
  font-size:11px;font-weight:600;white-space:nowrap;
}}
.badge-cs{{background:#e8f5e9;color:#2e7d32}}
.badge-nocs{{background:#fce4ec;color:#c62828}}
.badge-risk{{background:#fff3e0;color:#e65100}}
.badge-safe{{background:#e8f5e9;color:#2e7d32}}
.badge-reach{{background:#fce4ec;color:#c62828}}
.badge-unknown{{background:#f5f5f5;color:#999}}

/* Progress bar */
.progress-bar{{
  height:6px;background:#e0e0e0;border-radius:3px;overflow:hidden;
  margin-top:4px;
}}
.progress-fill{{height:100%;border-radius:3px}}
.progress-cs{{background:linear-gradient(90deg,#4caf50,#81c784)}}

/* Rank gap */
.gap-pos{{color:#c62828;font-weight:700}}
.gap-neg{{color:#2e7d32;font-weight:700}}
.gap-zero{{color:#ff9800;font-weight:700}}

/* Summary */
.summary-section{{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-bottom:24px}}
.summary-box{{
  background:#fff;border-radius:14px;padding:24px;
  box-shadow:0 2px 8px rgba(0,0,0,.06);
}}
.summary-box h3{{font-size:16px;margin-bottom:16px;color:#1a1a2e}}
.summary-box ul{{list-style:none}}
.summary-box li{{
  padding:8px 0;border-bottom:1px solid #f5f5f5;font-size:13px;
  display:flex;justify-content:space-between;
}}

/* Tooltip */
.tooltip{{
  position:relative;cursor:help;
  border-bottom:1px dotted #999;
}}
.tooltip:hover .tooltip-text{{
  display:block;
}}
.tooltip-text{{
  display:none;position:absolute;bottom:100%;left:50%;transform:translateX(-50%);
  background:#333;color:#fff;padding:6px 12px;border-radius:6px;font-size:11px;
  white-space:nowrap;z-index:10;
}}

/* Risk summary */
.risk-row{{display:flex;gap:24px;margin-bottom:24px}}
.risk-box{{
  flex:1;background:#fff;border-radius:14px;padding:20px;text-align:center;
  box-shadow:0 2px 8px rgba(0,0,0,.06);
}}
.risk-box .count{{font-size:42px;font-weight:900}}
.risk-box.r-chong .count{{color:#c62828}}
.risk-box.r-wen .count{{color:#e65100}}
.risk-box.r-bao .count{{color:#2e7d32}}
.risk-box.r-unknown .count{{color:#999}}
.risk-box .label{{font-size:13px;color:#888;margin-top:4px}}

@media print{{
  body{{background:#fff}}
  .hero{{background:#1a1a2e!important;-webkit-print-color-adjust:exact}}
}}
</style>
</head>
<body>
<div class="container">

<!-- Hero -->
<div class="hero">
  <h1>🎓 河南2026高考志愿分析报告</h1>
  <div class="subtitle">基于当前服务器数据 · 综合CS专业偏好 · 排序优化建议</div>
  <div class="hero-cards">
    <div class="hero-card">
      <div class="num gold">{student['score']}</div>
      <div class="lab">高考分数</div>
    </div>
    <div class="hero-card">
      <div class="num">{student['rank']}</div>
      <div class="lab">全省位次</div>
    </div>
    <div class="hero-card">
      <div class="num">{student['subject']}</div>
      <div class="lab">选科类别</div>
    </div>
    <div class="hero-card">
      <div class="num">{len(groups_analysis)}</div>
      <div class="lab">志愿组总数</div>
    </div>
    <div class="hero-card">
      <div class="num">{sum(1 for g in groups_analysis if g['cs_count'] > 0)}</div>
      <div class="lab">含CS专业组</div>
    </div>
  </div>
</div>

<!-- Risk distribution -->
<div class="risk-row">
  <div class="risk-box r-chong">
    <div class="count">{risk_counts.get('冲',0)}</div>
    <div class="label">🔴 冲 (位次之上)</div>
  </div>
  <div class="risk-box r-wen">
    <div class="count">{risk_counts.get('稳',0)}</div>
    <div class="label">🟡 稳 (位次附近)</div>
  </div>
  <div class="risk-box r-bao">
    <div class="count">{risk_counts.get('保',0)}</div>
    <div class="label">🟢 保 (位次之下)</div>
  </div>
  <div class="risk-box r-unknown">
    <div class="count">{risk_counts.get('unknown',0)}</div>
    <div class="label">⚪ 无历史数据</div>
  </div>
</div>

<!-- Key findings -->
<div class="section">
  <div class="section-title"><span class="icon">🔍</span> 核心发现与调整建议</div>
  <div class="summary-section">
    <div class="summary-box">
      <h3>⚠️ 需要关注的问题</h3>
      <ul>
'''

# Generate summary issues
issue_items = []
for s in suggestions:
    for iss in s['issues']:
        issue_items.append(f'<li><strong>#{s["group_index"]} {s["school"]}({s["group_code"]})</strong>: {iss}</li>')

# Also add general issues
# Check if groups with good CS+保 are too far back
good_cs_bao = [g for g in groups_analysis if g['best_tier'] <= 2 and g['risk'] == '保']
if good_cs_bao:
    names = ', '.join([f"#{g['index']} {g['school_name']}" for g in good_cs_bao[:5]])
    issue_items.append(f'<li><strong>CS优质+录取稳妥</strong>: {names} 等排在较后位置，考虑提前以确保录取CS专业</li>')

# Check groups without CS
no_cs_front = [g for g in groups_analysis if g['cs_count'] == 0 and g['index'] <= 20]
if no_cs_front:
    names = ', '.join([f"#{g['index']} {g['school_name']}" for g in no_cs_front])
    issue_items.append(f'<li><strong>前20组中无CS专业</strong>: {names} 无法满足计算机专业需求</li>')

for item in issue_items:
    html += f'        {item}\n'

html += '''
      </ul>
    </div>
    <div class="summary-box">
      <h3>✅ 排序策略建议</h3>
      <ul>
        <li><strong>前10位</strong>: 放CS强校+冲高（北航、北理、西交、北邮、电子科大等）</li>
        <li><strong>11-25位</strong>: 放CS匹配+位次适中（南开、武大、西工大、山大、重庆大学等）</li>
        <li><strong>26-35位</strong>: 放CS强势+录取稳妥（华科、华南理工、湖南大学、吉大等）</li>
        <li><strong>36-44位</strong>: 放保底+至少含CS专业的院校</li>
      </ul>
    </div>
  </div>
</div>

<!-- Main table -->
<div class="section">
  <div class="section-title"><span class="icon">📊</span> 全部44组志愿详细分析</div>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>策略</th>
          <th>院校代码</th>
          <th>学校</th>
          <th>组代码</th>
          <th>组名</th>
          <th>招生</th>
          <th>调</th>
          <th>最新投档</th>
          <th>位次差</th>
          <th>CS专业</th>
          <th>CS占比</th>
          <th>最佳CS</th>
          <th>评分</th>
          <th>建议</th>
        </tr>
      </thead>
      <tbody>
'''

for ga in groups_analysis:
    idx = ga['index']
    strategy = ga['strategy'] or '-'
    pc = ga['pc']
    sn = ga['school_name']
    gc = ga['group_code']
    gn = ga['group_name']
    enr = ga['enrollment']
    obey = '是' if ga['obey'] else '否'

    # 投档信息
    if ga['latest_rank'] > 0:
        tou_dang = f"{ga['latest_score']}分/{ga['latest_rank']}位"
        gap = ga['rank_gap']
        if gap < 0:
            gap_html = f'<span class="gap-neg">↑{abs(gap)}位</span>'
        elif gap > 0:
            gap_html = f'<span class="gap-pos">↓{gap}位</span>'
        else:
            gap_html = f'<span class="gap-zero">持平</span>'
    else:
        tou_dang = '无数据'
        gap_html = '<span style="color:#999">-</span>'

    # CS信息
    cs_info = f"{ga['cs_count']}/{ga['total_majors']}"
    cs_ratio = ga['cs_ratio']
    cs_bar_width = min(cs_ratio, 100)
    cs_bar_color = '#4caf50' if cs_ratio > 60 else ('#ff9800' if cs_ratio > 30 else '#f44336')

    # Best tier
    if ga['best_tier'] <= 5:
        best_cs = tier_badge(ga['best_tier'])
    else:
        best_cs = '<span style="color:#999;font-size:11px">无CS专业</span>'

    # Risk indicator
    risk = ga['risk']
    risk_emoji = risk_icon(risk)

    # Score
    score = ga['score']
    score_color = '#2e7d32' if score >= 70 else ('#e65100' if score >= 45 else '#c62828')

    # Suggestions column
    sug_text = ''
    for s in suggestions:
        if s['group_index'] == idx:
            sug_text = '⚠️ ' + '; '.join(s['issues'][:1])
            break

    # Row class
    row_class = ''
    if ga['best_tier'] <= 2 and ga['risk'] == '保':
        row_class = 'highlight'
    elif ga['cs_count'] == 0:
        row_class = 'warn-row'

    # 展开CS专业详情
    cs_detail_html = ''
    if ga['cs_majors_detail']:
        cs_items = []
        for m in sorted(ga['cs_majors_detail'], key=lambda x: x['tier']):
            rank_str = f"{m['rank']}位" if m['rank'] > 0 else '?'
            cs_items.append(f'{tier_badge(m["tier"])} {escape_html(m["name"][:30])} (招{m["enrollment"]}人, {rank_str})')
        cs_detail_html = '<br>'.join(cs_items)

    html += f'''
        <tr class="{row_class}">
          <td><strong>{idx}</strong></td>
          <td>{risk_emoji} {strategy}</td>
          <td>{pc}</td>
          <td><strong>{sn}</strong></td>
          <td>{gc}</td>
          <td style="max-width:120px;font-size:12px">{gn}</td>
          <td>{enr}</td>
          <td>{obey}</td>
          <td style="font-size:12px">{tou_dang}</td>
          <td>{gap_html}</td>
          <td style="font-size:12px">{cs_detail_html}</td>
          <td>
            {cs_info}<br>
            <div class="progress-bar"><div class="progress-fill progress-cs" style="width:{cs_bar_width}%;background:{cs_bar_color}"></div></div>
          </td>
          <td>{best_cs}</td>
          <td><strong style="color:{score_color}">{score}</strong></td>
          <td style="font-size:11px;color:#e65100">{sug_text}</td>
        </tr>'''

html += '''
      </tbody>
    </table>
  </div>
</div>

<!-- Detailed recommendations -->
<div class="section">
  <div class="section-title"><span class="icon">💡</span> 重点调整建议详解</div>
'''

# Generate detailed recommendations
# CS优质+保底的组
excellent_cs = [g for g in groups_analysis if g['best_tier'] <= 3 and g['cs_ratio'] >= 50 and g['risk'] in ('稳', '保')]

# 冲高但CS好的
reach_good_cs = [g for g in groups_analysis if g['best_tier'] <= 3 and g['risk'] == '冲']

# Build recommendation tiles
recs = []

# Issue 1: 北航三组全在最前面
beihang = [g for g in groups_analysis if '北京航空航天' in g['school_name']]
if len(beihang) >= 3:
    recs.append({
        'title': '🔴 北航三组占据前三位 — 建议分散风险',
        'detail': '北航(1485)的三组（101普通组/G01高校专项/301国家专项）全部排在最前面。近三年普通组投档线均在1300位以内，而考生3471位，冲高概率很低。建议：保留北航101（CS专业最丰富）在前3位，但将G01和301适当后移到5-8位，中间插入其他冲高学校（如北理1490、西交1185等）分散风险。',
        'type': 'warn'
    })

# Issue 2: CS强+保底偏后
if excellent_cs:
    names_list = [f"#{g['index']} {g['school_name']}({g['pc']}) {g['group_code']} [{g['cs_count']}个CS专业, {g['latest_rank']}位]" for g in excellent_cs[:6]]
    recs.append({
        'title': '🟢 CS专业优质且录取稳妥的组应适当提前',
        'detail': '以下组具备较好的CS专业配置且录取概率较高，建议将部分组提前到20-30位：<br>' + '<br>'.join(names_list),
        'type': 'info'
    })

# Issue 3: 无CS专业的组
no_cs_groups = [g for g in groups_analysis if g['cs_count'] == 0]
if no_cs_groups:
    names_list = [f"#{g['index']} {g['school_name']}({g['pc']}) {g['group_code']} {g['group_name']} — 招{g['total_majors']}个专业全非CS" for g in no_cs_groups]
    recs.append({
        'title': '⚠️ 以下组完全不含CS相关专业 — 建议移到末尾或删除',
        'detail': '<br>'.join(names_list) + '<br><br>这些组即使录取也无法进入计算机相关专业，对以CS为首选目标的你来说价值较低。如果这些组在前30位，可能浪费宝贵的志愿坑位。',
        'type': 'warn'
    })

# Issue 4: 同校多组建议
same_school = {}
for ga in groups_analysis:
    sn = ga['school_name']
    if sn not in same_school:
        same_school[sn] = []
    same_school[sn].append(ga['index'])

multi_group_schools = {k:v for k,v in same_school.items() if len(v) >= 3}
if multi_group_schools:
    items = [f"{k}: 当前在第{', '.join(map(str, v))}位" for k,v in multi_group_schools.items()]
    recs.append({
        'title': '📋 多组院校的志愿排布建议',
        'detail': '以下院校有3个及以上志愿组：<br>' + '<br>'.join(items) + '<br><br>建议同校各组之间保持3-5个位置的间隔，避免连续排列造成"鸡蛋放一个篮子"的风险。',
        'type': 'info'
    })

# Issue 5: 重点关注 - 高性价比CS组
value_cs = [g for g in groups_analysis if g['best_tier'] <= 2 and g['risk'] in ('稳', '保') and g['cs_ratio'] >= 40]
if value_cs:
    names_list = [f"#{g['index']} {g['school_name']}({g['pc']}) {g['group_code']} — {g['cs_count']}/{g['total_majors']}个CS专业, 投档{g['latest_rank']}位, 评分{g['score']}" for g in value_cs]
    recs.append({
        'title': '⭐ 高性价比CS志愿组（录取概率高 + CS质量好）',
        'detail': '<br>'.join(names_list) + '<br><br>这些组是本次填报的"甜蜜点"——既有可能录取，又有不错的CS专业。建议确保这些组排在20-35位的核心区间。',
        'type': 'info'
    })

for r in recs:
    html += f'''
  <div class="suggestions" style="margin-bottom:16px">
    <div class="suggestion-item {r['type']}">
      <h4>{r['title']}</h4>
      <p>{r['detail']}</p>
    </div>
  </div>'''

# CS Tier Legend
html += '''
<div class="section">
  <div class="section-title"><span class="icon">📌</span> 计算机专业分级说明</div>
  <div class="summary-section">
    <div class="summary-box">
      <h3>专业优先级 (根据你的偏好)</h3>
      <ul>
        <li>''' + tier_badge(1) + ''' <strong>T1 - 计算机核心</strong>: 计算机科学与技术、软件工程 — 最高优先级</li>
        <li>''' + tier_badge(2) + ''' <strong>T2 - 人工智能</strong>: 人工智能 — 高优先级</li>
        <li>''' + tier_badge(3) + ''' <strong>T3 - 安全/数据</strong>: 信息安全、网络空间安全、数据科学、大数据 — 中高优先级</li>
        <li>''' + tier_badge(4) + ''' <strong>T4 - 电子信息相关</strong>: 电子信息工程、通信、自动化、微电子、机器人等 — 可接受</li>
        <li>''' + tier_badge(5) + ''' <strong>T5 - 数学/物理</strong>: 数学、统计学、信息与计算科学 — 可接受</li>
      </ul>
    </div>
    <div class="summary-box">
      <h3>评分体系说明</h3>
      <ul>
        <li><strong>CS匹配度 (40分)</strong>: 最佳CS专业等级</li>
        <li><strong>CS占比 (20分)</strong>: CS相关专业占总专业的比例</li>
        <li><strong>录取可行性 (30分)</strong>: 基于历史位次评估录取概率</li>
        <li><strong>学校档次 (10分)</strong>: C9/985/211等院校层级加分</li>
        <li style="color:#2e7d32"><strong>≥70分</strong>: 强烈推荐 (CS好+录取概率高)</li>
        <li style="color:#e65100"><strong>45-69分</strong>: 可考虑 (有一定价值)</li>
        <li style="color:#c62828"><strong>&lt;45分</strong>: 需斟酌 (CS或录取至少一方明显不足)</li>
      </ul>
    </div>
  </div>
</div>

<!-- Footer -->
<div style="text-align:center;padding:32px 0;color:#999;font-size:12px">
  <p>报告生成时间: 2026年6月28日 | 数据来源: 59.110.20.167 志愿填报服务器</p>
  <p>本报告为AI辅助分析，仅供参考。最终志愿决定请结合实际情况和官方数据。</p>
</div>

</div>
</body>
</html>
'''

# Write report
report_path = 'volunteer_analysis_report.html'
with open(report_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"报告已生成: {os.path.abspath(report_path)}")
print(f"文件大小: {os.path.getsize(report_path):,} bytes")
print(f"共分析 {len(groups_analysis)} 个志愿组")
print(f"提出 {len(suggestions)} 组问题, {len(recs)} 条建议")
