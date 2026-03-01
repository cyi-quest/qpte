from qpte import parallelize, N_PROC, BLOCK_SIZE
from time import perf_counter

def no_op(block):
    return [block.data]

if __name__ == "__main__":
    number_of_runs = 2
    for _ in range(number_of_runs):
        start = perf_counter()
        parallelize(
            "audio/input/bell.wav",
            [f"audio/output/bell_{N_PROC:>02}_{BLOCK_SIZE:>04}.wav"],
            no_op
        )
        print(perf_counter() - start)
