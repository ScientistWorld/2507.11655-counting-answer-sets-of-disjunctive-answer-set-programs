from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Rule:
    head: tuple[str, ...]
    pos: tuple[str, ...]
    neg: tuple[str, ...]


@dataclass
class Program:
    rules: list[Rule]

    @property
    def atoms(self) -> list[str]:
        seen: set[str] = set()
        for rule in self.rules:
            seen.update(rule.head)
            seen.update(rule.pos)
            seen.update(rule.neg)
        return sorted(seen)


def _strip_comment(line: str) -> str:
    return line.split("%", 1)[0].strip()


def _split_atoms(text: str) -> tuple[str, ...]:
    text = text.strip()
    if not text:
        return ()
    atoms = []
    for part in text.split(","):
        atom = part.strip()
        if atom:
            atoms.append(atom)
    return tuple(atoms)


def parse_program(text: str) -> Program:
    rules: list[Rule] = []
    current = ""
    for raw_line in text.splitlines():
        line = _strip_comment(raw_line)
        if not line:
            continue
        current += " " + line
        while "." in current:
            stmt, current = current.split(".", 1)
            stmt = stmt.strip()
            if not stmt or stmt.startswith("#"):
                continue
            if ":-" in stmt:
                head_text, body_text = stmt.split(":-", 1)
            else:
                head_text, body_text = stmt, ""
            head = tuple(a.strip() for a in head_text.replace(";", "|").split("|") if a.strip())
            pos: list[str] = []
            neg: list[str] = []
            for lit in _split_atoms(body_text):
                if lit.startswith("not "):
                    neg.append(lit[4:].strip())
                else:
                    pos.append(lit)
            rules.append(Rule(head=tuple(sorted(head)), pos=tuple(sorted(pos)), neg=tuple(sorted(neg))))
    if current.strip():
        raise ValueError(f"unterminated rule: {current.strip()}")
    return Program(rules)


def load_program(path: str | Path) -> Program:
    return parse_program(Path(path).read_text())


def positive_dependency_graph(program: Program) -> dict[str, set[str]]:
    graph = {atom: set() for atom in program.atoms}
    for rule in program.rules:
        for head_atom in rule.head:
            for body_atom in rule.pos:
                graph.setdefault(head_atom, set()).add(body_atom)
                graph.setdefault(body_atom, set())
    return graph


def loop_atoms(program: Program) -> set[str]:
    graph = positive_dependency_graph(program)
    index = 0
    stack: list[str] = []
    indices: dict[str, int] = {}
    low: dict[str, int] = {}
    on_stack: set[str] = set()
    loops: set[str] = set()

    def strongconnect(v: str) -> None:
        nonlocal index
        indices[v] = index
        low[v] = index
        index += 1
        stack.append(v)
        on_stack.add(v)
        for w in graph.get(v, ()):
            if w not in indices:
                strongconnect(w)
                low[v] = min(low[v], low[w])
            elif w in on_stack:
                low[v] = min(low[v], indices[w])
        if low[v] == indices[v]:
            comp = []
            while True:
                w = stack.pop()
                on_stack.remove(w)
                comp.append(w)
                if w == v:
                    break
            if len(comp) > 1:
                loops.update(comp)
            elif comp[0] in graph.get(comp[0], set()):
                loops.add(comp[0])

    for atom in graph:
        if atom not in indices:
            strongconnect(atom)
    return loops


def satisfies_rule(model: set[str], rule: Rule) -> bool:
    if any(atom in model for atom in rule.head):
        return True
    if any(atom in model for atom in rule.neg):
        return True
    if any(atom not in model for atom in rule.pos):
        return True
    return False


def is_model(program: Program, model: set[str]) -> bool:
    return all(satisfies_rule(model, rule) for rule in program.rules)


def reduct(program: Program, model: set[str]) -> Program:
    rules = [
        Rule(rule.head, rule.pos, ())
        for rule in program.rules
        if not any(atom in model for atom in rule.neg)
    ]
    return Program(rules)


def is_answer_set(program: Program, model: set[str]) -> bool:
    if not is_model(program, model):
        return False
    atoms = sorted(model)
    red = reduct(program, model)
    for mask in range(1 << len(atoms)):
        if mask == (1 << len(atoms)) - 1:
            continue
        sub = {atoms[i] for i in range(len(atoms)) if mask & (1 << i)}
        if is_model(red, sub):
            return False
    return True


def enumerate_answer_sets(program: Program, limit: int | None = None) -> tuple[int, bool]:
    atoms = program.atoms
    count = 0
    complete = True
    for mask in range(1 << len(atoms)):
        model = {atoms[i] for i in range(len(atoms)) if mask & (1 << i)}
        if is_answer_set(program, model):
            count += 1
            if limit is not None and count >= limit:
                complete = False
                break
    return count, complete


def write_program(path: str | Path, rules: Iterable[str]) -> None:
    Path(path).write_text("\n".join(rules) + "\n")
