#!/usr/bin/env python3
"""Deterministic pseudo-random number generation.

Every stochastic decision in this repository is drawn from a `PRNG` seeded by a
*string* naming the exact decision site (arm, seed, generation, episode, step).
This has one purpose: **matched counterfactuals**.

Two experimental arms that differ only in which genome fields they may modify
must, when they take the same action in the same state at the same step, consume
the *same* random number. Seeding by site-name rather than by a shared mutable
stream guarantees this without any coordination between arms, and makes seed
asymmetry between arms structurally impossible rather than merely intended.

Adapted from the deterministic-seed discipline in `verified-code-rsi`; the
xorshift64* core is a standard published generator.
"""
from __future__ import annotations

import hashlib
import math
from typing import List, Sequence, TypeVar

T = TypeVar("T")

_MASK = (1 << 64) - 1


def seed_of(site: str) -> int:
    """Map a decision-site name to a 64-bit seed. Stable across processes and
    Python versions (unlike `hash()`)."""
    h = hashlib.sha256(site.encode("utf-8")).digest()
    s = int.from_bytes(h[:8], "big") & _MASK
    return s or 0x9E3779B97F4A7C15


class PRNG:
    """xorshift64* — deterministic, fast, no external state."""

    __slots__ = ("_s", "site")

    def __init__(self, site: str):
        self.site = site
        self._s = seed_of(site)

    def next_u64(self) -> int:
        s = self._s
        s ^= (s >> 12) & _MASK
        s = (s ^ (s << 25)) & _MASK
        s ^= (s >> 27) & _MASK
        self._s = s
        return (s * 0x2545F4914F6CDD1D) & _MASK

    def unit(self) -> float:
        """Uniform in [0, 1)."""
        return (self.next_u64() >> 11) * (1.0 / (1 << 53))

    def below(self, n: int) -> int:
        """Uniform integer in [0, n)."""
        if n <= 1:
            return 0
        return self.next_u64() % n

    def choice(self, xs: Sequence[T]) -> T:
        return xs[self.below(len(xs))]

    def shuffled(self, xs: Sequence[T]) -> List[T]:
        out = list(xs)
        for i in range(len(out) - 1, 0, -1):
            j = self.below(i + 1)
            out[i], out[j] = out[j], out[i]
        return out

    def categorical(self, logits: Sequence[float]) -> int:
        """Sample an index from a softmax over `logits`.

        `-inf` logits (used by the masking form of the authority term) are
        assigned exactly zero probability, which is the property Proposition 1
        in CONCEPTUAL_FRAMEWORK.md depends on.
        """
        m = max(logits)
        if m == float("-inf"):
            return 0
        exps = [0.0 if x == float("-inf") else math.exp(x - m) for x in logits]
        tot = sum(exps)
        r = self.unit() * tot
        acc = 0.0
        for i, e in enumerate(exps):
            acc += e
            if r <= acc:
                return i
        for i in range(len(exps) - 1, -1, -1):
            if exps[i] > 0.0:
                return i
        return 0
