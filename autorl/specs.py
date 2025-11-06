import math
import random
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class EnvSpec:
    name: str
    kind: str  # 'bandit' | 'synthetic'
    arms: int = 5
    nonstationary: bool = True


class NonStationaryBandit:
    """
    Simple non-stationary K-armed bandit: each arm has a drifting mean reward.
    Rewards ~ N(mu_t, 1). A training loop chooses actions and updates action-value estimates.
    """

    def __init__(self, seed: int, arms: int = 5, drift: float = 0.01):
        self.random = random.Random(seed)
        self.arms = arms
        self.drift = drift
        # Initialize arm means
        self.means = [self.random.gauss(0.0, 1.0) for _ in range(arms)]

    def step(self, action: int) -> float:
        # reward from current mean + unit Gaussian noise
        base = self.means[action]
        reward = self.random.gauss(base, 1.0)
        # drift all arms
        for i in range(self.arms):
            self.means[i] += self.random.gauss(0.0, self.drift)
        return reward


def default_env_specs() -> List[EnvSpec]:
    # A small set of bandit variations; keep cheap and fast
    return [
        EnvSpec(name="bandit_ns5", kind="bandit", arms=5, nonstationary=True),
        EnvSpec(name="bandit_ns7", kind="bandit", arms=7, nonstationary=True),
        EnvSpec(name="bandit_s5", kind="bandit", arms=5, nonstationary=False),
    ]


def make_env(spec: EnvSpec, seed: int):
    if spec.kind == "bandit":
        # Non-stationary vs stationary: set drift accordingly
        drift = 0.01 if spec.nonstationary else 0.0
        return NonStationaryBandit(seed=seed, arms=spec.arms, drift=drift)
    raise ValueError(f"Unknown env kind: {spec.kind}")


def train_and_eval_bandit(env: NonStationaryBandit, *, steps: int, 
                          eps_greedy: float, lr: float, seed: int) -> Dict[str, float]:
    """
    Lightweight bandit training loop with epsilon-greedy policy and constant-step-size Q updates.
    Returns mean reward and regret proxy.
    """
    rng = random.Random(seed + 12345)
    arms = env.arms
    Q = [0.0] * arms
    counts = [0] * arms
    rewards: List[float] = []

    for t in range(steps):
        explore = rng.random() < eps_greedy
        if explore:
            a = rng.randrange(arms)
        else:
            # break ties deterministically by index
            max_q = max(Q)
            a = next(i for i, q in enumerate(Q) if q == max_q)
        r = env.step(a)
        counts[a] += 1
        # constant step-size update (meta-parameter lr)
        Q[a] = (1 - lr) * Q[a] + lr * r
        rewards.append(r)

    # simple metrics
    mean_r = sum(rewards) / max(1, len(rewards))
    std_r = (sum((x - mean_r) ** 2 for x in rewards) / max(1, len(rewards))) ** 0.5
    # regret proxy: difference to optimistic upper bound (unknown optimal), so use |Q| dispersion
    dispersion = max(Q) - min(Q)
    return {"mean_reward": mean_r, "std_reward": std_r, "dispersion": dispersion}


def evaluate_candidate_on_env(spec: EnvSpec, params: Dict[str, float], *, seed: int, steps: int) -> Dict[str, float]:
    env = make_env(spec, seed)
    eps = float(params.get("eps_greedy", 0.1))
    lr = float(params.get("lr", 0.1))
    eps = min(max(eps, 0.0), 1.0)
    lr = min(max(lr, 0.0), 1.0)
    return train_and_eval_bandit(env, steps=steps, eps_greedy=eps, lr=lr, seed=seed)


def aggregate_metrics(env_results: List[Tuple[str, Dict[str, float]]]) -> Dict[str, float]:
    # Average across environments for key metrics
    keys = {k for _, m in env_results for k in m.keys()}
    agg: Dict[str, float] = {}
    for k in keys:
        vals = [m[k] for _, m in env_results if k in m]
        agg[f"avg_{k}"] = sum(vals) / max(1, len(vals))
    return agg
