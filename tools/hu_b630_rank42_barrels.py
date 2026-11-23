"""Solve BB turn barrels against measured size-matched three-bet-pot replies."""
from hu_b590_rank3_barrels import main

CASES = {
    "3d8h8s5s": (14592962403, "41ee16871985ecfcfbd4153ef3335e074b331fc85a54ebd5e9f78b1a85874f55"),
    "3d6h9sTs": (14532355569, "35e8c8b23589824b6fd738e29ce0418ea73bcecc962a5f410f952567e8879933"),
    "3dThKsTc": (14528716811, "133a5c64dfd671021da53556aa2e27800b2676545a2bf310a8001f5447c5072d"),
    "4d9hJsTs": (14592627989, "ce21cd35fbc9954630ac64800f14ebc1c3b667df6326081eb7d3017dfebf2e3e"),
    "4d8hAs8d": (14528551179, "fd980bcfd2418d4876fb68afdf5c442b11096ee397b00adec34fc9a878b228ac"),
}

if __name__ == "__main__":
    main(model_id="ln-3bp-3b_t_model-1fvksvd", rank=42, flop_line="b75 c", cases=CASES,
         schema="NL2_HU_B628_3BP_TURN_BARREL_RESPONSES_V1")
