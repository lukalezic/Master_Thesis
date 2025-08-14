#!/usr/bin/env python3
"""
Batch process: compute degree bins (low, medium, high) from RDF triples in every subdirectory.
Each subdir must contain one `.rdf` file. The script saves degree bins in that same subdir.
"""

from pathlib import Path
from typing import List, Tuple, Dict
from collections import Counter
import random
import math
import sys

try:
    from rdflib import Graph, URIRef, Literal
except ImportError as e:
    raise SystemExit("Please install rdflib: pip install rdflib") from e

Triple = Tuple[str, str, str]


def load_triples_from_rdf(path: Path) -> List[Triple]:
    g = Graph()
    g.parse(str(path))  # auto-detects format
    return [(str(s), str(p), str(o)) for s, p, o in g]


def train_test_split(triples: List[Triple], test_ratio=0.2, seed=42) -> Tuple[List[Triple], List[Triple]]:
    rng = random.Random(seed)
    shuffled = triples[:]
    rng.shuffle(shuffled)
    n_test = int(len(shuffled) * test_ratio)
    return shuffled[n_test:], shuffled[:n_test]  # train, test


def compute_entity_degrees(triples: List[Triple]) -> Dict[str, int]:
    deg = Counter()
    for h, _, t in triples:
        deg[h] += 1
        deg[t] += 1
    return dict(deg)


def make_degree_bins(degrees: Dict[str, int], triples: List[Triple]) -> Dict[str, int]:
    if not degrees:
        return {}

    values = sorted(degrees.values())
    ents = list(degrees.keys())
    total_triples = len(triples)

    def q(p):
        idx = min(len(values) - 1, max(0, int(math.ceil(p * (len(values) - 1)))))
        return values[idx]

    best_b1 = 0.85
    best_b2 = 0.95
    best_diff = float("inf")
    best_bins = {}

    for b1_p in [x / 1000 for x in range(940, 980, 1)]:  # 90.0% to 96.9%
        for b2_p in [x / 1000 for x in range(int(b1_p * 1000) + 10, 995, 1)]:  # b2 > b1
            b1 = q(b1_p)
            b2 = q(b2_p)
            bins = {}
            for e in ents:
                d = degrees[e]
                if d <= b1:
                    bins[e] = 0
                elif d <= b2:
                    bins[e] = 1
                else:
                    bins[e] = 2

            # Count how many triples each bin "owns"
            bin_triple_counts = {0: 0, 1: 0, 2: 0}
            for h, _, t in triples:
                bin_h = bins.get(h)
                bin_t = bins.get(t)
                if bin_t is not None and bin_h is not None:
                    if bin_t == bin_h:
                        bin_triple_counts[bin_h] += 1
                    else:
                        if random.random() < 0.5:
                            bin_triple_counts[bin_t] += 1
                        else:
                            bin_triple_counts[bin_h] += 1

            counts = list(bin_triple_counts.values())
            diff = max(counts) - min(counts)            
            if diff < best_diff:
                print(counts)  
                best_diff = diff
                best_b1 = b1
                best_b2 = b2
                best_bins = bins

    print(f"  Selected thresholds -> b1: {best_b1}, b2: {best_b2}")

    return best_bins


def save_bins(groups: Dict[int, set], output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    labels = ["low", "medium", "high"]
    for i, label in enumerate(labels):
        path = output_dir / f"{label}_degree.txt"
        with path.open("w", encoding="utf-8") as f:
            for ent in sorted(groups[i]):
                f.write(ent + "\n")
        print(f"  Saved {len(groups[i])} {label} degree entities to {path}")


def process_directory(dir_path: Path):
    rdf_files = list(dir_path.glob("*.rdf"))
    if not rdf_files:
        print(f"⚠️  Skipping {dir_path} (no .rdf file found)")
        return
    if len(rdf_files) > 1:
        print(f"⚠️  Skipping {dir_path} (more than one .rdf file found)")
        return

    rdf_path = rdf_files[0]
    print(f"\n📂 Processing {rdf_path}")

    try:
        triples = load_triples_from_rdf(rdf_path)
        print(f"  Loaded {len(triples)} triples")
    except Exception as e:
        print(f"  ❌ Failed to parse RDF: {e}")
        return

    train_triples, _ = train_test_split(triples, test_ratio=0.2, seed=42)
    print(f"  Train set size: {len(train_triples)} triples")

    degrees = compute_entity_degrees(train_triples)
    print(f"  Computed degrees for {len(degrees)} entities")

    ent2bin = make_degree_bins(degrees, train_triples)

    groups = {0: set(), 1: set(), 2: set()}
    for ent, bin_id in ent2bin.items():
        groups[bin_id].add(ent)

    save_bins(groups, dir_path)


def main():
    base_dir = Path(".").resolve()

    print(f"🔍 Scanning folders in: {base_dir}")
    subdirs = [p for p in base_dir.iterdir() if p.is_dir()]
    if not subdirs:
        print("❌ No subdirectories found.")
        sys.exit(1)

    for subdir in subdirs:
        if subdir.__str__()[-3:] in ["FRA", "DEU", "LUX"]:
            process_directory(subdir)


if __name__ == "__main__":
    main()
