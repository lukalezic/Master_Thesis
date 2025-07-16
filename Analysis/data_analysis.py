import rdflib
import pandas as pd
import matplotlib.pyplot as plt

countries = ["LUX", "FRA", "DEU"]
colors = ['blue', 'green', 'red']

# Create two subplots: one for relation freq, one for entity degree
fig1, ax1 = plt.subplots(figsize=(10, 6))
fig2, ax2 = plt.subplots(figsize=(10, 6))

for i, country in enumerate(countries):
    print(f"\n=== {country} ===")

    # Load RDF graph
    g = rdflib.Graph()
    g.parse(f"{country}/connected_sections.rdf")

    # Convert to DataFrame
    triples = [(str(s), str(p), str(o)) for s, p, o in g]
    df = pd.DataFrame(triples, columns=["subject", "predicate", "object"])

    total_triples = len(df)
    print("Total triples:", total_triples)
    print("Unique subjects:", df['subject'].nunique())
    print("Unique predicates:", df['predicate'].nunique())
    print("Unique objects:", df['object'].nunique())

    # --- Relation Frequency Plot ---
    relation_counts = df['predicate'].value_counts()
    if not relation_counts.empty:
        ax1.hist(
            relation_counts.values,
            bins=50,
            alpha=0.5,
            label=country,
            color=colors[i],
            density=True
        )

    # --- Entity Degree Plot ---
    entity_counts = pd.concat([df['subject'], df['object']]).value_counts()
    if not entity_counts.empty:
        ax2.hist(
            entity_counts.values,
            bins=50,
            alpha=0.5,
            label=country,
            color=colors[i],
            density=True
        )

    # --- Relation Functionality ---
    func_stats = []
    for r in df["predicate"].unique():
        sub_group = df[df["predicate"] == r].groupby("subject")["object"].nunique()
        obj_group = df[df["predicate"] == r].groupby("object")["subject"].nunique()
        functionality = sub_group.mean()
        inverse_functionality = obj_group.mean()
        func_stats.append((r, functionality, inverse_functionality))

    func_df = pd.DataFrame(func_stats, columns=["predicate", "functionality", "inverse_functionality"])
    func_df.to_csv(f"{country}/functionality_{country}.csv", index=False)

    print(f"\nTop 5 predicates by functionality in {country}:")
    print(func_df.sort_values(by="functionality", ascending=False).head())

# Finalize relation frequency plot
ax1.set_title("Relation Frequency Distribution (Normalized)")
ax1.set_xlabel("Frequency of Relation")
ax1.set_ylabel("Density")
ax1.set_yscale("log")
ax1.legend()
fig1.tight_layout()
fig1.savefig("comparison_relation_frequency_distribution.png")
plt.close(fig1)

# Finalize entity degree plot
ax2.set_title("Entity Degree Distribution (Normalized)")
ax2.set_xlabel("Entity Degree")
ax2.set_ylabel("Density")
ax2.set_yscale("log")
ax2.legend()
fig2.tight_layout()
fig2.savefig("comparison_entity_degree_distribution.png")
plt.close(fig2)

# === Functionality Comparison Plot ===
import os

top_n = 15
shared_preds = set()
func_data = {}

# Load functionality CSVs
for country in countries:
    path = f"{country}/functionality_{country}.csv"
    if os.path.exists(path):
        df = pd.read_csv(path)
        func_data[country] = df
        if not shared_preds:
            shared_preds = set(df["predicate"])
        else:
            shared_preds &= set(df["predicate"])

# Merge and prepare data
combined_df = pd.DataFrame()
for country in countries:
    df = func_data[country]
    df = df[df["predicate"].isin(shared_preds)]
    df["country"] = country
    combined_df = pd.concat([combined_df, df], ignore_index=True)

# Top N predicates by avg. functionality
avg_func = combined_df.groupby("predicate")["functionality"].mean().sort_values(ascending=False).head(top_n).index
plot_df = combined_df[combined_df["predicate"].isin(avg_func)]
plot_df["predicate_short"] = plot_df["predicate"].apply(lambda x: x.split("#")[-1].split("/")[-1])

# Plot
plt.figure(figsize=(12, 6))
for i, country in enumerate(countries):
    subset = plot_df[plot_df["country"] == country]
    plt.bar(
        [x + i*0.25 for x in range(len(subset))],
        subset["functionality"],
        width=0.25,
        label=country,
        color=colors[i]
    )

# X-axis labels
plt.xticks(
    [x + 0.25 for x in range(top_n)],
    plot_df[plot_df["country"] == countries[0]]["predicate_short"],
    rotation=45,
    ha="right"
)

plt.title("Top 15 Shared Predicates by Functionality")
plt.xlabel("Predicate")
plt.ylabel("Functionality (Avg. #objects per subject)")
plt.legend()
plt.tight_layout()
plt.savefig("comparison_functionality.png")
plt.clf()

# === Relation Type Classification + Percentage Plot ===

def classify_relation_type(row):
    f = row["functionality"]
    inv_f = row["inverse_functionality"]
    if f <= 1.2 and inv_f <= 1.2:
        return "1-to-1"
    elif f > 1.2 and inv_f <= 1.2:
        return "1-to-N"
    elif f <= 1.2 and inv_f > 1.2:
        return "N-to-1"
    else:
        return "N-to-N"

for country in countries:
    print(f"\n--- Relation Type Classification for {country} ---")

    path = f"{country}/functionality_{country}.csv"
    if not os.path.exists(path):
        print(f"Skipping {country} — missing functionality CSV.")
        continue

    df = pd.read_csv(path)
    df["relation_type"] = df.apply(classify_relation_type, axis=1)

    # Get value counts and normalize as percentages
    counts = df["relation_type"].value_counts(normalize=True) * 100
    print(counts.round(2).astype(str) + " %")

    # Pie chart (percentage-based)
    plt.figure(figsize=(6, 6))
    counts.plot.pie(autopct='%1.1f%%', startangle=90)
    plt.title(f"Relation Type Distribution in {country}")
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig(f"{country}/relation_type_distribution_pie.png")
    plt.clf()

    # Bar chart (percentage-based)
    plt.figure(figsize=(6, 4))
    counts.sort_index().plot(kind="bar", color="skyblue")
    plt.title(f"Relation Type Distribution in {country}")
    plt.xlabel("Relation Type")
    plt.ylabel("Percentage of Predicates")
    plt.ylim(0, 100)
    plt.tight_layout()
    plt.savefig(f"{country}/relation_type_distribution_bar.png")
    plt.clf()
