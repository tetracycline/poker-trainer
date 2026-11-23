"""Re-solve CO's turn bet versus measured BB replies after a limped flop stab."""
import argparse

from hu_b590_rank3_barrels import main

SOURCES = {
    46: ("ln-iso-lmp_t_model-17z0wyl", "x b50 c", {
        "3d8h8s5s": (14600026283, "7583287177315c74022553f0b64dc91d39c95a9dee0f84329dd99b22564c273e"),
        "2d7h7s3s": (14721557248, "a9c69fec0313802717caaf2f046632020e9b523d67f88aa373a09c6d627cb809"),
    }),
    47: ("ln-iso-lmp_t_model-1oaypnl", "x b33 c", {
        "4dQhKsTc": (14601426559, "144919b63c7609d4256109db43d81f60004bad04a1bb7398759d238edc70f454"),
        "3d8h8s5s": (14600026283, "7583287177315c74022553f0b64dc91d39c95a9dee0f84329dd99b22564c273e"),
        "3d6h9sTs": (14599037935, "f6d4d734bcb9d35f9c779e5b0d9853b23217bb1b44ef17b73ef35f4ef2fb0c11"),
    }),
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--rank", type=int, choices=SOURCES, required=True)
    args, remaining = parser.parse_known_args()
    model, line, cases = SOURCES[args.rank]
    main(model_id=model, rank=args.rank, flop_line=line, cases=cases, argv=remaining,
         schema="NL2_HU_B638_LIMPED_TURN_RESPONSES_V1")
