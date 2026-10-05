# -*- coding: utf-8 -*-
"""N=20 小规模：IQL（独立奖励）vs VDN（全局奖励，值分解）的协同学习对比。"""
import numpy as np, json
from collections import deque
W,H=24.0,16.0
EXITS=[(0.0,8.0,1.6),(24.0,8.0,1.2),(12.0,0.0,0.8)]
V0=1.34; FLOW=0.73; DT=0.2; MAXT=400.0
N=20

def bin_of(x,mx,b=4): return int(min(b-1, x/mx*b))
def state(pos,q):
    d=[np.hypot(pos[0]-EXITS[e][0],pos[1]-EXITS[e][1]) for e in range(3)]
    bd=bin_of(min(d),24.0); bq=bin_of(min(q),15.0)
    return bd*4+bq
S=16; A=3

def make_pos(seed):
    rng=np.random.default_rng(seed); parts=[]
    for cx,cy,w in [(12,3,0.60),(19,8,0.25),(5,8,0.15)]:
        m=int(round(N*w)); p=rng.normal(loc=(cx,cy),scale=(2.2,1.6),size=(m,2))
        p[:,0]=np.clip(p[:,0],0.5,W-0.5); p[:,1]=np.clip(p[:,1],0.5,H-0.5); parts.append(p)
    return np.concatenate(parts)[:N].copy()

def train(algo, seed, eps=150, lr=0.15, gam=0.95):
    rng=np.random.default_rng(seed)
    Q=np.zeros((S,A),np.float32)
    epsilon=1.0
    curves=[]
    for ep in range(eps):
        pos=make_pos(seed+ep); arrived=np.zeros(N,bool); departed=np.zeros(N,bool)
        queues=[deque() for _ in range(3)]; frac=[0.0]*3; ep_r=0.0; step=0
        while not departed.all() and step<1200:
            step+=1
            # 出口服务
            for e in range(3):
                frac[e]+=EXITS[e][2]*FLOW*DT; no=int(frac[e])
                for _ in range(no):
                    if queues[e]: i=queues[e].popleft(); departed[i]=True
                frac[e]-=no
            qlen=[len(queues[e]) for e in range(3)]
            acts=np.zeros(N,int); ss=np.zeros(N,int)
            for i in range(N):
                if arrived[i] or departed[i]: continue
                si=state(pos[i],qlen); ss[i]=si
                a=int(rng.integers(0,3)) if rng.random()<epsilon else int(np.argmax(Q[si]))
                acts[i]=a
            # 移动
            for i in range(N):
                if arrived[i] or departed[i]: continue
                e=acts[i]; ex,ey=EXITS[e][0],EXITS[e][1]
                dx=ex-pos[i,0]; dy=ey-pos[i,1]; dist=np.hypot(dx,dy); s=V0*DT
                pos[i,0]+=dx/dist*s; pos[i,1]+=dy/dist*s
                if dist<0.5: arrived[i]=True; queues[e].append(i)
            # 奖励与更新
            if algo=="iql":
                for i in range(N):
                    if departed[i]: continue
                    r=-0.01
                    if arrived[i]: r=0.0
                    si=ss[i]; a=acts[i]; nq=[len(queues[e]) for e in range(3)]
                    si2=state(pos[i],nq)
                    Q[si,a]+=lr*(r+gam*Q[si2].max()-Q[si,a])
                    ep_r+=r
            else:  # vdn：全局奖励 + 值分解（Q_tot = Σ Q(s_i,a_i)）
                r=-( ( (~departed).sum() )/N )*0.01
                ep_r+=r
                qn=[len(queues[e]) for e in range(3)]
                active=[i for i in range(N) if not departed[i]]
                if active:
                    qtot=sum(Q[state(pos[i],qn), acts[i]] for i in active if not arrived[i])
                    # 下一步 q_tot（argmax 各自）
                    qnext=0.0
                    for i in active:
                        if arrived[i]: continue
                        si2=state(pos[i],qn); qnext+=Q[si2].max()
                    td=r+gam*qnext-qtot
                    for i in active:
                        if arrived[i]: continue
                        si=state(pos[i],qn); Q[si,acts[i]]+=lr*(td/len(active))
        epsilon=max(0.05,epsilon*0.992)
        curves.append(ep_r)
    return Q, curves

def eval_policy(Q, seed, n=20):
    T=[]; flows=[]
    for k in range(n):
        pos=make_pos(seed+100+k); arrived=np.zeros(N,bool); departed=np.zeros(N,bool)
        queues=[deque() for _ in range(3)]; frac=[0.0]*3; flow=[0,0,0]
        for step in range(1600):
            for e in range(3):
                frac[e]+=EXITS[e][2]*FLOW*DT; no=int(frac[e])
                for _ in range(no):
                    if queues[e]: i=queues[e].popleft(); departed[i]=True; flow[e]+=1
                frac[e]-=no
            if departed.all(): break
            qlen=[len(queues[e]) for e in range(3)]
            for i in range(N):
                if arrived[i] or departed[i]: continue
                si=state(pos[i],qlen); e=int(np.argmax(Q[si]))
                ex,ey=EXITS[e][0],EXITS[e][1]; dx=ex-pos[i,0]; dy=ey-pos[i,1]; dist=np.hypot(dx,dy); s=V0*DT
                pos[i,0]+=dx/dist*s; pos[i,1]+=dy/dist*s
                if dist<0.5: arrived[i]=True; queues[e].append(i)
        T.append(step*DT); flows.append(flow)
    def gini(x):
        x=np.sort(np.asarray(x,float)); nn=len(x)
        return (2*np.sum(np.arange(1,nn+1)*x)-(nn+1)*np.sum(x))/(nn*np.sum(x)) if x.sum()>0 else 0
    return float(np.mean(T)), float(np.mean([gini(f) for f in flows])), [int(round(x)) for x in np.mean(flows,axis=0)]

if __name__=="__main__":
    out={}
    for algo in ["iql","vdn"]:
        cs=[]; ev=[]
        for seed in [1,2,3]:
            Q,c=train(algo,seed,400); cs.append(c); ev.append(eval_policy(Q,seed))
        C=np.array(cs)
        out[algo]={"curve_mean":C.mean(0).tolist(),"curve_std":C.std(0).tolist(),
                   "eval":[[round(x,2) for x in e] for e in ev]}
        print(algo, "eval(T,Gini,flow):", out[algo]["eval"])
    json.dump(out,open("/tmp/vdn_iql.json","w"),ensure_ascii=False)
