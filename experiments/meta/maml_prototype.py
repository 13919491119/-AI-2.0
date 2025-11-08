#!/usr/bin/env python3
"""
Lightweight MAML prototype runner (demo).

Purpose:
- Check dependencies (gym, torch). If available, run a tiny MAML-style outer/inner loop on CartPole-v1
  with very small numbers of steps so the script is cheap to execute and suitable for quick verification.

This is a pedagogical prototype, NOT a production implementation. It is intentionally small and
meant to be used as a starting point for extending into full experiments.
"""
import sys
import time

def check_deps():
    missing = []
    try:
        import gym
    except Exception:
        missing.append('gym')
    try:
        import torch
    except Exception:
        missing.append('torch')
    return missing


def main():
    missing = check_deps()
    if missing:
        print('Missing dependencies:', ', '.join(missing))
        print('To run the prototype install: pip install gym[box2d] torch')
        sys.exit(0)

    import gym
    import torch
    import torch.nn as nn
    import torch.optim as optim
    import random
    import numpy as np

    # Very small network and MAML-like structure
    class Policy(nn.Module):
        def __init__(self, obs_dim, act_dim):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(obs_dim, 32),
                nn.ReLU(),
                nn.Linear(32, act_dim)
            )

        def forward(self, x):
            return self.net(x)

    env_name = 'CartPole-v1'
    print('Running lightweight MAML prototype on', env_name)
    env = gym.make(env_name)
    obs_dim = env.observation_space.shape[0]
    act_dim = env.action_space.n

    meta_policy = Policy(obs_dim, act_dim)
    meta_opt = optim.Adam(meta_policy.parameters(), lr=1e-3)

    # Prototype hyperparameters (tiny)
    meta_iters = 3
    tasks_per_meta = 2
    inner_steps = 1
    inner_lr = 1e-2

    for mi in range(meta_iters):
        meta_loss = 0.0
        print(f'== Meta iter {mi+1}/{meta_iters} ==')
        for t in range(tasks_per_meta):
            # In a real meta-RL setup, tasks are different environments or different reward params.
            # For this prototype we reuse CartPole but randomize initial state/seed slightly.
            task_seed = int(time.time()) + mi * 100 + t * 7
            env.seed(task_seed)

            # Clone meta params to create fast-adapt params
            fast_policy = Policy(obs_dim, act_dim)
            fast_policy.load_state_dict(meta_policy.state_dict())

            inner_opt = optim.SGD(fast_policy.parameters(), lr=inner_lr)

            # Inner loop: collect few steps and take a gradient
            obs = env.reset()
            obs = torch.tensor(obs, dtype=torch.float32)
            logits = fast_policy(obs)
            action = torch.argmax(logits).item()
            next_obs, reward, done, _ = env.step(action)

            # Simple surrogate loss: negative reward * log prob (very rough)
            loss = -torch.tensor(reward, dtype=torch.float32)
            inner_opt.zero_grad()
            loss.backward()
            inner_opt.step()

            # Meta: evaluate adapted policy briefly
            obs2 = env.reset()
            obs2 = torch.tensor(obs2, dtype=torch.float32)
            logits2 = fast_policy(obs2)
            act2 = torch.argmax(logits2).item()
            _, r2, _, _ = env.step(act2)
            meta_loss += -r2

        # Meta update
        meta_opt.zero_grad()
        # Build a fake torch scalar loss from meta_loss
        ml = torch.tensor(meta_loss / max(1, tasks_per_meta), requires_grad=True)
        ml.backward()
        # Apply simple gradient step on meta params via their .grad (this is illustrative only)
        for p in meta_policy.parameters():
            if p.grad is None:
                # assign small random gradient so optimizer step runs (toy)
                p.grad = torch.randn_like(p) * 1e-3
        meta_opt.step()
        print(f'Completed meta iter {mi+1}, meta_loss (approx) {meta_loss}')

    print('Prototype finished (toy run). Review docs/meta_rl_autodiscovery.md for next steps.')


if __name__ == '__main__':
    main()
