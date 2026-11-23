"""Verify measured BB double- and triple-barrel responses following a half-pot SB flop bet."""
from hu_b590_rank3_barrels import main

CASES = {
    "2d7hKs9d": (14593610543, "28f37cefb8d6adb25ed64f2b7d20098d4215fda32054f6a88b672aad0dc627b7"),
    "3d7hAsKd": (14628913050, "b22c76c1e20f29d34096a197d1e50e3a5e03843bfe43554f6bcb02a9890a1aff"),
    "2d9hAsKd": (14598935222, "b1a8e88fd871a2e0e9f8f43f068ed5187df9fc51511a09de93bd663bac2fca8d"),
}


if __name__ == "__main__":
    main(model_id="ln-opfr-t_model-trdt3w", rank=4, flop_line="b50 c", cases=CASES)
