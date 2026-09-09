import asyncio
from aiohttp import web

# 1. Orders Service (Port 8081 - Healthy Microservice)
async def handle_orders(request):
    return web.json_response({
        "service": "orders-microservice",
        "status": "PROCESSED",
        "orderId": "ORD-98214",
        "items": ["Cell-Pack-A", "Inverter-Module"],
        "totalAmount": 1420.50
    })

# 2. Payments Service (Port 8082 - Simulates Hard Downstream Outage / Crash)
async def handle_payments_faulty(request):
    # Sever the socket abruptly to trigger transport failure (PrematureCloseException)
    if request.transport:
        request.transport.close()
    return web.Response()

# 3. AWS LocalStack / CloudWatch Metric Sink (Port 4566)
async def handle_aws_cloudwatch(request):
    data = await request.text()
    return web.json_response({"status": "AWS_METRICS_INGESTED", "bytes": len(data)})

async def main():
    # App 1: Orders (:8081)
    app_orders = web.Application()
    app_orders.router.add_get('/api/v1/orders', handle_orders)
    app_orders.router.add_post('/api/v1/orders', handle_orders)
    runner_orders = web.AppRunner(app_orders)
    await runner_orders.setup()
    site_orders = web.TCPSite(runner_orders, 'localhost', 8081)
    await site_orders.start()

    # App 2: Faulty Payments (:8082)
    app_payments = web.Application()
    app_payments.router.add_get('/api/v1/payments', handle_payments_faulty)
    runner_payments = web.AppRunner(app_payments)
    await runner_payments.setup()
    site_payments = web.TCPSite(runner_payments, 'localhost', 8082)
    await site_payments.start()

    # App 3: AWS CloudWatch Sink (:4566)
    app_aws = web.Application()
    app_aws.router.add_post('/metrics', handle_aws_cloudwatch)
    runner_aws = web.AppRunner(app_aws)
    await runner_aws.setup()
    site_aws = web.TCPSite(runner_aws, 'localhost', 4566)
    await site_aws.start()

    print("✓ Upstream Mock Cluster Online:")
    print("  • Orders Service:     http://localhost:8081/api/v1/orders (Healthy)")
    print("  • Payments Service:   http://localhost:8082/api/v1/payments (Crash Simulation)")
    print("  • AWS Telemetry Sink: http://localhost:4566/metrics (Cloud Simulator)")

    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
