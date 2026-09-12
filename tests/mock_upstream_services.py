import asyncio
import json

# 1. Orders Service (Port 8081 - Healthy Microservice)
async def handle_orders_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        # Read HTTP request header
        while True:
            line = await reader.readline()
            if not line or line == b"\r\n" or line == b"\n":
                break

        body = json.dumps({
            "service": "orders-microservice",
            "status": "PROCESSED",
            "orderId": "ORD-98214",
            "items": ["Cell-Pack-A", "Inverter-Module"],
            "totalAmount": 1420.50
        }).encode("utf-8")

        response = (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: application/json\r\n"
            b"Content-Length: " + str(len(body)).encode("ascii") + b"\r\n"
            b"Connection: close\r\n\r\n" + body
        )
        writer.write(response)
        await writer.drain()
    except Exception:
        pass
    finally:
        writer.close()
        await writer.wait_closed()

# 2. Payments Service (Port 8082 - Simulates Hard Downstream Outage / Crash)
async def handle_payments_faulty_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    # Sever the socket abruptly to trigger transport failure (PrematureCloseException)
    writer.close()
    await writer.wait_closed()

# 3. AWS LocalStack / CloudWatch Metric Sink (Port 4566)
async def handle_aws_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        content_length = 0
        while True:
            line = await reader.readline()
            if not line or line == b"\r\n" or line == b"\n":
                break
            if line.lower().startswith(b"content-length:"):
                content_length = int(line.split(b":")[1].strip())

        if content_length > 0:
            await reader.readexactly(content_length)

        body = json.dumps({"status": "AWS_METRICS_INGESTED", "bytes": content_length}).encode("utf-8")
        response = (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: application/json\r\n"
            b"Content-Length: " + str(len(body)).encode("ascii") + b"\r\n"
            b"Connection: close\r\n\r\n" + body
        )
        writer.write(response)
        await writer.drain()
    except Exception:
        pass
    finally:
        writer.close()
        await writer.wait_closed()

async def main():
    server_orders = await asyncio.start_server(handle_orders_client, None, 8081)
    server_payments = await asyncio.start_server(handle_payments_faulty_client, None, 8082)
    server_aws = await asyncio.start_server(handle_aws_client, None, 4566)

    print("✓ Upstream Mock Cluster Online:")
    print("  • Orders Service:     http://localhost:8081/api/v1/orders (Healthy)")
    print("  • Payments Service:   http://localhost:8082/api/v1/payments (Crash Simulation)")
    print("  • AWS Telemetry Sink: http://localhost:4566/metrics (Cloud Simulator)")

    async with server_orders, server_payments, server_aws:
        await asyncio.gather(
            server_orders.serve_forever(),
            server_payments.serve_forever(),
            server_aws.serve_forever()
        )

if __name__ == "__main__":
    asyncio.run(main())
