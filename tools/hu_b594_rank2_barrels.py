"""Verify measured BB responses across all rank 2 certified full-pot SB flop barrels."""
from hu_b590_rank3_barrels import main

CASES = {
    "4dQhKsTc": (14630030655, "5ad798c2d3516b289acc7b23edb634293b632c150ddbbc2997912198dc498bac"),
    "3d6h9sTs": (14626804686, "30aa0d0775724d1d8c53cb1b4539b5980393bf8ccb944681df8b2fce7cb6b9ab"),
    "2d9hAsKd": (14598935222, "b1a8e88fd871a2e0e9f8f43f068ed5187df9fc51511a09de93bd663bac2fca8d"),
}


if __name__ == "__main__":
    main(model_id="ln-opfr-t_model-19esov6", rank=2, flop_line="b100 c", cases=CASES)
