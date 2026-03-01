import json
import glob

data = []

for filepath in glob.glob("data/pass-cpus_*-block_size_*"):
    with open(filepath) as f:
        lines = f.readlines()
        
    cpus, block_size = map(int, lines[0].split())
    times = [float(line.strip()) for line in lines[1:] if line.strip()]
    
    data.append({
        "cpus": cpus,
        "block_size": block_size,
        "times": times
    })

with open("qpte_scaling.json", "w") as f:
    json.dump(data, f, indent=2)

print(f"Processed {len(data)} configurations")
