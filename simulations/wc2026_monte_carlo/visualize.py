"""Basic visualization for simulation outputs."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_winner_probabilities(
    winner_df: pd.DataFrame,
    output_path: Path,
    top_n: int = 15,
) -> Path:
    top = winner_df.head(top_n).sort_values("win_probability")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(top["team"], top["win_probability"] * 100, color="#1f4e79")
    ax.set_xlabel("Win Probability (%)")
    ax.set_title("World Cup 2026 Winner Probabilities (Monte Carlo)")
    ax.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def plot_stage_heatmap(stage_df: pd.DataFrame, output_path: Path, top_n: int = 12) -> Path:
    cols = [c for c in stage_df.columns if c.startswith("p_")]
    top = stage_df.head(top_n)
    data = top[cols].values * 100
    labels = [c.replace("p_", "").upper() for c in cols]
    fig, ax = plt.subplots(figsize=(10, 6))
    im = ax.imshow(data, aspect="auto", cmap="Blues")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels)
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(top["team"])
    ax.set_title("Probability of Reaching Each Stage")
    plt.colorbar(im, ax=ax, label="%")
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path