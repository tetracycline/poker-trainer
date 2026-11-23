"""Measure cutoff replies against UTG barrels on the three certified rank 30 flops."""
from hu_b590_rank3_barrels import main

CASES = {
    "4dQhKsTc": (14703138852, "6e2a963e65f65bac7cd7eae1985dcb230fe7d37625eb318cfeadf06f1f6b24cb"),
    "4d9hJsTs": (14703697349, "d4c382a1ede76563d60810b50742481c27424d6e605396b53c1c66de79d6eaed"),
    "4dJhQs7s": (14706190808, "18e28d53d3511b0467aed8f0c43625758bfebd0997c4f3d47822c63ef187ed76"),
}


if __name__ == "__main__":
    main(model_id="ln-opfr-t_model-1hmsxaw", rank=30, flop_line="b50 c", cases=CASES)
