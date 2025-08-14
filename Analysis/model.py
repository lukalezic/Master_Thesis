import rdflib
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from pykeen.triples import TriplesFactory
from pykeen.pipeline import pipeline
from pykeen.evaluation import RankBasedEvaluator

folders = ["DEU", "LUX", "FRA"]
models = ["TransE", "DistMult", "ComplEX", "ConvE"]
degree_labels = ["low", "medium", "high"]
x_labels = ["Skip low degree", "Skip medium degree", "Skip high degree"]

# Store results: results[model][country][degree] = MRR
results = {model: {country: {} for country in folders} for model in models}

for country in folders:
    folder = Path(country)
    print(f"\n=== Processing {country} ===")

    # === Load RDF triples ===
    rdf_files = list(folder.glob("*.rdf"))
    if not rdf_files:
        print(f"⚠️  No RDF file found in {country}")
        continue
    g = rdflib.Graph()
    g.parse(str(rdf_files[0]), format="xml")
    triples = [(str(s), str(p), str(o)) for s, p, o in g]

    # === Load degree bins ===
    bins = {}
    for i, label in enumerate(degree_labels):
        path = folder / f"{label}_degree.txt"
        bins[i] = set(open(path, encoding="utf-8").read().splitlines())

    # === Create full triples factory ===
    tf = TriplesFactory.from_labeled_triples(
        triples=np.array(triples, dtype=str),
        create_inverse_triples=True,
    )

    # === Split once for training, validation, testing ===
    training, validation, testing = tf.split([0.8, 0.1, 0.1], method="coverage")

    for model_name in models:
        print(f"\nTraining model {model_name} for {country} ...")

        result = pipeline(
            model=model_name,
            training=training,
            validation=validation,
            testing=testing,
            model_kwargs={"embedding_dim": 100},
            training_kwargs={"num_epochs": 500, "batch_size": 1024},
            optimizer="Adam",
            optimizer_kwargs={"lr": 1e-3, "weight_decay": 1e-5},
            negative_sampler_kwargs={"filtered": True},
            evaluator_kwargs={"batch_size": 16, "filtered": True},
            stopper="early",
            stopper_kwargs={"frequency": 10, "patience": 2, "metric": "mrr"},
            device="cuda",
        )

        model = result.model

        for bin_to_skip in [2, 1, 0]:  # high, medium, low
            label = degree_labels[bin_to_skip]
            skip_entities = bins[bin_to_skip]

            filtered_test_triples = [
                (h, r, t) for h, r, t in testing.triples
                if h not in skip_entities and t not in skip_entities
            ]

            if not filtered_test_triples:
                print(f"  No test triples left after skipping {label}-degree nodes")
                results[model_name][country][label] = None
                continue

            test_factory = TriplesFactory.from_labeled_triples(
                triples=np.array(filtered_test_triples, dtype=str),
                entity_to_id=training.entity_to_id,
                relation_to_id=training.relation_to_id,
            )

            evaluator = RankBasedEvaluator(filtered=True)
            eval_results = evaluator.evaluate(
                model=model,
                mapped_triples=test_factory.mapped_triples,
                additional_filter_triples=[
                    training.mapped_triples,
                    validation.mapped_triples
                ],
            )

            mrr = eval_results.get_metric("mean_reciprocal_rank")
            results[model_name][country][label] = mrr

            print(f"  [Skip {label}] MRR: {mrr:.4f}")

# === Plotting results ===
print("\n📊 Plotting results (MRR)...")

for model_name in models:
    fig, ax = plt.subplots()

    for country in folders:
        y_vals = []
        for label in ["low", "medium", "high"]:
            val = results[model_name][country].get(label)
            y_vals.append(val if val is not None else 0.0)

        ax.plot(x_labels, y_vals, marker='o', label=country)

    ax.set_title(f"{model_name} - MRR by Skipped Degree Group")
    ax.set_ylabel("MRR")
    ax.set_xlabel("Skipped Degree Group in Test Set")
    ax.legend(title="Country")
    ax.grid(True)
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(f"{model_name}_degree_bias_mrr.png")
    print(f"Saved plot: {model_name}_degree_bias_mrr.png")
    plt.close()
