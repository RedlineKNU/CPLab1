"""Локальний benchmark: послідовне vs паралельне решето Ератосфена.

Запускає обидва варіанти для різних N та кількостей воркерів,
виводить таблицю з часом і speedup.

Використання:
    python3 benchmark.py                    # дефолтні сітки
    python3 benchmark.py --n 10000000       # заданий N
    python3 benchmark.py --quick            # швидкий прогін для перевірки

Для фінального звіту ті самі заміри потрібно повторити на PARCS-кластері
(значення в таблиці будуть іншими — тут multiprocessing, там Pyro4 RPC).
"""
from __future__ import print_function
import argparse
import time
from multiprocessing import Pool

from sieve_serial import sieve_of_eratosthenes
from sieve_parallel import Solver


DEFAULT_N_VALUES = [10_000_000, 50_000_000, 100_000_000]
DEFAULT_K_VALUES = [1, 2, 4, 8]


def _segment_sieve_task(args):
    low, high, small_primes = args
    return Solver.segment_sieve(low, high, small_primes)


def parallel_sieve(n, k, pool):
    """Паралельний segmented sieve через multiprocessing.Pool."""
    sqrt_n = int(n ** 0.5)
    small = Solver.small_sieve(sqrt_n)

    start = sqrt_n + 1
    total = n - sqrt_n
    chunk = total // k
    tasks = []
    for i in range(k):
        low = start + i * chunk
        high = n if i == k - 1 else start + (i + 1) * chunk - 1
        tasks.append((low, high, small))

    results = pool.map(_segment_sieve_task, tasks)
    primes = list(small)
    for r in results:
        primes.extend(r)
    return primes


def run_benchmark(n_values, k_values):
    print("\n" + "=" * 72)
    print("Benchmark: Решето Ератосфена — послідовне vs паралельне")
    print("=" * 72)
    print("Платформа: локальна (multiprocessing). На PARCS-кластері цифри будуть іншими.\n")

    for n in n_values:
        print("─" * 72)
        print("N = %s" % f"{n:,}".replace(",", " "))
        print("─" * 72)

        # Baseline — серіальний
        t0 = time.perf_counter()
        serial = sieve_of_eratosthenes(n)
        t_serial = time.perf_counter() - t0
        print("  Серіальний:               %d простих, %.3f с" % (len(serial), t_serial))

        print("  %-12s %-12s %-12s %-10s" % ("Воркерів", "Час (с)", "Speedup", "Коректно"))
        for k in k_values:
            with Pool(k) as pool:
                t0 = time.perf_counter()
                parallel = parallel_sieve(n, k, pool)
                t_par = time.perf_counter() - t0
            speedup = t_serial / t_par
            ok = "✓" if len(parallel) == len(serial) else "✗"
            print("  %-12d %-12.3f %-12.2f %-10s" % (k, t_par, speedup, ok))
        print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, nargs="+", default=None, help="значення N")
    parser.add_argument("--k", type=int, nargs="+", default=None, help="кількості воркерів")
    parser.add_argument("--quick", action="store_true", help="швидкий прогін (менші N)")
    args = parser.parse_args()

    n_values = args.n or (DEFAULT_N_VALUES if not args.quick else [1_000_000, 5_000_000])
    k_values = args.k or DEFAULT_K_VALUES
    run_benchmark(n_values, k_values)


if __name__ == "__main__":
    main()
