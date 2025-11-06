import random
from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple


ParamSpace = Dict[str, Tuple[float, float]]  # name -> (min, max)


@dataclass
class Individual:
    params: Dict[str, float]
    score: float = float('-inf')


def random_params(space: ParamSpace, rng: random.Random) -> Dict[str, float]:
    return {k: rng.uniform(v[0], v[1]) for k, v in space.items()}


def mutate(params: Dict[str, float], space: ParamSpace, rng: random.Random, scale: float = 0.2) -> Dict[str, float]:
    out = dict(params)
    for k, (lo, hi) in space.items():
        span = hi - lo
        delta = rng.gauss(0.0, scale * span)
        out[k] = min(max(out[k] + delta, lo), hi)
    return out


def pbt_evolve(
    *,
    population_size: int,
    generations: int,
    param_space: ParamSpace,
    eval_fn: Callable[[Dict[str, float]], float],
    rng: random.Random,
    exploit_fraction: float = 0.2,
    explore_scale: float = 0.15,
) -> List[Individual]:
    assert population_size >= 2
    # initialize population
    pop: List[Individual] = [Individual(params=random_params(param_space, rng)) for _ in range(population_size)]
    # evaluate
    for ind in pop:
        ind.score = float(eval_fn(ind.params))

    for _ in range(generations):
        # sort by score desc
        pop.sort(key=lambda x: x.score, reverse=True)
        elite_n = max(1, int(exploit_fraction * population_size))
        elites = pop[:elite_n]
        # exploit/explore: replace worst individuals by mutated elites
        for i in range(elite_n, population_size):
            parent = rng.choice(elites)
            child_params = mutate(parent.params, param_space, rng, scale=explore_scale)
            pop[i] = Individual(params=child_params)
            pop[i].score = float(eval_fn(pop[i].params))
    # final sort
    pop.sort(key=lambda x: x.score, reverse=True)
    return pop
