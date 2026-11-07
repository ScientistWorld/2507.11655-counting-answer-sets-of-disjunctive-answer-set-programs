"""Small exact checks of the genuine counter improvement; run on a job node."""
from itertools import product
import random
from method.sharpasp_sr.counter import count_models, projected_count

rng = random.Random(4921)
checks = 0
for n in range(1, 7):
    for _ in range(40):
        clauses = []
        for _ in range(rng.randrange(0, 12)):
            vs = rng.sample(range(1, n + 1), rng.randrange(0, min(n, 3) + 1))
            clauses.append(tuple(v * rng.choice((-1, 1)) for v in vs))
        projection = rng.sample(range(1, n + 1), rng.randrange(n + 1))
        models = [assignment for assignment in product((False, True), repeat=n)
                  if all(any(assignment[abs(lit) - 1] == (lit > 0) for lit in clause) for clause in clauses)]
        assert count_models(clauses, n) == len(models), (n, clauses)
        assert projected_count(clauses, projection) == len({tuple(m[v - 1] for v in projection) for m in models})
        checks += 2
print(f'{checks} exhaustive ordinary/projected-count checks passed')
