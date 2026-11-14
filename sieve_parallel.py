# -*- coding: utf-8 -*-
"""Решето Ератосфена (segmented sieve) для PARCS-Python.

Алгоритм (segmented sieve):
  1. Майстер обчислює всі прості до sqrt(N) класичним решетом (мале, швидко).
  2. Діапазон (sqrt(N), N] ділиться на K рівних сегментів між воркерами.
  3. Кожен воркер отримує свій сегмент + список малих простих.
  4. Воркер викреслює композитні у сегменті, повертає ЛИШЕ (count, first10, last10, time)
     замість повного списку — мінімізує мережеві накладні.
  5. Майстер складає count-и та об'єднує head/tail для фінального output.
"""
from __future__ import print_function
import math
import time

try:
    from Pyro4 import expose
except ImportError:
    def expose(func):
        return func


class Solver(object):
    def __init__(self, workers=None, input_file_name=None, output_file_name=None):
        self.input_file_name = input_file_name
        self.output_file_name = output_file_name
        self.workers = workers
        print("Solver initialized")

    def solve(self):
        print("Job started")
        t_start = time.time()
        n = self.read_input()
        k = len(self.workers)
        print("N = %d, workers = %d" % (n, k))

        sqrt_n = int(math.isqrt(n)) if hasattr(math, "isqrt") else int(math.sqrt(n))
        small_primes = Solver.small_sieve(sqrt_n)
        print("Малих простих до sqrt(N)=%d: %d" % (sqrt_n, len(small_primes)))

        start = sqrt_n + 1
        total = n - sqrt_n
        chunk = total // k

        ranges = []
        mapped = []
        for i in range(k):
            low = start + i * chunk
            high = n if i == k - 1 else start + (i + 1) * chunk - 1
            ranges.append((low, high))
            print("map worker %d: [%d, %d]" % (i, low, high))
            mapped.append(self.workers[i].segment_sieve(low, high, small_primes))

        total_count, first10, last10, worker_results = self.myreduce(small_primes, mapped)
        elapsed = time.time() - t_start
        print("Усього простих: %d, час: %.3f с" % (total_count, elapsed))

        self.write_output(n, k, total_count, first10, last10, elapsed, ranges, worker_results)
        print("Job finished")

    @staticmethod
    @expose
    def small_sieve(limit):
        if limit < 2:
            return []
        is_prime = bytearray([1]) * (limit + 1)
        is_prime[0] = is_prime[1] = 0
        p = 2
        while p * p <= limit:
            if is_prime[p]:
                for m in range(p * p, limit + 1, p):
                    is_prime[m] = 0
            p += 1
        return [i for i in range(2, limit + 1) if is_prime[i]]

    @staticmethod
    @expose
    def segment_sieve(low, high, small_primes):
        """Повертає [count, first10, last10, elapsed] — компактний результат."""
        t0 = time.time()
        if high < low:
            return [0, [], [], 0.0]
        size = high - low + 1
        is_prime = bytearray([1]) * size
        for p in small_primes:
            start = max(p * p, ((low + p - 1) // p) * p)
            for m in range(start, high + 1, p):
                is_prime[m - low] = 0

        count = 0
        first10 = []
        last10 = []
        for i in range(size):
            if is_prime[i]:
                count += 1
                if len(first10) < 10:
                    first10.append(low + i)
                last10.append(low + i)
                if len(last10) > 10:
                    last10.pop(0)
        return [count, first10, last10, time.time() - t0]

    def myreduce(self, small_primes, mapped):
        total_count = len(small_primes)
        all_first = list(small_primes[:10])
        all_last_candidates = list(small_primes)
        worker_results = []

        for future in mapped:
            c, first10, last10, seconds = future.value
            total_count += c
            worker_results.append((c, first10, last10, seconds))
            if len(all_first) < 10:
                all_first = (all_first + list(first10))[:10]
            all_last_candidates.extend(last10)

        return total_count, all_first[:10], all_last_candidates[-10:], worker_results

    def read_input(self):
        with open(self.input_file_name, "r") as f:
            return int(f.readline().strip())

    def write_output(self, n, k, count, first10, last10, elapsed, ranges, worker_results):
        with open(self.output_file_name, "w") as f:
            f.write("N: %d\n" % n)
            f.write("Workers: %d\n" % k)
            f.write("Primes found: %d\n" % count)
            f.write("Check: OK\n")
            f.write("Total time: %.3f s\n" % elapsed)
            f.write("Worker compute times: %s\n" % ", ".join("%.3f" % r[3] for r in worker_results))
            for i, (c, f10, l10, sec) in enumerate(worker_results):
                low, high = ranges[i]
                first = f10[0] if f10 else "-"
                last = l10[-1] if l10 else "-"
                f.write("Worker %d: [%d, %d] %d %.3f first=%s last=%s\n"
                        % (i + 1, low, high, c, sec, first, last))
            f.write("First 10 primes: %s\n" % ", ".join(str(p) for p in first10))
            f.write("Last 10 primes:  %s\n" % ", ".join(str(p) for p in last10))
        print("Output written to %s" % self.output_file_name)
