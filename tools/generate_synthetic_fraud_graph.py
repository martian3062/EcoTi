"""Generate synthetic EcoTi fraud-network data.

Outputs:
  data/synthetic/accounts.csv
  data/synthetic/transactions.csv
  data/synthetic/scam_messages.json
  data/synthetic/graph_summary.json
"""
from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

import networkx as nx
from faker import Faker

DISTRICTS = [
    "Delhi",
    "Mumbai",
    "Bengaluru",
    "Chennai",
    "Hyderabad",
    "Kolkata",
    "Jaipur",
    "Lucknow",
    "Patna",
    "Kochi",
]

SCRIPT_TEMPLATES = [
    "This is CBI. Your Aadhaar is linked to money laundering. This is a digital arrest. Transfer to RBI account now.",
    "Your KYC has expired. Share the OTP immediately or your bank account will be blocked.",
    "Your courier parcel is seized by customs. A case is registered. Join video statement now.",
    "Refund pending. Install support app and enter UPI PIN to receive the amount.",
]


def _upi(fake: Faker, idx: int) -> str:
    name = fake.user_name().replace(".", "")[:12]
    return f"{name}{idx}@upi"


def build_graph(seed: int, accounts: int, mule_clusters: int) -> tuple[nx.DiGraph, list[dict]]:
    rng = random.Random(seed)
    fake = Faker("en_IN")
    Faker.seed(seed)

    graph = nx.DiGraph()
    rows: list[dict] = []
    for idx in range(accounts):
        account_id = _upi(fake, idx)
        is_mule = False
        graph.add_node(
            account_id,
            name=fake.name(),
            phone=fake.msisdn()[:10],
            district=rng.choice(DISTRICTS),
            is_mule=is_mule,
        )

    nodes = list(graph.nodes)
    cluster_size = max(4, accounts // max(1, mule_clusters * 3))
    for cluster in range(mule_clusters):
        center = rng.choice(nodes)
        members = rng.sample(nodes, k=min(cluster_size, len(nodes)))
        for node in members:
            graph.nodes[node]["is_mule"] = True
            amount = rng.randint(1500, 95000)
            graph.add_edge(
                center,
                node,
                amount=amount,
                channel=rng.choice(["UPI", "wallet", "bank_transfer"]),
                minutes_after_contact=rng.randint(2, 240),
                cluster=f"mule_cluster_{cluster + 1}",
            )

    for _ in range(accounts * 2):
        src, dst = rng.sample(nodes, 2)
        if src == dst:
            continue
        graph.add_edge(
            src,
            dst,
            amount=rng.randint(100, 15000),
            channel=rng.choice(["UPI", "wallet"]),
            minutes_after_contact=rng.randint(10, 1440),
            cluster="background",
        )

    for node, attrs in graph.nodes(data=True):
        rows.append({"account_id": node, **attrs})
    return graph, rows


def write_outputs(graph: nx.DiGraph, accounts: list[dict], out_dir: Path, seed: int) -> None:
    rng = random.Random(seed)
    out_dir.mkdir(parents=True, exist_ok=True)

    with (out_dir / "accounts.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["account_id", "name", "phone", "district", "is_mule"],
        )
        writer.writeheader()
        writer.writerows(accounts)

    with (out_dir / "transactions.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "source",
                "target",
                "amount",
                "channel",
                "minutes_after_contact",
                "cluster",
            ],
        )
        writer.writeheader()
        for source, target, attrs in graph.edges(data=True):
            writer.writerow({"source": source, "target": target, **attrs})

    mule_accounts = [row for row in accounts if row["is_mule"]]
    messages = []
    for idx, account in enumerate(rng.sample(mule_accounts, k=min(30, len(mule_accounts)))):
        messages.append(
            {
                "id": f"msg_{idx + 1:03d}",
                "identifier": account["phone"],
                "upi": account["account_id"],
                "district": account["district"],
                "message": rng.choice(SCRIPT_TEMPLATES),
            }
        )
    (out_dir / "scam_messages.json").write_text(json.dumps(messages, indent=2), encoding="utf-8")

    summary = {
        "accounts": graph.number_of_nodes(),
        "transactions": graph.number_of_edges(),
        "mule_accounts": len(mule_accounts),
        "top_risk_districts": sorted(
            (
                {
                    "district": district,
                    "mule_accounts": sum(
                        1 for row in mule_accounts if row["district"] == district
                    ),
                }
                for district in DISTRICTS
            ),
            key=lambda item: item["mule_accounts"],
            reverse=True,
        )[:5],
    }
    (out_dir / "graph_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--accounts", type=int, default=250)
    parser.add_argument("--mule-clusters", type=int, default=8)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--out", default="data/synthetic")
    args = parser.parse_args()

    graph, accounts = build_graph(args.seed, args.accounts, args.mule_clusters)
    write_outputs(graph, accounts, Path(args.out), args.seed)
    print(
        f"Wrote {graph.number_of_nodes()} accounts and {graph.number_of_edges()} "
        f"transactions to {args.out}"
    )


if __name__ == "__main__":
    main()
