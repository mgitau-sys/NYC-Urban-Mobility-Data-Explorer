"""Run: python tests/test_algorithms.py"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from algorithms import top_k 
random.seed(1)
for n, k in [(0, 5), (3, 5), (10, 10), (1000, 7), (5000, 50)]:
    rows = [{"trips": random.randint(1, 500)} for _ in range(n)]
    got = [r["trips"] for r in tops_k(rows, k, lambda r: r["trips"])]
    want = sorted((r["trips"] for r in rows), reverse=True)[:k]
    assert got == want, (n, k)
print("top_k matches sorted() on all cases")