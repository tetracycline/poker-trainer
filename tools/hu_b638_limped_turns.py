"""Reproduce BB turn choices against the measured limped-pot reply distribution."""
import argparse

from hu_b590_rank3_barrels import main

SOURCES = {
    1: ("ln-iso-lmp_t_model-19hfq8v", "b50 c", {
        "2d4h4s8s": (14643520614, "72edc1b5a75c1a81f89f85efb5daffcdf24b5b1cec45ff4428a5c105caeaab65"),
        "2s4h6dKh": (14646892297, "54f16c00656c2235f13bf219e76d2c8635fb9591eaaf11e6ac9c977bee656023"),
        "3d5h7s6c": (14648360341, "aa1a858743cc1904a7f92a7cb2c4d4102e9faf760bdd4fbd89d482268ad27897"),
        "3d8h8s5s": (14643774933, "a8ab800f0289e0ffeacf7aaf823ff12abbab372cfa732af29f113a7123b04d65"),
    }),
    7: ("ln-iso-lmp_t_model-1e9jvm0", "x x", {
        "3d8h8s5s": (14600026283, "7583287177315c74022553f0b64dc91d39c95a9dee0f84329dd99b22564c273e"),
        "3d6h9sTs": (14599037935, "f6d4d734bcb9d35f9c779e5b0d9853b23217bb1b44ef17b73ef35f4ef2fb0c11"),
        "4dQhKsTc": (14601426559, "144919b63c7609d4256109db43d81f60004bad04a1bb7398759d238edc70f454"),
    }),
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--rank", type=int, choices=SOURCES, required=True)
    args, remaining = parser.parse_known_args()
    model_id, line, cases = SOURCES[args.rank]
    main(model_id=model_id, rank=args.rank, flop_line=line, cases=cases, argv=remaining,
         schema="NL2_HU_B638_LIMPED_TURN_RESPONSES_V1")
