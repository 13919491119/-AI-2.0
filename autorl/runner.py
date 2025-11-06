import argparse
import json
import os
import random
from datetime import datetime, timezone
from typing import Dict, List, Tuple

from .pbt import pbt_evolve
from .specs import EnvSpec, default_env_specs, evaluate_candidate_on_env, aggregate_metrics
from .meta_metrics import save_run_artifact, gate_improvement


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def evaluate_params_across_envs(param_dict: Dict[str, float], env_specs: List[EnvSpec], *, 
                                steps_train: int, steps_eval: int, seeds: List[int]) -> Tuple[float, Dict[str, Dict[str, float]], Dict[str, float]]:
    env_results: List[Tuple[str, Dict[str, float]]] = []
    # Train/eval is simplified: for bandit we reuse same routine; steps_eval used same as steps_train here to keep cheap.
    for i, spec in enumerate(env_specs):
        # mix seed per env for variance
        seed = seeds[i % len(seeds)]
        metrics = evaluate_candidate_on_env(spec, param_dict, seed=seed, steps=steps_train)
        env_results.append((spec.name, metrics))
    agg = aggregate_metrics(env_results)
    # Composite score for PBT
    score = float(agg.get("avg_mean_reward", 0.0)) - 0.1 * float(agg.get("avg_std_reward", 0.0))
    # package per-env
    env_map = {name: m for name, m in env_results}
    return score, env_map, agg


def main():
    parser = argparse.ArgumentParser(description="AutoRL/Meta-RL lightweight runner (PBT over bandits)")
    parser.add_argument("--population", type=int, default=8)
    parser.add_argument("--generations", type=int, default=6)
    parser.add_argument("--train-steps", type=int, default=300)
    parser.add_argument("--eval-steps", type=int, default=300)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--min-delta", type=float, default=0.02)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    env_specs = default_env_specs()
    seeds = [args.seed, args.seed + 1, args.seed + 2]

    # Parameter search space (can be extended)
    param_space = {
        "eps_greedy": (0.0, 0.5),
        "lr": (0.01, 0.5),
    }

    # define evaluation for PBT individuals
    def eval_fn(params: Dict[str, float]) -> float:
        score, _, _ = evaluate_params_across_envs(params, env_specs, steps_train=args.train_steps, steps_eval=args.eval_steps, seeds=seeds)
        return score

    pop = pbt_evolve(
        population_size=args.population,
        generations=args.generations,
        param_space=param_space,
        eval_fn=eval_fn,
        rng=rng,
        exploit_fraction=0.25,
        explore_scale=0.12,
    )

    # Take top-k for detailed aggregation
    topk = pop[:3]
    detailed: List[Dict] = []
    for ind in topk:
        _, env_map, agg = evaluate_params_across_envs(ind.params, env_specs, steps_train=args.train_steps, steps_eval=args.eval_steps, seeds=seeds)
        detailed.append({
            "params": ind.params,
            "score": ind.score,
            "per_env": env_map,
            "aggregate": agg,
        })

    # Choose best by aggregate score
    best = max(detailed, key=lambda d: float(d["aggregate"].get("avg_mean_reward", 0.0) - 0.1 * d["aggregate"].get("avg_std_reward", 0.0)))
    agg = best["aggregate"]

    payload = {
        "ts": _now_iso(),
        "env_specs": [s.__dict__ for s in env_specs],
        "population": args.population,
        "generations": args.generations,
        "train_steps": args.train_steps,
        "eval_steps": args.eval_steps,
        "seed": args.seed,
        "topk": detailed,
        "best": best,
    }

    filename = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path = save_run_artifact(filename, payload)

    decision = gate_improvement(agg, key="avg_mean_reward", min_delta=args.min_delta)
    payload["gate_decision"] = decision
    # Update file with decision
    save_run_artifact(filename, payload)

    # Optional stdout for logs
    print(f"[autorl] Saved run to {path}")
    print(f"[autorl] Gate: improved={decision['improved']} prev={decision['previous']:.4f} -> cur={decision['current']:.4f}")


if __name__ == "__main__":
    main()
