# -*- coding: utf-8 -*-
"""Решето Ератосфена (segmented sieve) для PARCS-Python.

Алгоритм (segmented sieve):
  1. Майстер обчислює всі прості до sqrt(N) класичним решетом (мале, швидко).
  2. Діапазон (sqrt(N), N] ділиться на K рівних сегментів між воркерами.
  3. Кожен воркер отримує свій сегмент + список малих простих.
  4. Воркер викреслює композитні у сегменті, повертає ЛИШЕ (count, first10, last10)
     замість повного списку — мінімізує мережеві накладні.
  5. Майстер складає count-и та об'єднує head/tail для фінального output.
"""
from __future__ import print_function
import math

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
        n = self.read_input()
        k = len(self.workers)
        print("N = %d, workers = %d" % (n, k))

        sqrt_n = int(math.isqrt(n)) if hasattr(math, "isqrt") else int(math.sqrt(n))
        small_primes = Solver.small_sieve(sqrt_n)
        print("Малих простих до sqrt(N)=%d: %d" % (sqrt_n, len(small_primes)))

        start = sqrt_n + 1
        total = n - sqrt_n
        chunk = total // k

        mapped = []
        for i in range(k):
            low = start + i * chunk
            high = n if i == k - 1 else start + (i + 1) * chunk - 1
            print("map worker %d: [%d, %d]" % (i, low, high))
            mapped.append(self.workers[i].segment_sieve(low, high, small_primes))

        total_count, first10, last10 = self.myreduce(small_primes, mapped)
        print("Усього простих: %d" % total_count)

        self.write_output(total_count, first10, last10)
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
        """Повертає (count, first10, last10) — компактний результат.

        count — кількість простих у [low, high],
        first10/last10 — перші/останні 10 простих (для фінального head/tail).
        """
        if high < low:
            return [0, [], []]
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
        return [count, first10, last10]

    def myreduce(self, small_primes, mapped):
        """Складає count-и з усіх сегментів + формує глобальні first_10 / last_10."""
        total_count = len(small_primes)
        all_first = list(small_primes[:10])
        all_last_candidates = list(small_primes)

        for chunk in mapped:
            value = chunk
            # Розгортаємо FutureResult: пробуємо індексувати, якщо ні — беремо .value
            for _ in range(5):
                try:
                    _ = value[0]
                    break
                except (TypeError, AttributeError):
                    pass
                if hasattr(value, "value"):
                    value = value.value
                else:
                    break
            c = int(value[0])
            first10 = list(value[1])
            last10 = list(value[2])
            total_count += c
            if len(all_first) < 10:
                all_first.extend(first10)
                all_first = all_first[:10]
            all_last_candidates.extend(last10)

        last10 = all_last_candidates[-10:]
        return total_count, all_first[:10], last10

    def read_input(self):
        with open(self.input_file_name, "r") as f:
            return int(f.readline().strip())

    def write_output(self, count, first10, last10):
        with open(self.output_file_name, "w") as f:
            f.write("count=%d\n" % count)
            f.write("first_10: %s\n" % ", ".join(str(p) for p in first10))
            f.write("last_10:  %s\n" % ", ".join(str(p) for p in last10))
        print("Output written to %s" % self.output_file_name)
