"""Bounded satisfiability of immutable, same-binding categorical expressions.

Only declared domains and Boolean grammar enter this check: no observations,
task labels, rewards or alternative-action grading. Unknown always permits trial.
`xor` has the formal engine's exactly-one semantics, not parity semantics.
"""
from dataclasses import dataclass
from itertools import product


@dataclass(frozen=True)
class CompatibilityConfig:
    enabled: bool = True
    max_nodes: int = 128
    max_assignments: int = 256
    max_operations: int = 32768
    cache_entries: int = 256

    def __post_init__(self):
        if type(self.enabled) is not bool or any(type(v) is not int or v < 1 for v in
                (self.max_nodes, self.max_assignments, self.max_operations, self.cache_entries)):
            raise ValueError("positive compatibility limits and Boolean enabled required")


@dataclass(frozen=True)
class Verdict:
    status: str
    assignments: int = 0
    operations: int = 0
    reason: str = ""


@dataclass(frozen=True)
class PreparedCheck:
    instructions: tuple
    roots: tuple
    domains: tuple
    assignments: int

    @property
    def signature(self):
        # Versioned, flat encoding avoids recursive Expression hashing. Typed
        # domains distinguish Boolean False/True from integer 0/1.
        return (1, self.instructions, self.roots, self.domains)


def prepare_check(context, candidate, schema, config):
    instructions, roots, domains = [], [], {}
    visited = 0
    for root in (context, candidate):
        stack, results = [(root, False)], []
        while stack:
            expression, expanded = stack.pop()
            if not expanded:
                visited += 1
                if visited > config.max_nodes or len(expression.children) > config.max_nodes:
                    return Verdict("unknown", reason="expression budget")
                if expression.operator in ("read", "true"):
                    if expression.operator == "read":
                        index, expected = expression.atom
                        if index >= len(schema):
                            return Verdict("unknown", reason="undeclared reader")
                        coordinate = schema[index]
                        if len(coordinate.values) > config.max_assignments:
                            return Verdict("unknown", reason="domain budget")
                        try:
                            coordinate.validate(expected)
                        except ValueError:
                            return Verdict("unknown", reason="reader type/domain mismatch")
                        domains[index] = (index, coordinate.name, type(expected).__name__, coordinate.values)
                        instruction = ("read", index, type(expected).__name__, expected)
                    else:
                        instruction = ("true",)
                    instructions.append(instruction)
                    results.append(len(instructions)-1)
                elif expression.operator in ("and", "or", "xor"):
                    if len(stack) + len(expression.children) > 2*config.max_nodes:
                        return Verdict("unknown", reason="expression budget")
                    stack.append((expression, True))
                    stack.extend((child, False) for child in reversed(expression.children))
                else:
                    return Verdict("unknown", reason="unsupported semantics")
            else:
                count = len(expression.children)
                children = tuple(results[-count:])
                del results[-count:]
                instructions.append((expression.operator, children))
                results.append(len(instructions)-1)
        assert len(results) == 1
        roots.append(results[0])
    total = 1
    for _, _, _, values in domains.values():
        total *= len(values)
        if total > config.max_assignments:
            return Verdict("unknown", reason="assignment budget")
    # Bound node visits and their child reductions, not just assignment count.
    cost = sum(1 + (len(i[1]) if i[0] in ("and", "or", "xor") else 0)
               for i in instructions)
    if cost*total > config.max_operations:
        return Verdict("unknown", reason="operation budget")
    return PreparedCheck(tuple(instructions), tuple(roots), tuple(sorted(domains.values())), total)


def solve_prepared(prepared):
    operations = assignments = 0
    for row in product(*(domain[3] for domain in prepared.domains)):
        assignments += 1
        readings = dict(zip((d[0] for d in prepared.domains), row))
        values = []
        for instruction in prepared.instructions:
            operator = instruction[0]
            operations += 1
            if operator == "true":
                value = True
            elif operator == "read":
                value = readings[instruction[1]] == instruction[3]
            else:
                children = [values[i] for i in instruction[1]]
                operations += len(children)
                value = (all(children) if operator == "and" else any(children)
                         if operator == "or" else sum(children) == 1)
            values.append(value)
        if all(values[i] for i in prepared.roots):
            return Verdict("compatible", assignments, operations, "declared-domain witness")
    return Verdict("impossible", assignments, operations, "exhausted declared domains")


def check_compatibility(context, candidate, schema, config=None):
    prepared = prepare_check(context, candidate, schema, config or CompatibilityConfig())
    return prepared if isinstance(prepared, Verdict) else solve_prepared(prepared)
