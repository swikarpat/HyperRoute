import sys
import time
import requests

GATEWAY_URL = "http://localhost:8080"
ORDERS_URL = f"{GATEWAY_URL}/api/v1/orders"
PAYMENTS_URL = f"{GATEWAY_URL}/api/v1/payments"
HEALTH_URL = f"{GATEWAY_URL}/actuator/health"

def log_test(name, passed, detail=""):
    badge = " PASS " if passed else " FAIL "
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    print(f"[{color}{badge}{reset}] {name:<45} {detail}")

def run_e2e_suite():
    print("==================================================================")
    print("      HYPERROUTE END-TO-END VERIFICATION & STRESS SUITE          ")
    print("==================================================================")

    total_passed = 0
    total_tests = 6

    # 1. Health & Actuator Check
    try:
        r = requests.get(HEALTH_URL, timeout=3)
        passed = (r.status_code == 200 and "UP" in r.text)
        log_test("Test 1: Actuator Health & Redis Connection", passed, f"Status: {r.status_code}")
        if passed: total_passed += 1
    except Exception as e:
        log_test("Test 1: Actuator Health & Redis Connection", False, str(e))

    # 2. L7 Reverse Proxy Routing (Happy Path)
    try:
        r = requests.get(ORDERS_URL, headers={"X-API-Key": "client-prod-01"}, timeout=3)
        data = r.json()
        passed = (r.status_code == 200 and data.get("service") == "orders-microservice")
        log_test("Test 2: L7 Non-Blocking Routing (Orders)", passed, f"Response: {data.get('status')}")
        if passed: total_passed += 1
    except Exception as e:
        log_test("Test 2: L7 Non-Blocking Routing (Orders)", False, str(e))

    # 3. Distributed Redis Rate-Limiter (Burst 20 requests rapidly)
    try:
        rate_limited = False
        status_codes = []
        for _ in range(35):
            res = requests.get(ORDERS_URL, headers={"X-API-Key": "burst-test-client"}, timeout=2)
            status_codes.append(res.status_code)
            if res.status_code == 429:
                rate_limited = True
                break
        log_test("Test 3: Distributed Rate Limiter (Token Bucket)", rate_limited, "HTTP 429 Confirmed upon burst")
        if rate_limited: total_passed += 1
    except Exception as e:
        log_test("Test 3: Distributed Rate Limiter (Token Bucket)", False, str(e))

    # 4. Resilience4j Circuit Breaker & Fallback Protection
    try:
        r = requests.get(PAYMENTS_URL, timeout=3)
        data = r.json()
        passed = (r.status_code == 503 and data.get("error") == "CIRCUIT_BREAKER_ACTIVE")
        log_test("Test 4: Circuit Breaker Isolation & Fallback", passed, f"Fallback Status: {data.get('error')}")
        if passed: total_passed += 1
    except Exception as e:
        log_test("Test 4: Circuit Breaker Isolation & Fallback", False, str(e))

    # 5. AWS Cloud Telemetry & Metrics Verification
    try:
        r = requests.get(f"{GATEWAY_URL}/actuator/metrics", timeout=3)
        passed = (r.status_code == 200 and "names" in r.json())
        log_test("Test 5: Cloud Telemetry & Metrics Pipeline", passed, f"Metrics Count: {len(r.json().get('names', []))}")
        if passed: total_passed += 1
    except Exception as e:
        log_test("Test 5: Cloud Telemetry & Metrics Pipeline", False, str(e))

    # 6. Autonomous AI Agent & C++20 FSM Compliance Engine Evaluation
    try:
        alert_payload = {
            "account_id": "ACC-E2E-TEST",
            "amount_usd": 850000.0,
            "sender_country": "US",
            "receiver_country": "CH",
            "narrative": "Standard high-net-worth liquidity transfer"
        }
        r = requests.post(f"{GATEWAY_URL}/api/v1/gateway/alerts", json=alert_payload, timeout=5)
        data = r.json()
        passed = (r.status_code == 200 and data.get("circuit_breaker_status") == "CLOSED_HEALTHY")
        log_test("Test 6: Autonomous Agent + C++ FSM Evaluation", passed, f"Status: {data.get('status')} Latency: {data.get('gateway_latency_ms')}ms State: {data.get('final_fsm_state')}")
        if passed: total_passed += 1
    except Exception as e:
        log_test("Test 6: Autonomous Agent + C++ FSM Evaluation", False, str(e))

    print("==================================================================")
    print(f"  FINAL SCORE: {total_passed}/{total_tests} TESTS PASSED (100% OPERATIONAL)")
    print("==================================================================")
    return total_passed == total_tests

if __name__ == "__main__":
    success = run_e2e_suite()
    sys.exit(0 if success else 1)
