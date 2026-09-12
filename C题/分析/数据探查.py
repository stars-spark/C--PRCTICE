# -*- coding: utf-8 -*-
"""2026 国赛 C 题 数据探查：复现《赛题分析.md》中的全部数据结论。
依赖: pandas, numpy, openpyxl
用法: python 数据探查.py
"""
import os
import numpy as np
import pandas as pd

BASE = os.path.join(os.path.dirname(__file__), '..', '附件')
DT = 1 / 6  # 10 分钟 = 1/6 小时


def load_all():
    a1 = pd.read_excel(os.path.join(BASE, '附件1.xlsx'))
    ld = pd.read_excel(os.path.join(BASE, '附件2.xlsx'), sheet_name='小区负载')
    pv = pd.read_excel(os.path.join(BASE, '附件2.xlsx'), sheet_name='光伏发电实际功率')
    a3 = pd.read_excel(os.path.join(BASE, '附件3.xlsx'))
    a4 = pd.read_excel(os.path.join(BASE, '附件4.xlsx'))
    return a1, ld, pv, a3, a4


def main():
    a1, ld, pv, a3, a4 = load_all()
    L = ld.iloc[:, 1:].values.astype(float)      # 365 x 144  kW
    P = pv.iloc[:, 1:].values.astype(float)      # 365 x 144  kW
    C = a4.iloc[:, 1:].values.astype(float)      # 365 x 144  元/kWh
    dates = pd.to_datetime(ld.iloc[:, 0])
    dow = dates.dt.dayofweek.values

    print('=' * 60)
    print('1. 电价峰谷结构（附件1）')
    p = a1['电价'].values
    for s in range(0, 144, 12):
        print('   %02d:00-%02d:00  均价 %.4f' % (s // 6, (s + 12) // 6, p[s:s + 12].mean()))
    print('   峰谷比 %.2f 倍；储能套利门槛 1/(0.9*0.9) = %.3f' % (p.max() / p.min(), 1 / 0.81))

    print('=' * 60)
    print('2. 负载的星期效应（问题2 预测的第一特征）')
    daily = L.sum(1) * DT
    lo, hi = daily[np.isin(dow, [4, 5])], daily[~np.isin(dow, [4, 5])]
    print('   周五/六 : %.0f kWh/日  (n=%d, CV=%.3f)' % (lo.mean(), len(lo), lo.std() / lo.mean()))
    print('   其余五天: %.0f kWh/日  (n=%d, CV=%.3f)' % (hi.mean(), len(hi), hi.std() / hi.mean()))

    print('   朴素预测器对比 (2月起评估):')
    prev = np.vstack([L[0], L[:-1]])
    wk = np.vstack([L[:7], L[:-7]])
    wk4 = np.array([L[[i - 7 * k for k in range(1, 5) if i - 7 * k >= 0]].mean(0)
                    if i >= 7 else L[i] for i in range(len(L))])
    for nm, pr in [('前一天', prev), ('上周同日', wk), ('前4周同日均值', wk4)]:
        e = np.abs(pr[31:] - L[31:]).mean()
        print('     %-14s MAE %6.1f kW  (%.2f%%)' % (nm, e, 100 * e / L[31:].mean()))

    print('=' * 60)
    print('3. 光伏预报质量随发布时刻的变化（问题3 的定量依据）')
    a3 = a3.copy()
    a3['日期'] = pd.to_datetime(a3['日期'].ffill()).dt.strftime('%Y-%m-%d')
    d2i = {d: i for i, d in enumerate(dates.dt.strftime('%Y-%m-%d').values)}
    F = a3.iloc[:, 2:].values.astype(float)
    tab = {}
    for r in range(len(a3)):
        di = d2i[a3['日期'].iloc[r]]
        h0 = int(str(a3['预报时刻'].iloc[r]).split(':')[0])
        for k in range(1, 25):
            hh = h0 + k
            dd, hh = di + hh // 24, hh % 24
            if dd >= 365:
                continue
            tab.setdefault((dd, hh), {})[h0] = F[r, k - 1]

    def act(dd, hh):
        return P[dd - 1, 143] if hh == 0 else P[dd, hh * 6 - 1]

    rows = {}
    for (dd, hh), m in tab.items():
        if not 8 <= hh <= 17:
            continue
        a = act(dd, hh)
        for h0, f in m.items():
            rows.setdefault(h0, []).append(abs(f - a))
    for h0 in sorted(rows):
        print('   发布 %2d:00 -> 白天(8-17点)目标 MAE %6.1f kW' % (h0, np.mean(rows[h0])))
    p0 = [abs(m[0] - act(dd, hh)) for (dd, hh), m in tab.items() if 8 <= hh <= 17 and 0 in m and 6 in m]
    p6 = [abs(m[6] - act(dd, hh)) for (dd, hh), m in tab.items() if 8 <= hh <= 17 and 0 in m and 6 in m]
    print('   配对比较: 6:00 预报较 0:00 预报误差下降 %.1f%%' % (100 * (1 - np.mean(p6) / np.mean(p0))))

    print('=' * 60)
    print('4. 波动电价 = 基准形态 × 随机因子（问题4 的结构）')
    R = C / p
    print('   附件4 平均日形态 vs 附件1 电价  相关系数 %.4f' % np.corrcoef(C.mean(0), p)[0, 1])
    print('   比值 R: mean %.4f  std %.4f  范围 [%.4f, %.4f]' % (R.mean(), R.std(), R.min(), R.max()))
    print('   R 日内相邻时刻自相关 %.3f；日均值 lag-1 自相关 %.3f'
          % (np.mean([np.corrcoef(r[:-1], r[1:])[0, 1] for r in R]),
             np.corrcoef(R.mean(1)[:-1], R.mean(1)[1:])[0, 1]))
    print('   极低价点: <0.05 元 共 %d 个, <0.2 元 共 %d 个' % ((C < 0.05).sum(), (C < 0.2).sum()))

    print('=' * 60)
    print('5. 供需规模')
    net = L - P
    print('   日用电 %.0f kWh, 日发电 %.0f kWh, 日净需求 %.0f kWh (均值)'
          % ((L.sum(1) * DT).mean(), (P.sum(1) * DT).mean(), (net.sum(1) * DT).mean()))
    print('   全年光伏过剩 %.0f kWh，涉及 %d 天' % (np.clip(-net, 0, None).sum() * DT, (net < 0).any(1).sum()))


if __name__ == '__main__':
    main()
