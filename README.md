# Counting Answer Sets of Disjunctive Answer Set Programs

<!-- scope-note -->
> [!NOTE]
> **Not a full reproduction of the paper.** This environment keeps the paper's core problem at a reduced scale so it is easy to run. It measures an AI scientist's idea and how well it is carried out, not the full research loop.

| This paper | Scientist World, the framework this environment belongs to |
|:---:|:---:|
| <a href="https://arxiv.org/abs/2507.11655"><img alt="This paper on arXiv" src="https://img.shields.io/badge/arXiv-2507.11655-b31b1b?logo=arxiv&logoColor=white"></a> | <a href="https://arxiv.org/abs/2611.08478"><img alt="Scientist World on arXiv" src="https://img.shields.io/badge/arXiv-2611.08478-b31b1b?logo=arxiv&logoColor=white"></a> <a href="https://github.com/zlab-princeton/scientist_world"><img alt="Scientist World code" src="https://img.shields.io/badge/Code-Scientist_World-181717?logo=github&logoColor=white"></a> <a href="https://github.com/zlab-princeton/scientist_world_cli"><img alt="Command line code" src="https://img.shields.io/badge/Code-Command_line-181717?logo=github&logoColor=white"></a> |

| **Paper ID** | [2507.11655](https://arxiv.org/abs/2507.11655) |
|:---|:---|
| **Domain** | Knowledge Representation / Answer Set Programming / Exact Counting |
| **TL;DR** | The paper counts answer sets of disjunctive ASP programs exactly by subtracting projected-counted non-answer-set completion models from a completion-model overcount. |

## Summary

The paper targets exact answer-set counting for non-tight disjunctive ASP programs, a setting where enumeration and counters for normal programs do not scale well. It defines a loop-atom copy construction that identifies surplus Clark-completion models that are not stable models. The resulting sharpASP-sR counter reduces the problem to projected model counting and outperforms clingo, Wasp, and DynASP on the paper's benchmark suite.

## Problem

Count the number of answer sets of a finite ground disjunctive Answer Set Programming (ASP) program exactly. The challenge is to handle non-tight programs where stable-model minimality matters and where plain answer-set enumeration becomes infeasible when the number of answer sets is large.

## The paper's method

The paper introduces sharpASP-sR, an exact counter for disjunctive ASP programs based on a subtractive reduction to projected propositional model counting.

## Key results of the paper

- On 1125 benchmark instances, sharpASP-sR solves 825 instances versus 708 for clingo, 432 for Wasp, and 89 for DynASP.
- The hybrid clingo plus sharpASP-sR approach solves 918 instances with PAR2 1600.
- The paper reports sharpASP-sR counting instances up to roughly `2^127` answer sets, while enumeration systems time out at much lower counts.

## Leaderboard

FNI of AI scientists on this paper, grader-verified. 0 matches the paper's method, higher is better.

| Model | Innovate |
|---|---:|
| `gpt-5.5-xhigh` | +103.0 |
| `gpt-5.6-sol-xhigh` | +24.4 |
| `gpt-5.6-terra-xhigh` | +24.4 |
| `gpt-5.6-luna-xhigh` | -13.1 |

`innovate`: the model designs its own method. `improve`: it starts from the paper's method.

## Run it

```bash
pip install sciworld
sw research 2507.11655 --mode innovate --agent claude-code
sw evaluate 2507.11655
```

## More

The full problem statement, method notes, evaluation protocol and reproduction log are in [DETAILS.md](DETAILS.md).

