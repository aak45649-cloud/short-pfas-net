"""Process-condition encoder (MLP) and the full multi-modal model."""

from __future__ import annotations

from typing import Dict, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F

from .gnn import GATEncoder, GraphEncoder


class ConditionEncoder(nn.Module):
    """MLP encoder for standardized process / water-matrix conditions."""

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 64,
        num_layers: int = 2,
        out_dim: int = 64,
        dropout: float = 0.1,
    ):
        super().__init__()
        layers = [nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Dropout(dropout)]
        for _ in range(num_layers - 1):
            layers += [nn.Linear(hidden_dim, hidden_dim), nn.ReLU(), nn.Dropout(dropout)]
        self.mlp = nn.Sequential(*layers)
        self.out_proj = nn.Linear(hidden_dim, out_dim)

    def forward(self, conditions: torch.Tensor) -> torch.Tensor:
        return self.out_proj(self.mlp(conditions))


class AttentionFusion(nn.Module):
    """Learned attention-weighted fusion of molecular and condition embeddings."""

    def __init__(self, embed_dim: int):
        super().__init__()
        self.query = nn.Linear(embed_dim, embed_dim)
        self.key = nn.Linear(embed_dim, embed_dim)
        self.scale = embed_dim ** -0.5

    def forward(self, mol_emb: torch.Tensor, cond_emb: torch.Tensor) -> torch.Tensor:
        # mol_emb as query, cond_emb as key/value
        q = self.query(mol_emb)
        k = self.key(cond_emb)
        attn = torch.softmax((q * k).sum(-1, keepdim=True) * self.scale, dim=-1)
        return mol_emb + attn * cond_emb  # residual gating


class ShortPFASNet(nn.Module):
    """Multi-modal model for PFAS removal prediction.

    Molecular graph (GNN) + process conditions (MLP) -> attention fusion ->
    prediction head with optional uncertainty (MC Dropout / ensemble).

    Args:
        node_feat_dim: molecular node feature dimension.
        edge_feat_dim: molecular edge feature dimension.
        cond_dim: process-condition feature dimension.
        hidden_dim: shared embedding dimension.
        gnn_type: "gin" (GraphEncoder) or "gat" (GATEncoder).
        dropout: dropout rate (also enables MC Dropout for uncertainty when
            ``dropout > 0`` at inference time).
        num_targets: number of prediction heads (1 = removal only,
            2 = removal + capacity).
    """

    def __init__(
        self,
        node_feat_dim: int,
        edge_feat_dim: int,
        cond_dim: int,
        hidden_dim: int = 64,
        gnn_type: str = "gin",
        dropout: float = 0.1,
        num_targets: int = 1,
    ):
        super().__init__()
        if gnn_type == "gin":
            self.graph_encoder = GraphEncoder(
                node_feat_dim, edge_feat_dim, hidden_dim=hidden_dim,
                out_dim=hidden_dim, dropout=dropout,
            )
        elif gnn_type == "gat":
            self.graph_encoder = GATEncoder(
                node_feat_dim, edge_feat_dim, hidden_dim=hidden_dim,
                out_dim=hidden_dim, dropout=dropout,
            )
        else:
            raise ValueError(f"Unknown gnn_type: {gnn_type}")

        self.cond_encoder = ConditionEncoder(
            cond_dim, hidden_dim=hidden_dim, out_dim=hidden_dim, dropout=dropout
        )
        self.fusion = AttentionFusion(hidden_dim)
        self.head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_targets),
        )

    def forward(
        self,
        node_features: torch.Tensor,
        edge_index: torch.Tensor,
        edge_features: torch.Tensor,
        batch: torch.Tensor,
        conditions: torch.Tensor,
    ) -> torch.Tensor:
        mol_emb = self.graph_encoder(node_features, edge_index, edge_features, batch)
        cond_emb = self.cond_encoder(conditions)
        fused = self.fusion(mol_emb, cond_emb)
        return self.head(fused)  # (B, num_targets)

    def predict_with_uncertainty(
        self,
        node_features: torch.Tensor,
        edge_index: torch.Tensor,
        edge_features: torch.Tensor,
        batch: torch.Tensor,
        conditions: torch.Tensor,
        n_samples: int = 30,
    ) -> Dict[str, torch.Tensor]:
        """MC Dropout uncertainty: run forward pass n_samples times.

        Returns mean prediction and predictive standard deviation.
        Requires the model to be in ``train()`` mode so dropout is active.
        """
        self.train()
        preds = []
        with torch.no_grad():
            for _ in range(n_samples):
                preds.append(
                    self.forward(node_features, edge_index, edge_features, batch, conditions)
                )
        stack = torch.stack(preds, dim=0)  # (n_samples, B, num_targets)
        mean = stack.mean(0)
        std = stack.std(0)
        return {"mean": mean, "std": std}
