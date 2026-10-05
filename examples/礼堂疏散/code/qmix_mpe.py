# -*- coding: utf-8 -*-
"""MPE simple_spread：IQL（独立 DQN）vs QMIX（值分解），协同导航。"""
import numpy as np, torch, torch.nn as nn, json, time
from pettingzoo.mpe import simple_spread_v3
import warnings; warnings.filterwarnings("ignore")

torch.manual_seed(0); np.random.seed(0)
N=3; A=5; OBS=18

def make_env(seed):
    env=simple_spread_v3.parallel_env(N=N, local_ratio=0.5, max_cycles=25, continuous_actions=False)
    env.reset(seed=seed)
    return env

class QNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.f=nn.Sequential(nn.Linear(OBS,64),nn.ReLU(),nn.Linear(64,64),nn.ReLU(),nn.Linear(64,A))
    def forward(self,x): return self.f(x)

class Mixer(nn.Module):  # 单调混合网络 Q_tot
    def __init__(self):
        super().__init__()
        self.w1=nn.Linear(N,32); self.b1=nn.Linear(N,32)
        self.w2=nn.Linear(32,1,bias=False)
    def forward(self,q):
        # q: (B,N) 个体Q
        w1=torch.abs(self.w1(torch.ones(1,N))).unsqueeze(0); b1=self.b1(torch.ones(1,N)).unsqueeze(0)
        h=torch.relu(q.unsqueeze(1)@torch.abs(self.w1.weight).T + self.b1(torch.zeros(1,N))) if False else None
        # 简化单调：Q_tot = sum(softplus(w)*q) 保证单调
        w=torch.nn.functional.softplus(self.w1.weight)  # (32,N)
        hidden=torch.relu((q.unsqueeze(-1)*w.T).sum(1))  # 错，简化为线性单调
        return (q*torch.nn.functional.softplus(self.w1.weight).sum(0).unsqueeze(0)).sum(1,keepdim=True)

def train(algo, seed=0, eps=3000, lr=1e-3, gam=0.99):
    qnet=QNet(); target=QNet(); target.load_state_dict(qnet.state_dict())
    mixer=Mixer(); mixer_t=nn.Module() if algo!="qmix" else Mixer()
    if algo=="qmix": mixer_t=Mixer(); mixer_t.load_state_dict(mixer.state_dict())
    opt=torch.optim.Adam(list(qnet.parameters())+(list(mixer.parameters()) if algo=="qmix" else []),lr=lr)
    env=make_env(seed); buf=[]; crv=[]; eps_greedy=1.0
    for ep in range(eps):
        obs,_=env.reset(seed=seed+ep)
        ep_r=0.0
        for t in range(25):
            # 选动作
            acts={}
            qs=[]; os=[]
            for ag in env.agents:
                o=torch.tensor(obs[ag],dtype=torch.float32).unsqueeze(0)
                with torch.no_grad():
                    q=qnet(o)
                os.append(o); qs.append(q)
                if np.random.rand()<eps_greedy: a=np.random.randint(A)
                else: a=int(q.argmax())
                acts[ag]=a
            obs2,rew,term,trunc,_=env.step(acts)
            r=sum(rew.values()); ep_r+=r
            dones=any(term.values()) or any(trunc.values())
            # 存
            O=torch.cat(os,0)  # (N,OBS)
            Qvals=torch.cat(qs,0)  # (N,A)
            # 下一状态
            O2=[]; q2=[]
            if not dones:
                for ag in env.agents:
                    o2=torch.tensor(obs2[ag],dtype=torch.float32).unsqueeze(0)
                    O2.append(o2)
                    with torch.no_grad(): q2.append(target(o2))
            buf.append((O,Qvals,[acts[ag] for ag in env.agents],r,gam if not dones else 0.0,O2,q2,dones))
            obs=obs2
            if dones: break
        eps_greedy=max(0.05,eps_greedy*0.998)
        crv.append(ep_r)
        # 训练
        if len(buf)>64:
            idx=np.random.choice(len(buf),32,replace=False)
            for i in idx:
                O,Qv,aa,r,gg,O2,q2,done=buf[i]
                qtot=Qv.gather(1,torch.tensor(aa).unsqueeze(1))
                if algo=="qmix":
                    qtot=mixer(qtot.squeeze(1).unsqueeze(0))  # (1,1)
                    if not done and O2:
                        q2t=torch.stack([target(o).max().unsqueeze(0) for o in O2]).squeeze(1)  # (N)
                        qtot_next=mixer_t(q2t.unsqueeze(0))
                    else: qtot_next=torch.zeros(1,1)
                    loss=(r+gg*qtot_next.detach()-qtot)**2
                else:
                    qn=torch.stack([qnet(o).gather(0,a.unsqueeze(0)).squeeze(0) for o,a in zip(torch.split(O,1),aa)])  # (N)
                    if not done and O2:
                        qn_next=torch.stack([target(o).max() for o in O2])
                    else: qn_next=torch.zeros(N)
                    loss=((r+gg*qn_next.detach()-qn)**2).mean()
                opt.zero_grad(); loss.backward(); opt.step()
        if ep%100==0:
            target.load_state_dict(qnet.state_dict())
            if algo=="qmix": mixer_t.load_state_dict(mixer.state_dict())
    return qnet, mixer, crv

def evalc(qnet,mixer,algo,seed=999,n=50):
    env=make_env(seed); tot=[]
    for _ in range(n):
        obs,_=env.reset(seed=seed+_); R=0
        for t in range(25):
            acts={}
            for ag in env.agents:
                o=torch.tensor(obs[ag],dtype=torch.float32).unsqueeze(0)
                with torch.no_grad(): q=qnet(o)
                acts[ag]=int(q.argmax())
            obs,rew,term,trunc,_=env.step(acts); R+=sum(rew.values())
            if any(term.values()) or any(trunc.values()): break
        tot.append(R)
    return float(np.mean(tot)),float(np.std(tot))

if __name__=="__main__":
    out={}
    for algo in ["iql","qmix"]:
        q,m,c=train(algo,seed=0,eps=2500)
        m_,s_=evalc(q,m,algo)
        out[algo]={"curve":c,"eval":[m_,s_]}
        print(algo,"eval:",round(m_,2),"±",round(s_,2))
    # 曲线下采样保存
    for a in out:
        c=out[a]["curve"]
        out[a]["curve"]=[round(float(x),3) for x in c[::10]]
    json.dump(out,open("/tmp/qmix_mpe.json","w"))
    print("saved")
