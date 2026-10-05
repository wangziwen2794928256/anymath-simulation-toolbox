# -*- coding: utf-8 -*-
"""Climbing Game（经典协同矩阵博弈）：IQL vs QMIX 值分解，展示协同学习与信用分配。"""
import numpy as np, json
# 收益矩阵（共同收益，2 智能体 × 3 动作）
PAY=[[11,-30,0],[-30,7,6],[0,6,5]]
A=3
def pay(a,b): return PAY[a][b]

def train_iql(seed, eps=3000, lr=0.2, gam=0.95):
    rng=np.random.default_rng(seed); Q=[np.zeros(A),np.zeros(A)]; e=1.0; crv=[]
    for ep in range(eps):
        a=int(rng.integers(0,3)) if rng.random()<e else int(np.argmax(Q[0]))
        b=int(rng.integers(0,3)) if rng.random()<e else int(np.argmax(Q[1]))
        r=pay(a,b)
        Q[0][a]+=lr*(r+gam*Q[0].max()-Q[0][a])
        Q[1][b]+=lr*(r+gam*Q[1].max()-Q[1][b])
        e=max(0.01,e*0.999); crv.append(r)
    return Q,crv

def train_qmix(seed, eps=3000, lr=0.2, gam=0.95):
    rng=np.random.default_rng(seed)
    Q=[np.zeros(A),np.zeros(A)]
    w=np.abs(rng.normal(1,0.2,2))  # 单调混合权重
    e=1.0; crv=[]
    for ep in range(eps):
        a=int(rng.integers(0,3)) if rng.random()<e else int(np.argmax(Q[0]))
        b=int(rng.integers(0,3)) if rng.random()<e else int(np.argmax(Q[1]))
        r=pay(a,b)
        qtot=w[0]*Q[0][a]+w[1]*Q[1][b]
        qnext=w[0]*Q[0].max()+w[1]*Q[1].max()
        td=r+gam*qnext-qtot
        Q[0][a]+=lr*td; Q[1][b]+=lr*td
        e=max(0.01,e*0.999); crv.append(r)
    return Q,w,crv

def evaluate(Q):
    a=np.argmax(Q[0]); b=np.argmax(Q[1]); return pay(a,b), (int(a),int(b))

if __name__=="__main__":
    out={}
    # IQL 多 seed
    for algo in ["iql","qmix"]:
        crvs=[]; pays=[]
        for s in [0,1,2]:
            if algo=="iql": Q,c=train_iql(s)
            else: Q,w,c=train_qmix(s)
            p,pol=evaluate(Q); crvs.append(c); pays.append(p)
        C=np.array(crvs)
        out[algo]={"curve_mean":C.mean(0)[::20].round(2).tolist(),"pays":pays,
                    "final_policy":[evaluate(train_iql(s)[0] if algo=='iql' else train_qmix(s)[0])[1] for s in [0,1,2]]}
        print(algo,"final payoffs:",pays,"policies:",out[algo]["final_policy"])
    json.dump(out,open("/tmp/climbing.json","w"),ensure_ascii=False)
    print("最优共同收益=11（协调 (a,a)），次优=7 (b,b)，陷阱=5 (c,c)")
