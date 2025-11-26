"""
Legacy shim that exposes the MUTS security helpers for compatibility.
"""

from muts.security.seed_key import MazdaECUType, MazdaSeedKeyDatabase, bypass_security

__all__ = ["MazdaECUType", "MazdaSeedKeyDatabase", "bypass_security"]
