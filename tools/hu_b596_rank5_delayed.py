"""Verify SB delayed continuation bets with measured NL2 responses pooled over bet sizes."""
from hu_b590_rank3_barrels import main

CASES = {
    "3d8h8s5s": (14598504895, "17f1f9d0c1e6e5bb1301873e4eb76e44e619dd23b5fe4d32d911fdd258020722"),
    "3d6h9sTs": (14626804686, "30aa0d0775724d1d8c53cb1b4539b5980393bf8ccb944681df8b2fce7cb6b9ab"),
    "6s9dJh3c": (14628394918, "2e95b5b63a796934ed2d4e20c73a785d0d14b48b180c9baca47252127171b7b5"),
    "2d7hKs9d": (14593610543, "28f37cefb8d6adb25ed64f2b7d20098d4215fda32054f6a88b672aad0dc627b7"),
    "3d7hAsKd": (14628913050, "b22c76c1e20f29d34096a197d1e50e3a5e03843bfe43554f6bcb02a9890a1aff"),
}


if __name__ == "__main__":
    main(model_id="ln-opfr-t_model-id38uf", rank=5, flop_line="x x", cases=CASES)
