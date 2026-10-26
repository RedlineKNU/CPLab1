"""Паралельне решето Ератосфена (segmented sieve) для PARCS-Python.

Запуск у PARCS через веб-інтерфейс майстра (http://MASTER_IP:8080):
  - Script: цей файл
  - Input: sieve_input.txt (містить одне число — N)
  - Output: будь-який

Алгоритм (segmented sieve):
  1. Майстер обчислює всі прості до sqrt(N) класичним решетом (мале, швидко).
  2. Діапазон (sqrt(N), N] ділиться на K рівних сегментів між воркерами.
  3. Кожен воркер отримує свій сегмент + список малих простих.
  4. Воркер викреслює композитні у сегменті, повертає список знайдених простих.
  5. Майстер об'єднує: малі прості + усі сегментні.
"""
from __future__ import print_function
import math

try:
    from Pyro4 import expose
except ImportError:
    # Локальний режим без PARCS/Pyro4 — @expose стає noop.
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

        # 1. Малі прості до sqrt(N) — послідовно на майстрі (швидко).
        sqrt_n = int(math.isqrt(n)) if hasattr(math, "isqrt") else int(math.sqrt(n))
        small_primes = Solver.small_sieve(sqrt_n)
        print("Малих простих до sqrt(N)=%d: %d" % (sqrt_n, len(small_primes)))

        # 2. Поділ діапазону (sqrt_n, N] на K сегментів.
        start = sqrt_n + 1
        total = n - sqrt_n
        chunk = total // k

        mapped = []
        for i in range(k):
            low = start + i * chunk
            high = n if i == k - 1 else start + (i + 1) * chunk - 1
            print("map worker %d: [%d, %d]" % (i, low, high))
            mapped.append(self.workers[i].segment_sieve(low, high, small_primes))

        # 3. Збір результатів.
        all_primes = self.myreduce(small_primes, mapped)
        print("Усього простих: %d" % len(all_primes))

        self.write_output(all_primes)
        print("Job finished")

    @staticmethod
    @expose
    def small_sieve(limit):
        """Класичне решето для чисел [2, limit]. Виконується на майстрі."""
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
        """Викреслює композитні в [low, high] за допомогою малих простих.

        Повертає список простих у сегменті.
        """
        if high < low:
            return []
        size = high - low + 1
        is_prime = bytearray([1]) * size
        for p in small_primes:
            # Перше кратне p у [low, high]: ceil(low/p)*p, але не менше p*p
            start = max(p * p, ((low + p - 1) // p) * p)
            for m in range(start, high + 1, p):
                is_prime[m - low] = 0
        return [low + i for i in range(size) if is_prime[i]]

    def myreduce(self, small_primes, mapped):
        """Об'єднує малі прості + результати з усіх воркерів."""
        result = list(small_primes)
        for chunk in mapped:
            # У PARCS Pyro4 результат — Future, його треба .value
            value = chunk.value if hasattr(chunk, "value") else chunk
            result.extend(value)
        return result

    def read_input(self):
        with open(self.input_file_name, "r") as f:
            return int(f.readline().strip())

    def write_output(self, primes):
        with open(self.output_file_name, "w") as f:
            f.write("count=%d\n" % len(primes))
            # Записуємо лише перші 10 і останні 10 (економимо місце)
            if len(primes) <= 20:
                f.write("primes: %s\n" % ", ".join(str(p) for p in primes))
            else:
                head = ", ".join(str(p) for p in primes[:10])
                tail = ", ".join(str(p) for p in primes[-10:])
                f.write("first_10: %s\n" % head)
                f.write("last_10:  %s\n" % tail)
        print("Output written to %s" % self.output_file_name)
