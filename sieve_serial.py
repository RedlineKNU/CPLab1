"""Послідовне решето Ератосфена (baseline для benchmark).

Використання:
    python3 sieve_serial.py <N>

Виводить: кількість простих до N та час виконання (с).
"""
from __future__ import print_function
import sys
import time


def sieve_of_eratosthenes(n):
    """Класичне решето Ератосфена, O(n log log n), O(n) пам'яті.

    Повертає список простих чисел у [2, n].
    """
    if n < 2:
        return []
    is_prime = bytearray([1]) * (n + 1)
    is_prime[0] = is_prime[1] = 0
    p = 2
    while p * p <= n:
        if is_prime[p]:
            # Викреслюємо з p*p (менші кратні вже викреслено меншими простими)
            for multiple in range(p * p, n + 1, p):
                is_prime[multiple] = 0
        p += 1
    return [i for i in range(2, n + 1) if is_prime[i]]


def main():
    if len(sys.argv) < 2:
        print("Використання: python3 sieve_serial.py <N>")
        sys.exit(1)
    n = int(sys.argv[1])
    t0 = time.perf_counter()
    primes = sieve_of_eratosthenes(n)
    elapsed = time.perf_counter() - t0
    print("N = %d" % n)
    print("Знайдено простих: %d" % len(primes))
    print("Останні 5: %s" % primes[-5:])
    print("Час: %.4f с" % elapsed)


if __name__ == "__main__":
    main()
