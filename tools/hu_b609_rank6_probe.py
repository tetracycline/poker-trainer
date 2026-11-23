"""Compare BB probes with measured IP preflop-raiser responses after a checked flop."""
from hu_b590_rank3_barrels import main

CASES = {
    "3d8h8s5s": (14592317474, "e9f9b205d1ba876c0e713e0a62344865fc99adb87b8188e0c62dfa99b645ffdd"),
    "2s7sKs9d": (14531225991, "c68b5f8ccb94788a6ba82b2e4ba475fa702e96634a1778996894dc8de70c5b1d"),
    "3d6h9sTs": (14530176503, "4a6a1cf475b97aec2e60d20d2ad3f36ba64d2bf5fada736cdc65fd375da8c252"),
    "4d9hJsTs": (14591863023, "3e938b4911d61697da9e1fe458f61153b56fa2da32ecd38f3b675f9a1a9b57c7"),
    "4dQhKsTc": (14591903053, "a91926766c28752b494da69e09d90ea001e7665c50643f15265faf152fbc9898"),
}


if __name__ == "__main__":
    main(model_id="ln-bb-t_model-1n6d5u3", rank=6, flop_line="x x", cases=CASES,
         schema="NL2_HU_B609_BB_PROBE_RESPONSES_V1")
