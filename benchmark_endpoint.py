#!/usr/bin/env python3
"""
Simple benchmark script to measure response time of /v1/webhooks/transactions endpoint.

Usage:
    python benchmark_endpoint.py [--url URL] [--requests N]
"""
import argparse
import time
import statistics
from datetime import datetime
import httpx


def benchmark_transaction_endpoint(base_url: str, num_requests: int = 10):
    """Benchmark the transaction webhook endpoint."""

    endpoint = f"{base_url}/v1/webhooks/transactions"

    print(f"Benchmarking: {endpoint}")
    print(f"Number of requests: {num_requests}")
    print("-" * 60)

    response_times = []
    successful_requests = 0
    failed_requests = 0

    for i in range(num_requests):
        # Create unique transaction data for each request
        transaction_data = {
            "transaction_id": f"TXN-{datetime.now().timestamp()}-{i}",
            "source_account": "ACC-SOURCE-001",
            "destination_account": "ACC-DEST-002",
            "amount": 100.50,
            "currency": "USD"
        }

        start_time = time.perf_counter()

        try:
            response = httpx.post(
                endpoint,
                json=transaction_data,
                timeout=30.0
            )

            end_time = time.perf_counter()
            elapsed_time = (end_time - start_time) * 1000  # Convert to milliseconds

            response_times.append(elapsed_time)

            if response.status_code == 202:
                successful_requests += 1
                status_symbol = "✓"
            else:
                failed_requests += 1
                status_symbol = "✗"

            print(f"Request {i+1:3d}: {status_symbol} {elapsed_time:8.2f}ms | Status: {response.status_code}")

        except Exception as e:
            end_time = time.perf_counter()
            elapsed_time = (end_time - start_time) * 1000
            failed_requests += 1
            print(f"Request {i+1:3d}: ✗ {elapsed_time:8.2f}ms | Error: {str(e)[:50]}")

        # Small delay between requests to avoid overwhelming the server
        time.sleep(0.1)

    # Calculate statistics
    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)

    if response_times:
        print(f"Total Requests:    {num_requests}")
        print(f"Successful:        {successful_requests}")
        print(f"Failed:            {failed_requests}")
        print(f"\nResponse Time Statistics (ms):")
        print(f"  Min:             {min(response_times):8.2f}ms")
        print(f"  Max:             {max(response_times):8.2f}ms")
        print(f"  Mean:            {statistics.mean(response_times):8.2f}ms")
        print(f"  Median:          {statistics.median(response_times):8.2f}ms")

        if len(response_times) > 1:
            print(f"  Std Dev:         {statistics.stdev(response_times):8.2f}ms")

        # Calculate percentiles
        sorted_times = sorted(response_times)
        p50 = sorted_times[len(sorted_times) // 2]
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)]

        print(f"\nPercentiles:")
        print(f"  50th (p50):      {p50:8.2f}ms")
        print(f"  95th (p95):      {p95:8.2f}ms")
        print(f"  99th (p99):      {p99:8.2f}ms")

        # Throughput
        total_time = sum(response_times) / 1000  # Convert to seconds
        throughput = num_requests / total_time if total_time > 0 else 0
        print(f"\nThroughput:        {throughput:.2f} requests/second")
    else:
        print("No successful requests to analyze.")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark the transaction webhook endpoint"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the API (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=10,
        help="Number of requests to send (default: 10)"
    )

    args = parser.parse_args()

    try:
        benchmark_transaction_endpoint(args.url, args.requests)
    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted by user.")
    except Exception as e:
        print(f"\nError running benchmark: {e}")
        raise


if __name__ == "__main__":
    main()
