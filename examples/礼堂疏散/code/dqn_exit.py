# -*- coding: utf-8 -*-
"""线性 Q-learning 出口选择：特征=距离+排队，动作=3出口。稳定、有训练曲线。"""
import numpy as np, json
W,H=24.0,16.0
EXITS=[(0.0,8.0),(24.0,8.0),(12.0,0.0)]
V0=1.34; DT=0.1
GAMMA=0.98; LR=0.02

def feat(pos,q):
    d=[np.hypot(pos[0]-EXITS[e][0],pos[1]-EXITS[e][1])/24.0 for e in range(3)]
    return np.array(d+[q[e]/15.0 for e in range(3)],np.float32)

def step_agent(pos,a,q):
    ex,ey=EXITS[a]; dx=ex-pos[0]; dy=ey-pos[1]; d=np.hypot(dx,dy)
    if d<0.4:
        return pos, True, -0.0
    s=V0*DT
    return (pos[0]+dx/d*s, pos[1]+dy/d*s), False, -0.1

def train(seed, episodes=1500):
    rng=np.random.default_rng(seed)
    w=rng.normal(0,0.1,(3,6)).astype(np.float32)
    eps=1.0; curve=[]
    for ep in range(episodes):
        pos=(float(rng.uniform(2,22)), float(rng.uniform(2,14)))
        q=[0.0,0.0,0.0]; done=False; R=0.0; st=0
        while not done and st<600:
            s=feat(pos,q)
            if rng.random()<eps: a=int(rng.integers(0,3))
            else: a=int(np.argmax(w@s))
            q=[min(15.0,max(0.0,q[e]+(1.0 if e==a else 0.0)-0.35)) for e in range(3)]
            pos,done,r=step_agent(pos,a,q)
            s2=feat(pos,q)
            q2=w@s2
            td=r+GAMMA*q2.max()-float(w[a]@s)
            w[a]+=LR*td*s
            R+=r; st+=1
        eps=max(0.05,eps*0.996)
        curve.append(R)
    return w, curve

def eval_policy(w, n=100):
    rng=np.random.default_rng(123); R=[]
    for _ in range(n):
        pos=(float(rng.uniform(2,22)), float(rng.uniform(2,14))); q=[0.0]*3; done=False; rsum=0; st=0
        while not done and st<600:
            a=int(np.argmax(w@feat(pos,q)))
            q=[min(15.0,max(0.0,q[e]+(1.0 if e==a else 0.0)-0.35)) for e in range(3)]
            pos,done,r=step_agent(pos,a,q); rsum+=r; st+=1
        R.append(rsum)
    return float(np.mean(R)), float(np.std(R))

if __name__=="__main__":
    curves=[]; ev=[]
    for seed in [1,2,3]:
        w,c=train(seed); curves.append(c); ev.append(eval_policy(w))
    C=np.array(curves)
    json.dump({"curve_mean":C.mean(0).tolist(),"curve_std":C.std(0).tolist(),
               "eval":[[float(x) for x in e] for e in ev]}, open("/tmp/dqn_results.json","w"))
    print("eval:", [round(e[0],2) for e in ev])
    print("curve first/last (mean):", round(C.mean(0)[0],2), round(C.mean(0)[-1],2))
