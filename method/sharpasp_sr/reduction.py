from __future__ import annotations

from data.asp import Program, loop_atoms
from .cnf import CNF
from .counter import count_models, projected_count


def _body_lits(cnf: CNF, rule, rename: dict[str, str] | None = None) -> list[int]:
    rename = rename or {}
    lits = [cnf.lit(rename.get(atom, atom), True) for atom in rule.pos]
    lits += [cnf.lit(atom, False) for atom in rule.neg]
    return lits


def add_completion(cnf: CNF, program: Program) -> None:
    atoms = program.atoms
    head_rules = {atom: [] for atom in atoms}
    for rule in program.rules:
        for atom in rule.head:
            head_rules[atom].append(rule)
    for atom in atoms:
        cnf.var(atom)
        if not head_rules[atom]:
            cnf.add_clause([-cnf.var(atom)])
    for rule in program.rules:
        cnf.add_implication(_body_lits(cnf, rule), [cnf.lit(atom) for atom in rule.head])
    for atom, rules in head_rules.items():
        if not rules:
            continue
        support_aux = []
        for rule in rules:
            term_lits = _body_lits(cnf, rule)
            term_lits += [cnf.lit(other, False) for other in rule.head if other != atom]
            aux = cnf.new_aux(f"support_{atom}")
            cnf.add_and_equiv(aux, term_lits)
            support_aux.append(aux)
        cnf.add_implication([cnf.lit(atom)], support_aux)


def add_copy(cnf: CNF, program: Program, loops: set[str], suffix: str) -> dict[str, str]:
    rename = {}
    for atom in loops:
        copy_var = cnf.new_aux(f"copy{suffix}_{atom}")
        rename[atom] = cnf.names[copy_var]
        cnf.add_implication([cnf.lit(rename[atom])], [cnf.lit(atom)])
    for rule in program.rules:
        if not set(rule.head).intersection(loops):
            continue
        antecedent = [cnf.lit(rename.get(atom, atom), True) for atom in rule.pos]
        antecedent += [cnf.lit(atom, False) for atom in rule.neg]
        consequent = [cnf.lit(rename.get(atom, atom), True) for atom in rule.head]
        cnf.add_implication(antecedent, consequent)
    return rename


def build_phi1(program: Program) -> tuple[CNF, list[int], set[str]]:
    cnf = CNF()
    for atom in program.atoms:
        cnf.var(atom)
    add_completion(cnf, program)
    return cnf, [cnf.var(atom) for atom in program.atoms], loop_atoms(program)


def build_phi2(program: Program) -> tuple[CNF, list[int], set[str]]:
    cnf = CNF()
    for atom in program.atoms:
        cnf.var(atom)
    add_completion(cnf, program)
    loops = loop_atoms(program)
    prime = add_copy(cnf, program, loops, "__prime")
    star = add_copy(cnf, program, loops, "__star")
    diff_aux = []
    for atom in loops:
        cnf.add_implication([cnf.lit(prime[atom])], [cnf.lit(star[atom])])
        aux = cnf.new_aux(f"diff_{atom}")
        cnf.add_and_equiv(aux, [cnf.lit(prime[atom], False), cnf.lit(star[atom])])
        diff_aux.append(aux)
    if diff_aux:
        cnf.add_clause(diff_aux)
    else:
        cnf.add_clause([])
    kept_projection_atoms = [cnf.var(atom) for atom in program.atoms]
    return cnf, kept_projection_atoms, loops


def sharpasp_sr_count(program: Program, backend: str = "python") -> dict:
    """|AS(P)| = #phi1 - #exists(CV' u CV*) phi2  (Theorem 1).

    backend="ganak" uses the GANAK exact projected model counter, as in the
    paper's prototype; backend="python" uses the small in-repo counter (only
    usable on tiny programs, kept for self-tests).
    """
    phi1, atoms, loops = build_phi1(program)
    phi2, kept_projection_atoms, _ = build_phi2(program)
    if backend == "ganak":
        from .ganak import ganak_count

        overcount = ganak_count(len(phi1.var_ids), phi1.clauses)
        # Tight programs: Copy(P) is empty and Comp(P) models are exactly the
        # answer sets, so the surplus is 0 (phi2 would contain the empty clause).
        surplus = ganak_count(len(phi2.var_ids), phi2.clauses, kept_projection_atoms) if loops else 0
    else:
        overcount = count_models(phi1.clauses, len(phi1.var_ids))
        # The paper writes #exists X phi2 for X = CV' union CV*, i.e. copies are
        # disregarded. The projection set passed here is the dual: the original
        # atoms whose projected assignments are kept.
        surplus = projected_count(phi2.clauses, kept_projection_atoms)
    return {
        "answer_sets": overcount - surplus,
        "overcount": overcount,
        "surplus": surplus,
        "atoms": len(atoms),
        "loop_atoms": len(loops),
        "core_clauses": len(phi1.clauses),
        "auxiliary_clauses": len(phi2.clauses),
        "phi1_vars": len(phi1.var_ids),
        "phi1_clauses": len(phi1.clauses),
        "phi2_vars": len(phi2.var_ids),
        "phi2_clauses": len(phi2.clauses),
    }
