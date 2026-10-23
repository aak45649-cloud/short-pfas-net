"""SMILES -> molecular graph construction using RDKit.

Converts a PFAS SMILES string into an undirected molecular graph with atom
features (atomic number, degree, formal charge, etc.) and bond features,
ready for consumption by a graph neural network.

If RDKit is not installed, calling :func:`smiles_to_graph` raises a clear
ImportError instead of failing silently.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np


class RDKitError(ImportError):
    pass


def _rdkit():
    try:
        from rdkit import Chem  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover
        raise RDKitError(
            "RDKit is required for molecular graph construction. "
            "Install it with: pip install rdkit"
        ) from exc
    return Chem


# Atom feature dimension: 16 (element one-hot) + 6 (degree) + 1 (formal charge)
# + 1 (num H) + 1 (aromatic) + 6 (hybridization) = 31
ATOM_FEATURE_DIM = 31


def _atom_features(atom) -> List[float]:
    """Return a fixed-length feature vector for a single RDKit atom."""
    feats = []
    # atomic number (categorical, bucket common elements)
    atomic_num = atom.GetAtomicNum()
    one_hot = [0.0] * 16
    for idx, elem in enumerate([1, 6, 7, 8, 9, 15, 16, 17, 35, 53]):
        if atomic_num == elem:
            one_hot[idx] = 1.0
            break
    feats.extend(one_hot)
    # degree
    deg = [0.0] * 6
    deg[min(atom.GetDegree(), 5)] = 1.0
    feats.extend(deg)
    # formal charge (bucketed)
    fc = atom.GetFormalCharge()
    feats.append(float(fc))
    # number of hydrogens
    feats.append(float(atom.GetTotalNumHs()))
    # aromaticity
    feats.append(float(atom.GetIsAromatic()))
    # hybridization (one-hot, 6 buckets)
    hyb = atom.GetHybridization()
    hyb_idx = int(hyb) if int(hyb) < 6 else 5
    hyb_one_hot = [0.0] * 6
    hyb_one_hot[hyb_idx] = 1.0
    feats.extend(hyb_one_hot)
    return feats


def _bond_features(bond) -> List[float]:
    """Return a fixed-length feature vector for a single RDKit bond."""
    bt = bond.GetBondType()
    type_map = {
        "SINGLE": 0,
        "DOUBLE": 1,
        "TRIPLE": 2,
        "AROMATIC": 3,
    }
    one_hot = [0.0] * 4
    key = str(bt)
    if key in type_map:
        one_hot[type_map[key]] = 1.0
    feats = list(one_hot)
    feats.append(float(bond.GetIsConjugated()))
    feats.append(float(bond.IsInRing()))
    return feats


def smiles_to_graph(
    smiles: str,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Convert a SMILES string into graph tensors.

    Returns
    -------
    node_features : np.ndarray, shape (n_atoms, ATOM_FEATURE_DIM)
    edge_index : np.ndarray, shape (2, n_edges), undirected
    edge_features : np.ndarray, shape (n_edges, n_bond_features)
    adjacency : np.ndarray, shape (n_atoms, n_atoms), 0/1 adjacency matrix
    """
    Chem = _rdkit()
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles!r}")

    node_features: List[List[float]] = []
    for atom in mol.GetAtoms():
        node_features.append(_atom_features(atom))
    node_features = np.asarray(node_features, dtype=np.float32)

    edge_index: List[List[int]] = []
    edge_features: List[List[float]] = []
    for bond in mol.GetBonds():
        i = bond.GetBeginAtomIdx()
        j = bond.GetEndAtomIdx()
        ef = _bond_features(bond)
        edge_index.append([i, j])
        edge_index.append([j, i])  # undirected
        edge_features.append(ef)
        edge_features.append(ef)

    if edge_index:
        edge_index = np.asarray(edge_index, dtype=np.int64).T  # (2, n_edges)
        edge_features = np.asarray(edge_features, dtype=np.float32)
    else:
        edge_index = np.empty((2, 0), dtype=np.int64)
        edge_features = np.empty((0, 6), dtype=np.float32)

    n_atoms = node_features.shape[0]
    adjacency = np.zeros((n_atoms, n_atoms), dtype=np.float32)
    if edge_index.shape[1] > 0:
        adjacency[edge_index[0], edge_index[1]] = 1.0

    return node_features, edge_index, edge_features, adjacency
