from __future__ import annotations

from dataclasses import dataclass, field


Lit = int
Clause = tuple[Lit, ...]


@dataclass
class CNF:
    var_ids: dict[str, int] = field(default_factory=dict)
    names: dict[int, str] = field(default_factory=dict)
    clauses: list[Clause] = field(default_factory=list)

    def var(self, name: str) -> int:
        if name not in self.var_ids:
            idx = len(self.var_ids) + 1
            self.var_ids[name] = idx
            self.names[idx] = name
        return self.var_ids[name]

    def lit(self, name: str, positive: bool = True) -> int:
        v = self.var(name)
        return v if positive else -v

    def add_clause(self, lits: list[int] | tuple[int, ...]) -> None:
        uniq = []
        seen = set()
        for lit in lits:
            if -lit in seen:
                return
            if lit not in seen:
                uniq.append(lit)
                seen.add(lit)
        self.clauses.append(tuple(uniq))

    def new_aux(self, prefix: str = "aux") -> int:
        idx = len(self.var_ids) + 1
        while True:
            name = f"__{prefix}_{idx}"
            if name not in self.var_ids:
                return self.var(name)
            idx += 1

    def add_implication(self, antecedent: list[int], consequent: list[int]) -> None:
        self.add_clause([-lit for lit in antecedent] + consequent)

    def add_and_equiv(self, out: int, inputs: list[int]) -> None:
        for lit in inputs:
            self.add_clause([-out, lit])
        self.add_clause([out] + [-lit for lit in inputs])

    def extend(self, clauses: list[Clause]) -> None:
        for clause in clauses:
            self.add_clause(clause)
