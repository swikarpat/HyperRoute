import asyncio
import time
import random
import statistics
import httpx
from typing import List, Dict

import os

TARGET_URL = os.getenv("TARGET_URL", "http://localhost:8000/api/v1/agent/evaluate")
CONCURRENCY_LEVEL = int(os.getenv("CONCURRENCY", "50"))
TOTAL_REQUESTS = int(os.getenv("TOTAL_REQUESTS", "1000"))

COUNTRIES = ["US", "SG", "GB", "CH", "DE", "HK", "AE", "JP"]

def generate_payload() -> dict:
    """Generates synthetic high-throughput financial transactions."""
    is_anomaly = random.random() < 0.25
    sender = random.choice(COUNTRIES)
    receiver = random.choice(COUNTRIES) if is_anomaly else sender
    amount = round(random.uniform(1_500_000, 10_000_000), 2) if is_anomaly else round(random.uniform(500, 50_000), 2)

    return {
        "account_id": f"ACC-CORP-{random.randint(1000, 9999)}",
        "amount_usd": amount,
        "sender_country": sender,
        "receiver_country": receiver,
        "narrative": "Liquidity cross-border rebalancing" if is_anomaly else "Standard vendor settlement"
    }

async def send_worker(
    worker_id: int,
    queue: asyncio.Queue,
    client: httpx.AsyncClient,
    latencies_ms: List[float],
    status_counts: Dict[str, int]
):
    while not queue.empty():
        try:
            _ = await queue.get()
            payload = generate_payload()
            start_t = time.perf_counter()

            response = await client.post(TARGET_URL, json=payload, timeout=5.0)
            elapsed_ms = (time.perf_counter() - start_t) * 1000.0

            latencies_ms.append(elapsed_ms)
            code_key = str(response.status_code)
            status_counts[code_key] = status_counts.get(code_key, 0) + 1

        except httpx.RequestError as e:
            status_counts["CONNECTION_ERROR"] = status_counts.get("CONNECTION_ERROR", 0) + 1
        finally:
            queue.task_done()

async def run_load_test():
    print(f"\n=======================================================")
    print(f"  HyperRoute Enterprise Synthetic Load Test Harness   ")
    print(f"=======================================================")
    print(f" Target Endpoint:   {TARGET_URL}")
    print(f" Concurrency Level: {CONCURRENCY_LEVEL} workers")
    print(f" Total Requests:    {TOTAL_REQUESTS} transactions")
    print(f" Status:            Dispatching load pipeline...\n")

    queue = asyncio.Queue()
    for i in range(TOTAL_REQUESTS):
        await queue.put(i)

    latencies_ms: List[float] = []
    status_counts: Dict[str, int] = {}

    limits = httpx.Limits(max_connections=CONCURRENCY_LEVEL + 10, max_keepalive_connections=CONCURRENCY_LEVEL)
    
    start_total_time = time.perf_counter()

    async with httpx.AsyncClient(limits=limits) as client:
        workers = [
            asyncio.create_task(send_worker(w, queue, client, latencies_ms, status_counts))
            for w in range(CONCURRENCY_LEVEL)
        ]
        await queue.join()
        for w in workers:
            w.cancel()

    total_duration_s = time.perf_counter() - start_total_time
    total_successful = sum(count for code, count in status_counts.items() if code == "200")
    rps = len(latencies_ms) / total_duration_s if total_duration_s > 0 else 0

    latencies_ms.sort()
    p50 = statistics.median(latencies_ms) if latencies_ms else 0.0
    p90 = latencies_ms[int(len(latencies_ms) * 0.90)] if latencies_ms else 0.0
    p95 = latencies_ms[int(len(latencies_ms) * 0.95)] if latencies_ms else 0.0
    p99 = latencies_ms[int(len(latencies_ms) * 0.99)] if latencies_ms else 0.0
    max_lat = max(latencies_ms) if latencies_ms else 0.0
    min_lat = min(latencies_ms) if latencies_ms else 0.0

    print("-------------------------------------------------------")
    print(" Execution Telemetry Summary")
    print("-------------------------------------------------------")
    print(f" Total Wall Time:        {total_duration_s:.3f} s")
    print(f" Effective Throughput:   {rps:.2f} req/s")
    print(f" Successful (HTTP 200):  {total_successful}/{TOTAL_REQUESTS}")
    print(f" HTTP Status Breakdown:  {dict(status_counts)}")
    print("\n Latency Percentiles (End-to-End Client Roundtrip):")
    print(f"  • Min:    {min_lat:.2f} ms")
    print(f"  • P50:    {p50:.2f} ms")
    print(f"  • P90:    {p90:.2f} ms")
    print(f"  • P95:    {p95:.2f} ms")
    print(f"  • P99:    {p99:.2f} ms")
    print(f"  • Max:    {max_lat:.2f} ms")
    print("-------------------------------------------------------\n")

if __name__ == "__main__":
    asyncio.run(run_load_test())
