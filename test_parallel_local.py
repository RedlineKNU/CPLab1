"""Локальний тест sieve_parallel.py з мок-воркерами (без PARCS-кластера).

Імітує K воркерів викликаючи segment_sieve напряму.
Для перевірки коректності й швидкого debug'у перед деплоєм.

Використання:
    python3 test_parallel_local.py <N> <K>
    python3 test_parallel_local.py 1000000 4
"""
from __future__ import print_function
import sys
import time
from sieve_parallel import Solver
from sieve_serial import sieve_of_eratosthenes


class MockFuture(object):
    """Імітує Pyro4 Future — просто обгортає значення."""
    def __init__(self, value):
        self.value = value


class MockWorker(object):
    """Мок-воркер: викликає Solver.segment_sieve синхронно."""
    def segment_sieve(self, low, high, small_primes):
        return MockFuture(Solver.segment_sieve(low, high, small_primes))


def main():
    if len(sys.argv) < 3:
        print("Використання: python3 test_parallel_local.py <N> <K>")
        sys.exit(1)
    n = int(sys.argv[1])
    k = int(sys.argv[2])

    # Записуємо вхід
    with open("sieve_input.txt", "w") as f:
        f.write("%d\n" % n)

    workers = [MockWorker() for _ in range(k)]
    solver = Solver(workers=workers,
                    input_file_name="sieve_input.txt",
                    output_file_name="sieve_output.txt")
    t0 = time.perf_counter()
    solver.solve()
    parallel_time = time.perf_counter() - t0

    # Перевірка коректності проти серіального
    t0 = time.perf_counter()
    serial = sieve_of_eratosthenes(n)
    serial_time = time.perf_counter() - t0

    with open("sieve_output.txt") as f:
        head = f.readline().strip()
        parallel_count = int(head.split("=")[1])

    print("\n=== Порівняння ===")
    print("Серіальний:     %d простих, %.4f с" % (len(serial), serial_time))
    print("Паралельний(мок): %d простих, %.4f с" % (parallel_count, parallel_time))
    print("Коректність: %s" % ("✓ OK" if len(serial) == parallel_count else "✗ FAIL"))


if __name__ == "__main__":
    main()
