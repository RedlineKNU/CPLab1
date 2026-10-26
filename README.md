# CPLab1 — Паралельний алгоритм решета Ератосфена на PARCS

Лабораторна робота №1 з курсу «Хмарні обчислення», факультет комп'ютерних наук та кібернетики, КНУ ім. Тараса Шевченка.

## Задача

Знайти всі прості числа у діапазоні [2, N] за допомогою:
1. **Послідовного** решета Ератосфена — baseline для порівняння.
2. **Паралельного** segmented sieve — на платформі **PARCS-Python** у хмарному середовищі **Google Cloud**.

Виміряти час для різних N і різної кількості воркерів, оцінити speedup.

## Алгоритм (segmented sieve)

1. **Майстер** знаходить всі прості ≤ √N послідовним решетом (виконується швидко, бо список малий).
2. Діапазон (√N, N] ділиться на **K рівних сегментів** за кількістю воркерів.
3. **Кожен воркер** отримує:
   - свій сегмент [low, high]
   - список малих простих (≤ √N)
4. Воркер викреслює композитні числа у сегменті, використовуючи малі прості, повертає список простих.
5. **Майстер** об'єднує малі прості + результати з усіх воркерів.

## Структура проєкту

```
CPLab1/
├── sieve_serial.py          Послідовне решето (baseline)
├── sieve_parallel.py        Паралельний Solver для PARCS
├── sieve_input.txt          Вхідний файл (значення N)
├── test_parallel_local.py   Локальна перевірка коректності з мок-воркерами
├── benchmark.py             Benchmark через multiprocessing (локальна оцінка)
├── report/                  LaTeX звіт з результатами
└── README.md
```

## Локальна перевірка

```bash
# Серіальний варіант
python3 sieve_serial.py 1000000

# Перевірка коректності паралельного (з мок-воркерами)
python3 test_parallel_local.py 1000000 4

# Benchmark через multiprocessing
python3 benchmark.py --quick
```

## Деплой на Google Cloud

### 1. Передумови

- Акаунт Google Cloud з увімкненим білінгом (безкоштовний tier)
- `gcloud` CLI встановлений і авторизований
- Клонований `PARCS-Python`: https://github.com/Hummer12007/parcs-python

### 2. Створити проєкт і налаштування

```bash
gcloud auth login
gcloud projects create parcs-cplab1-knu
gcloud config set project parcs-cplab1-knu
gcloud config set compute/zone europe-north1-a
gcloud config set compute/region europe-north1
```

### 3. Firewall

```bash
gcloud compute firewall-rules create allow-all \
  --direction=INGRESS --priority=1000 --network=default \
  --action=ALLOW --rules=all --source-ranges=0.0.0.0/0
```

### 4. Створити майстер

```bash
gcloud compute instances create-with-container master \
  --container-image=registry.hub.docker.com/hummer12007/parcs-node \
  --container-env PARCS_ARGS="master"
```

Записати **INTERNAL_IP** майстра (напр. `10.166.0.2`) і **EXTERNAL_IP**.

### 5. Створити воркерів

Для кожного експерименту (K = 1, 2, 4, 8) запускаємо потрібну кількість воркерів:

```bash
# K = 4 воркерів:
gcloud compute instances create-with-container worker1 worker2 worker3 worker4 \
  --container-image=registry.hub.docker.com/hummer12007/parcs-node \
  --container-env PARCS_ARGS="worker 10.166.0.2"
```

### 6. Запуск експерименту

1. Відкрити веб-інтерфейс PARCS: `http://MASTER_EXTERNAL_IP:8080`
2. **Script:** завантажити `sieve_parallel.py`
3. **Input:** завантажити `sieve_input.txt` (одне число N)
4. **Output:** будь-яке ім'я, напр. `output.txt`
5. Натиснути **Run**
6. Фіксувати час виконання з логів майстра

### 7. Прибрати ресурси після експериментів

```bash
gcloud compute instances delete master worker1 worker2 worker3 worker4 --quiet
```

## Таблиця експериментів

Повторити для **N ∈ {10⁷, 10⁸, 10⁹}** і **K ∈ {1, 2, 4, 8}**.

Шаблон таблиці (заповнити після прогону):

| N | K воркерів | Час (с) | Speedup | Efficiency |
|---|---:|---:|---:|---:|
| 10⁷ | 1 (seq) | ? | 1.00 | — |
| 10⁷ | 2 | ? | ? | ? |
| 10⁷ | 4 | ? | ? | ? |
| 10⁷ | 8 | ? | ? | ? |
| ... | | | | |

- **Speedup** = T₁ / Tₖ
- **Efficiency** = Speedup / K

## Корисні посилання

- PARCS-Python: https://github.com/Hummer12007/parcs-python
- Мануал PARCS-Python + Google Cloud: https://mi.csc.knu.ua/wp-content/uploads/2025/09/PARCS-Python_Google_Cloud_0925.pdf
- Методичка курсу: https://mi.csc.knu.ua/wp-content/uploads/2025/09/Task_1_2_Cloud_Computing_0925.pdf
