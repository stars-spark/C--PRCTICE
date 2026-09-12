# -*- coding: utf-8 -*-
"""问题2 价值阶梯 + 安全裕度 U 型曲线回测（334 天完整模拟）。

量化三件事：
  A. 无储能基线（上界）  B. 完美信息下界  C. 预测+优化的现实可达成本
其中 C-B 即信息价值 EVPI，是各队唯一能拉开差距的部分。

依赖: pandas, numpy, scipy, openpyxl；在仓库根目录运行: python C题/分析/问题2_价值阶梯回测.py
注意: 预测器故意保持朴素（上周同日均值 / 近5日均值），
      目的是给出"可改进空间"的基准，而非最终方案。
"""
import os
import numpy as np
import pandas as pd
from scipy.optimize import linprog

BASE='C题/附件'
T,DT=144,1/6; ETA=.9; EMIN,EMAX,E0=1200.,10800.,6000.; PS=5000*DT

ld=pd.read_excel(f'{BASE}/附件2.xlsx',sheet_name='小区负载')
pv=pd.read_excel(f'{BASE}/附件2.xlsx',sheet_name='光伏发电实际功率')
L=ld.iloc[:,1:].values.astype(float); P=pv.iloc[:,1:].values.astype(float)
dates=pd.to_datetime(ld.iloc[:,0]); dow=dates.dt.dayofweek.values
c=pd.read_excel(f'{BASE}/附件1.xlsx')['电价'].values   # 问题2: 每天电价相同

# ---- 预构建 LP 结构(只有 b 随天变化) ----
Z=np.zeros((T,T)); I=np.eye(T); TRIL=np.tril(np.ones((T,T)))
# 变量 [q, ch, dis]
A_bal=np.hstack([-I,  I, -I])                       # -q +ch -dis <= PV*dt - L*dt
A_hi =np.hstack([Z,  ETA*TRIL, -TRIL/ETA])          # E_t - E_s <= EMAX-E_s
A_lo =np.hstack([Z, -ETA*TRIL,  TRIL/ETA])          # -(E_t-E_s) <= E_s-EMIN
A_ub=np.vstack([A_bal,A_hi,A_lo])
A_term=np.hstack([np.zeros(T),-ETA*np.ones(T), np.ones(T)/ETA])[None,:]  # -(ΔE) <= -(Etgt-E_s)
BND=[(0,None)]*T+[(0,PS)]*T*2

def plan(Lf,Pf,Es,Etgt):
    """给定预测(Lf,Pf)与起始电量Es, 解日前LP, 返回计划购电量 q; 终端约束 E_24 >= Etgt"""
    A=np.vstack([A_ub, A_term])
    b=np.concatenate([(Pf-Lf)*DT, np.full(T,EMAX-Es), np.full(T,Es-EMIN), [-(Etgt-Es)]])
    r=linprog(np.concatenate([c,np.zeros(2*T)]),A_ub=A,b_ub=b,bounds=BND,method='highs')
    return r.x[:T] if r.success else None

def execute(q,La,Pa,Es):
    """实时执行: 电池作缓冲, 不足部分紧急购电(5c)"""
    E=Es; emer=np.zeros(T); spill=0.
    for t in range(T):
        need=La[t]*DT-Pa[t]*DT-q[t]
        if need>0:
            d=min(need,PS,(E-EMIN)*ETA); E-=d/ETA
            if need-d>1e-9: emer[t]=need-d
        elif need<0:
            ch=min(-need,PS,(EMAX-E)/ETA); E+=ETA*ch; spill+=(-need-ch)
    return E,emer,spill

# ---- 预测器 ----
def fc_load(d,z,sd):
    idx=[d-7*k for k in range(1,5) if d-7*k>=0]
    return L[idx].mean(0)+z*sd
def fc_pv(d,z,sd):
    return np.clip(P[max(0,d-5):d].mean(0)-z*sd,0,None)

# 残差std(按时段), 用截至当日的历史滚动估计(每30天更新一次以提速)
def resid_std(d):
    sl,sp=[],[]
    for i in range(7,d):
        idx=[i-7*k for k in range(1,5) if i-7*k>=0]
        sl.append(L[i]-L[idx].mean(0)); sp.append(P[i]-P[max(0,i-5):i].mean(0))
    return np.std(sl,0),np.std(sp,0)

START=31  # 2025-02-01
def run(z,verbose=False):
    Es=E0; cost=0.; emer_kwh=0.; emer_cost=0.; sdL,sdP=resid_std(START)
    for d in range(START,365):
        if (d-START)%30==0: sdL,sdP=resid_std(d)
        q=plan(fc_load(d,z,sdL),fc_pv(d,z,sdP),Es,E0)
        if q is None: continue
        Es,em,_=execute(q,L[d],P[d],Es)
        cost+=c@q+5*(c@em); emer_kwh+=em.sum(); emer_cost+=5*(c@em)
    return cost,emer_kwh,emer_cost

def perfect():
    """完美信息下界: 用真实值做计划, 无紧急购电"""
    Es=E0; cost=0.
    for d in range(START,365):
        q=plan(L[d],P[d],Es,E0)
        Es,em,_=execute(q,L[d],P[d],Es); cost+=c@q+5*(c@em)
    return cost

def nostorage():
    tot=0.
    for d in range(START,365): tot+=c@(np.clip(L[d]-P[d],0,None)*DT)
    return tot

print('【问题2 价值阶梯】(2025.2.1-12.31, 334天, 附件1固定电价)\n')
lb=perfect(); ns=nostorage()
print(f'  A. 无储能、完美信息(直购)      {ns:14,.0f} 元')
print(f'  B. 有储能、完美信息(理论下界)  {lb:14,.0f} 元   储能价值 {ns-lb:11,.0f} 元 ({100*(ns-lb)/ns:.2f}%)')
print()
print('  C. 有储能 + 点/分位预测 —— 安全裕度 z 扫描:')
print(f'     {"z":>5} {"总成本(元)":>14} {"紧急购电(kWh)":>14} {"紧急费用(元)":>13} {"较下界":>9}')
best=None
for z in [0,.25,.5,.75,1.,1.5,2.,2.5,3.]:
    tc,ek,ec=run(z)
    gap=100*(tc-lb)/lb
    print(f'     {z:5.2f} {tc:14,.0f} {ek:14,.0f} {ec:13,.0f} {gap:8.2f}%')
    if best is None or tc<best[1]: best=(z,tc)
print(f'\n  => 最优裕度 z* = {best[0]}, 总成本 {best[1]:,.0f} 元, 距完美信息 {100*(best[1]-lb)/lb:.2f}%')
print(f'  => 信息价值(EVPI) = {best[1]-lb:,.0f} 元')
