#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""分析志愿表数据，输出结构化信息"""
import json
import sys
import os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

with open('data/volunteer_data_current.json', 'r', encoding='utf-8') as f:
    vdata = json.load(f)

print(f"=== 志愿数据概览 ===")
print(f"总组数: {len(vdata.get('groups', []))}")
print()

# 考生基本信息
# 从 Code json 获取
code_file = 'Code_20260628002009(1).json'
if os.path.exists(code_file):
    with open(code_file, 'r', encoding='utf-8') as f:
        codedata = json.load(f)
    stu = codedata.get('student', {})
    print(f"考生: {stu.get('score', '?')}分 / {stu.get('rank', '?')}位 / {stu.get('subject', '?')}类 / {stu.get('province', '?')} {stu.get('year', '?')}")
    print()

# 策略分类
for i, g in enumerate(vdata.get('groups', [])):
    config = g.get('config', {})
    # Try to get strategy from various places
    strategy = config.get('strategy', g.get('strategy', '?'))
    school_code = config.get('nationalCode', config.get('schoolCode', '?'))
    school_name = config.get('schoolName', '?')

    hist = config.get('history', [])
    hist_latest = hist[0] if hist else {}

    group_code = g.get('groupCode', '?')
    group_name = g.get('groupName', '?')
    enrollment = g.get('groupEnrollment', '?')

    # Get obeyAdjust
    obey = config.get('obeyAdjust', g.get('obeyAdjust', None))
    if obey is None:
        obey = True  # default

    note = config.get('note', g.get('note', ''))

    majors = g.get('majors', [])

    # Determine how many CS-related majors
    cs_keywords = ['计算机', '软件', '人工智能', '信息安全', '网络空间安全', '数据科学', '大数据', '智能', '信息对抗', '虚拟现实']
    cs_majors = []
    non_cs_majors = []
    for m in majors:
        mname = m.get('name', '')
        is_cs = any(kw in mname for kw in cs_keywords)
        if is_cs:
            cs_majors.append(m)
        else:
            non_cs_majors.append(m)

    print(f"#{i+1} [{strategy.upper()}] {school_code} - {school_name}")
    print(f"  组: {group_code} {group_name}, 招生{enrollment}人, 服从调剂={obey}")

    # History
    if hist:
        hist_parts = []
        for h in hist[:3]:
            hist_parts.append(f"{h.get('year','?')}:{h.get('score','?')}分/{h.get('rank','?')}位")
        print(f"  近三年投档: {' | '.join(hist_parts)}")

    # CS major ratio
    print(f"  计算机类专业: {len(cs_majors)}/{len(majors)}")
    for m in majors:
        mname = m.get('name', '')
        mcode = m.get('code', '?')
        menr = m.get('enrollment', '?')
        is_cs = any(kw in mname for kw in cs_keywords)
        tag = "[CS]" if is_cs else ""
        mhist = m.get('history', [])
        if mhist:
            latest = mhist[0]
            mhist_str = f"最新{latest.get('year','?')}:{latest.get('score','?')}分/{latest.get('rank','?')}位"
        else:
            mhist_str = "无历史"
        print(f"    {mcode} {mname} (招{menr}人) {mhist_str} {tag}")

    # Note
    if note:
        note_short = note[:150] + '...' if len(note) > 150 else note
        print(f"  备注: {note_short}")

    print()

# Summary stats
print()
print("=== 策略分布 ===")
strategies = {}
for g in vdata.get('groups', []):
    config = g.get('config', {})
    s = config.get('strategy', g.get('strategy', '?'))
    strategies[s] = strategies.get(s, 0) + 1
for s, c in sorted(strategies.items()):
    print(f"  {s}: {c}个")

# Check order
print()
print("=== 当前顺序 ===")
for i, g in enumerate(vdata.get('groups', [])):
    config = g.get('config', {})
    s = config.get('strategy', g.get('strategy', '?'))
    school_name = config.get('schoolName', '?')
    group_code = g.get('groupCode', '?')
    group_name = g.get('groupName', '?')
    hist = config.get('history', [])
    latest_score = hist[0].get('score', '?') if hist else '?'
    latest_rank = hist[0].get('rank', '?') if hist else '?'
    print(f"  #{i+1:2d} [{s:4s}] {school_name} | {group_code} {group_name} | 投档: {latest_score}分/{latest_rank}位")
