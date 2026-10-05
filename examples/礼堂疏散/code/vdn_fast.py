# -*- coding: utf-8 -*-
"""快速版：N=10，IQL vs VDN，表格 Q，向量化内循环。"""
import numpy as np, json
W,H=24.0,16.0; EXITS=[(0.,8.,1.6),(24.,8.,1.2),(12.,0.,0.8)]; V0=1.34; FLOW=0.73; DT=0.3; N=10; MAXT=400
S=16; A=3
def state(P,q):
    # q: (3,) 全局各出口排队；P:(N,2)
    D=np.hypot(P[:,0:1]-np.array([e[0] for e in EXITS])[None,:], P[:,1:2]-np.array([e[1] for e in EXITS])[None,:])  # (N,3)
    dmin=D.min(1); e=np.argmin(D,1)
    qe=np.array(q)[e]
    bd=(dmin/24*4).astype(int).clip(0,3); bq=(qe/15*4).astype(int).clip(0,3)
    return bd*4+bq
def make_pos(seed):
    rng=np.random.default_rng(seed); P=rng.uniform(1,23,(N,2)); P[:,1]=rng.uniform(1,15,N); return P
def gini(x):
    x=np.sort(np.asarray(x,float)); n=len(x); return (2*np.sum(np.arange(1,n+1)*x)-(n+1)*np.sum(x))/(n*np.sum(x)) if x.sum()>0 else 0
def train(algo,seed,eps=60):
    rng=np.random.default_rng(seed); Q=np.zeros((S,A)); epss=1.0; crv=[]
    for ep in range(eps):
        P=make_pos(seed+ep); arrv=np.zeros(N,bool); dept=np.zeros(N,bool); q=[0.,0.,0.]; fr=[0.,0.,0.]; rsum=0.0
        for st in range(1500):
            for e in range(3):
                fr[e]+=EXITS[e][2]*FLOW*DT; no=int(fr[e])
                # 简化：直接按容量减少排队（不追踪身份）
                fr[e]-=no; q[e]=max(0,q[e]-no)
            if dept.all(): break
            Qlen=min(q) if False else q
            ss=state(P,np.array(q))
            a=np.array([int(rng.integers(0,3)) if rng.random()<epss else int(np.argmax(Q[s])) for s in ss])
            # 移动
            for i in range(N):
                if arrv[i] or dept[i]: continue
                e=a[i]; ex,ey=EXITS[e][0],EXITS[e][1]; dx=ex-P[i,0]; dy=ey-P[i,1]; dist=np.hypot(dx,dy)
                P[i,0]+=dx/dist*V0*DT; P[i,1]+=dy/dist*V0*DT
                if dist<0.5: arrv[i]=True; q[e]+=1
            # 离场：按容量
            for e in range(3):
                for _ in range(int(EXITS[e][2]*FLOW*DT)):
                    if q[e]>0: q[e]-=1
            if algo=="iql":
                for i in range(N):
                    if dept[i]: continue
                    r=-0.01 if not arrv[i] else 0.0
                    Q[ss[i],a[i]]+=0.15*(r+0.95*Q[ss[i]].max()-Q[ss[i],a[i]]); rsum+=r
            else:
                r=-(np.sum(~dept)/N)*0.01; rsum+=r
                ss2=state(P,np.array(q))
                qtot=sum(Q[ss[i],a[i]] for i in range(N) if not dept[i])
                qnext=sum(Q[ss2[i]].max() for i in range(N) if not dept[i])
                td=r+0.95*qnext-qtot
                for i in range(N):
                    if not dept[i]: Q[ss[i],a[i]]+=0.15*(td/N)
        epss=max(0.05,epss*0.98); crv.append(rsum)
    return Q,crv
def evalc(Q,seed):
    P=make_pos(seed+999); arrv=np.zeros(N,bool); dept=np.zeros(N,bool); q=[0.,0.,0.]; fr=[0.,0.,0.]; flow=[0,0,0]
    for st in range(2000):
        for e in range(3):
            fr[e]+=EXITS[e][2]*FLOW*DT; no=int(fr[e]); fr[e]-=no
            for _ in range(no):
                if q[e]>0: q[e]-=1; flow[e]+=1
        if dept.all(): break
        ss=state(P,np.array(q)); a=np.array([int(np.argmax(Q[s])) for s in ss])
        for i in range(N):
            if arrv[i] or dept[i]: continue
            e=a[i]; ex,ey=EXITS[e][0],EXITS[e][1]; dx=ex-P[i,0]; dy=ey-P[i,1]; dist=np.hypot(dx,dy)
            P[i,0]+=dx/dist*V0*DT; P[i,1]+=dy/dist*V0*DT
            if dist<0.5: arrv[i]=True; q[e]+=1
    return st*DT, gini(flow), flow
out={}
for algo in ["iql","vdn"]:
    Q,c=train(algo,1,60); t,g,f=evalc(Q,1)
    out[algo]={"T":round(t,1),"gini":round(g,3),"flow":[int(x) for x in f],"curve":c}
    print(algo,"T",round(t,1),"gini",round(g,3),"flow",[int(x) for x in f],"curve_last",round(c[-1],2))
json.dump({k:{**v,"curve":None} for k,v in out.items()},open("/tmp/vdn_fast.json","w"))
# 存曲线
json.dump({"iql_curve":out["iql"]["curve"],"vdn_curve":out["vdn"]["curve"]},open("/tmp/vdn_curves.json","w"))
