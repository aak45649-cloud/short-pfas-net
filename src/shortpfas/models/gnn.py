"""Graph neural network encoders for molecular graphs."""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class MessagePassingLayer(nn.Module):
    """A single graph message-passing layer with a simple sum aggregation.

    Updates node features h_i as:
        h_i' = ReLU( W_self * h_i + sum_{j in N(i)} ReLU(W_msg * [h_j || e_ij]) )
    """

    def __init__(self, in_dim: int, out_dim: int, edge_dim: int):
        super().__init__()
        self.self_proj = nn.Linear(in_dim, out_dim)
        self.msg_proj = nn.Linear(in_dim + edge_dim, out_dim)
        self.norm = nn.LayerNorm(out_dim)

    def forward(
        self,
        node_features: torch.Tensor,   # (B, N, in_dim)
        edge_index: torch.Tensor,      # (2, E) with node indices offset per graph
        edge_features: torch.Tensor,   # (E, edge_dim)
        batch: torch.Tensor,           # (B*N,) graph index per node
    ) -> torch.Tensor:
        B, N, feat_dim = node_features.shape
        flat = node_features.reshape(B * N, feat_dim)  # (B*N, F)

        # Build edge feature source/target node features
        src = edge_index[0]
        dst = edge_index[1]

        # concatenate source node feature with edge feature
        src_feat = flat[src]                     # (E, F)
        msg_input = torch.cat([src_feat, edge_features], dim=-1)  # (E, F + edge_dim)
        messages = F.relu(self.msg_proj(msg_input))  # (E, out_dim)

        # scatter-add messages to destination nodes
        aggregated = torch.zeros(B * N, messages.shape[1], device=node_features.device)
        aggregated.index_add_(0, dst, messages)

        updated = self.self_proj(flat) + aggregated
        updated = F.relu(self.norm(updated))
        return updated.reshape(B, N, -1)


class GraphEncoder(nn.Module):
    """Molecular graph encoder (GIN-style with sum aggregation).

    Produces a fixed-size graph embedding by mean + max pooling over nodes.
    """

    def __init__(
        self,
        node_feat_dim: int,
        edge_feat_dim: int,
        hidden_dim: int = 64,
        num_layers: int = 3,
        out_dim: int = 64,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.in_proj = nn.Linear(node_feat_dim, hidden_dim)
        self.layers = nn.ModuleList()
        for _ in range(num_layers):
            self.layers.append(MessagePassingLayer(hidden_dim, hidden_dim, edge_feat_dim))
        self.dropout = nn.Dropout(dropout)
        self.out_proj = nn.Linear(2 * hidden_dim, out_dim)

    def forward(
        self,
        node_features: torch.Tensor,   # (B, N, node_feat_dim)
        edge_index: torch.Tensor,      # (2, E)
        edge_features: torch.Tensor,   # (E, edge_feat_dim)
        batch: torch.Tensor,           # (B*N,)
    ) -> torch.Tensor:
        h = F.relu(self.in_proj(node_features))
        for layer in self.layers:
            h = layer(h, edge_index, edge_features, batch)
            h = self.dropout(h)
        # graph readout: mean + max pooling over nodes (within each graph)
        B = node_features.shape[0]
        h_flat = h.reshape(B * h.shape[1], -1)
        # build per-graph mask via batch indices (assumes contiguous node order)
        # simpler: mean/max over node dim directly (small molecules, padded)
        mask = (node_features.abs().sum(-1) > 0).float().unsqueeze(-1)  # (B, N, 1)
        mean_pool = (h * mask).sum(1) / mask.sum(1).clamp(min=1)
        max_pool = h.masked_fill(mask == 0, -1e9).max(1).values
        graph_emb = torch.cat([mean_pool, max_pool], dim=-1)  # (B, 2*hidden)
        return self.out_proj(graph_emb)  # (B, out_dim)


class GATEncoder(nn.Module):
    """Graph attention encoder (GAT-style) — alternative molecular encoder."""

    def __init__(
        self,
        node_feat_dim: int,
        edge_feat_dim: int,
        hidden_dim: int = 64,
        num_heads: int = 4,
        num_layers: int = 2,
        out_dim: int = 64,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.in_proj = nn.Linear(node_feat_dim, hidden_dim)
        self.attn_layers = nn.ModuleList()
        for _ in range(num_layers):
            self.attn_layers.append(
                nn.MultiheadAttention(
                    hidden_dim, num_heads, dropout=dropout, batch_first=True
                )
            )
        self.out_proj = nn.Linear(hidden_dim, out_dim)

    def forward(
        self,
        node_features: torch.Tensor,
        edge_index: torch.Tensor,
        edge_features: torch.Tensor,
        batch: torch.Tensor,
    ) -> torch.Tensor:
        h = F.relu(self.in_proj(node_features))
        for attn in self.attn_layers:
            h, _ = attn(h, h, h)  # full attention over the (padded) node set
        mask = (node_features.abs().sum(-1) > 0).float().unsqueeze(-1)
        mean_pool = (h * mask).sum(1) / mask.sum(1).clamp(min=1)
        return self.out_proj(mean_pool)
