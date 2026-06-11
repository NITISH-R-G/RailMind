import asyncio
import time
from backend.agents.nodes import detect_node

async def run_benchmark():
    # Mock state
    num_trains = 10000
    raw_data = []
    processed_trains = []

    for i in range(num_trains):
        raw_data.append({
            "train_number": f"T{i}",
            "train_name": f"Train {i}",
            "delay_minutes": 20,
            "passenger_load": "normal"
        })
        if i % 2 == 0:
            processed_trains.append(f"T{i}")

    state = {
        "raw_train_data": raw_data,
        "processed_trains": processed_trains
    }

    # Run a few times to warmup
    for _ in range(3):
        await detect_node(state.copy())

    start_time = time.perf_counter()
    iterations = 10
    for _ in range(iterations):
        await detect_node(state.copy())
    end_time = time.perf_counter()

    avg_time = (end_time - start_time) / iterations
    print(f"Average time per call: {avg_time:.4f} seconds")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
