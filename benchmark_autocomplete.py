import time
import json
import bisect

class AutocompleteBenchmark:
    def __init__(self, data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Use keys as the completion list
            self.completion_list = sorted(list(data.keys()), key=str.lower)

    def search_linear(self, prefix):
        _hits = []
        prefix_lower = prefix.lower()
        for element in self.completion_list:
            if element.lower().startswith(prefix_lower):
                _hits.append(element)
        return _hits

    def search_optimized(self, prefix):
        if not prefix:
             return self.completion_list[:]

        _hits = []
        prefix_lower = prefix.lower()

        # Binary search to find the insertion point
        start_index = bisect.bisect_left(self.completion_list, prefix_lower, key=str.lower)

        for i in range(start_index, len(self.completion_list)):
            element = self.completion_list[i]
            if element.lower().startswith(prefix_lower):
                _hits.append(element)
            else:
                # Since list is sorted, once we mismatch, we are done
                break
        return _hits

    def benchmark(self, iterations=1000):
        prefixes = ["", "P", "Pi", "Pik", "Ch", "Z", "Mew", "Bulba", "X"]

        print(f"Benchmarking with {iterations} iterations per prefix...")
        print(f"{'Prefix':<10} | {'Linear (sec)':<15} | {'Optimized (sec)':<15} | {'Speedup':<10}")
        print("-" * 60)

        total_linear = 0
        total_opt = 0

        for p in prefixes:
            # Measure Linear
            start = time.perf_counter()
            for _ in range(iterations):
                self.search_linear(p)
            dur_linear = time.perf_counter() - start
            total_linear += dur_linear

            # Measure Optimized
            start = time.perf_counter()
            for _ in range(iterations):
                self.search_optimized(p)
            dur_opt = time.perf_counter() - start
            total_opt += dur_opt

            # Verify correctness
            res_lin = self.search_linear(p)
            res_opt = self.search_optimized(p)
            if res_lin != res_opt:
                print(f"MISMATCH for '{p}'!")
                print("Linear len:", len(res_lin))
                print("Optimized len:", len(res_opt))
                # print("Linear:", res_lin)
                # print("Optimized:", res_opt)
                return

            speedup = dur_linear / dur_opt if dur_opt > 0 else 0
            print(f"{p:<10} | {dur_linear:.6f}        | {dur_opt:.6f}        | {speedup:.2f}x")

        print("-" * 60)
        print(f"Total      | {total_linear:.6f}        | {total_opt:.6f}        | {total_linear/total_opt:.2f}x")

if __name__ == "__main__":
    bm = AutocompleteBenchmark("pokemon_data.json")
    bm.benchmark(iterations=5000)
