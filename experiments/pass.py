from qpte import parallelize
from time import perf_counter

def no_op(block):
    return block

if __name__ == "__main__":
    number_of_runs = 2
    for _ in range(number_of_runs):
        start = perf_counter()
        parallelize(
            "audio/input/bell.wav",
            [f"audio/output/bell.wav"],
            no_op
        )
        print(perf_counter() - start)