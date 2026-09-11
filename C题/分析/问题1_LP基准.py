# -*- coding: utf-8 -*-
"""问题1 确定性线性规划基准解。
依赖: pandas, numpy, scipy, openpyxl
用法: python 问题1_LP基准.py
输出可用于校验自研求解代码；结果随效率口径而变，见《赛题分析.md》第三节。
"""
import os
import numpy as np
import pandas as pd
from scipy.optimize import linprog
from scipy.sparse import lil_matrix

BASE = os.path.join(os.path.dirname(__file__), '..', '附件')

T, DT = 144, 1 / 6
ETA = 0.90               # 充、放电效率各 90%
E_MIN, E_MAX, E_0 = 1200.0, 10800.0, 6000.0
P_STEP = 5000 * DT       # 单步最大充放电量 kWh


def solve():
    a1 = pd.read_excel(os.path.join(BASE, '附件1.xlsx'))
    c = a1['电价'].values
    L = a1['小区负载'].values
    PV = a1['光伏发电预测功率'].values

    # 变量顺序: q(T) 购电量 | ch(T) 充电(母线侧) | dis(T) 放电(母线侧)
    n = 3 * T
    obj = np.concatenate([c, np.zeros(T), np.zeros(T)])

    A = lil_matrix((3 * T, n))
    b = np.zeros(3 * T)
    # 供电平衡: q + PV*dt + dis - ch >= L*dt
    for t in range(T):
        A[t, t] = -1
        A[t, 2 * T + t] = -1
        A[t, T + t] = 1
        b[t] = (PV[t] - L[t]) * DT
    # SOC 上下界: E_t = E_0 + sum(eta*ch - dis/eta)
    for t in range(T):
        for k in range(t + 1):
            A[T + t, T + k], A[T + t, 2 * T + k] = ETA, -1 / ETA
            A[2 * T + t, T + k], A[2 * T + t, 2 * T + k] = -ETA, 1 / ETA
        b[T + t], b[2 * T + t] = E_MAX - E_0, E_0 - E_MIN
    # 末端 SOC 回到初值
    Aeq = lil_matrix((1, n))
    Aeq[0, T:2 * T], Aeq[0, 2 * T:] = ETA, -1 / ETA

    res = linprog(obj, A_ub=A.tocsr(), b_ub=b, A_eq=Aeq.tocsr(), b_eq=[0.0],
                  bounds=[(0, None)] * T + [(0, P_STEP)] * T * 2, method='highs')
    assert res.success, res.message
    return c, L, PV, res.x[:T], res.x[T:2 * T], res.x[2 * T:]


def main():
    c, L, PV, q, ch, dis = solve()
    E = E_0 + np.cumsum(ETA * ch - dis / ETA)
    baseline = np.clip(L - PV, 0, None) * DT

    print('【问题1 最优解】')
    print('  全天购电量 %.2f kWh' % q.sum())
    print('  全天购电费 %.2f 元' % (c @ q))
    print('  无储能对照 %.2f kWh / %.2f 元' % (baseline.sum(), c @ baseline))
    print('  储能节省   %.2f 元 (%.2f%%)' % (c @ baseline - c @ q, 100 * (1 - (c @ q) / (c @ baseline))))
    print('  SOC 范围 %.1f ~ %.1f，末值 %.1f' % (E.min(), E.max(), E[-1]))

    print('\n  表1  指定时段购电量 (kWh)')
    for lab, idx in [('10:00-10:10', 60), ('12:00-12:10', 72), ('14:00-14:10', 84),
                     ('16:00-16:10', 96), ('18:00-18:10', 108), ('20:00-20:10', 120)]:
        print('    %s  %10.2f' % (lab, q[idx]))

    print('\n  表2  储能分时段充放电量 (kWh)')
    for s in range(0, T, 24):
        print('    %02d:00-%02d:00  充 %9.1f  放 %9.1f'
              % (s // 6, (s + 24) // 6, ch[s:s + 24].sum(), dis[s:s + 24].sum()))
    print('    0:00 储电量 %.1f    24:00 储电量 %.1f' % (E_0, E[-1]))


if __name__ == '__main__':
    main()
