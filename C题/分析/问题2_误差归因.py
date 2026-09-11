# -*- coding: utf-8 -*-
"""回答: 距完美信息的 17.68% 缺口里, 负载预测误差和光伏预测误差各占多少?
结论决定该先打磨哪个预测器。在仓库根目录运行: python C题/分析/问题2_误差归因.py
"""
import os
import numpy as np

# 复用回测脚本的数据、LP 与执行逻辑(截取到打印段之前)
_src = os.path.join(os.path.dirname(__file__), '问题2_价值阶梯回测.py')
exec(open(_src, encoding='utf-8').read().split("print('【问题2")[0])

def run2(z, perfectL=False, perfectP=False):
    Es=E0; cost=0.; ek=0.; sdL,sdP=resid_std(START)
    for d in range(START,365):
        if (d-START)%30==0: sdL,sdP=resid_std(d)
        Lf = L[d] if perfectL else fc_load(d,z,sdL)
        Pf = P[d] if perfectP else fc_pv(d,z,sdP)
        q=plan(Lf,Pf,Es,E0)
        if q is None: continue
        Es,em,_=execute(q,L[d],P[d],Es); cost+=c@q+5*(c@em); ek+=em.sum()
    return cost,ek

lb,_=run2(0,True,True)
print(f'【误差归因】完美信息下界 {lb:,.0f} 元\n')
res={}
for nm,pl,pp,zs in [('两者都预测(基线)',False,False,[.5,.75,1.]),
                    ('负载完美/光伏预测',True,False,[0,.25,.5,.75]),
                    ('负载预测/光伏完美',False,True,[0,.25,.5,.75])]:
    cand=[(run2(z,pl,pp),z) for z in zs]
    (bc,bk),bz=min(cand,key=lambda r:r[0][0])
    res[nm]=bc
    print(f'  {nm:<18} 最优z={bz:.2f}  成本 {bc:12,.0f} 元  较下界 {100*(bc-lb)/lb:6.2f}%  紧急 {bk:9,.0f} kWh')
b=res['两者都预测(基线)']; gap=b-lb
print(f'\n  总缺口 = {gap:,.0f} 元')
print(f'    消除负载预测误差可省 {b-res["负载完美/光伏预测"]:11,.0f} 元  ({100*(b-res["负载完美/光伏预测"])/gap:5.1f}% of gap)')
print(f'    消除光伏预测误差可省 {b-res["负载预测/光伏完美"]:11,.0f} 元  ({100*(b-res["负载预测/光伏完美"])/gap:5.1f}% of gap)')
