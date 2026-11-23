"""Solve SB's half-pot turn barrel against observed three-bet-pot responses."""
from hu_b590_rank3_barrels import main

CASES = {
    "3d8h8s5s": (14593107489, "f10f5b64a733529c6219c243975ffa6d64758d70fd99ba9a7da63be541b6f5e5"),
    "3d7hAsJh": (14528582176, "174b88e1fd55c9e29f7473a35650dd4d6d7bb2225a84f920870bbbc4874b17d6"),
    "2d7hKs9d": (14593123141, "a4f8ce62f6b0589e988939a4c6b020e2fba7d7d3dc7dd4c494d3583883e0fad5"),
}

if __name__ == "__main__":
    main(model_id="ln-3bp-3b_t_model-1gg0bw", rank=19, flop_line="b75 c", cases=CASES,
         schema="NL2_HU_B628_3BP_TURN_BARREL_RESPONSES_V1")
