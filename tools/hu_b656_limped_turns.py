"""Rebuild both seats' turn decisions after a called half-pot bet in a limped pot."""
import argparse

from hu_b590_rank3_barrels import main

SOURCES = {
    10: ("ln-iso-lmp_t_model-1nf06ka", "b50 c", {
        "3c3d4h7h": (14787238707, "5c49ea7800af801c809abe3ae0c0b407bda0cdc5804078a2355af9f077a762cf"),
        "2h5c5dKc": (14787935838, "14c1287f61520199c9284108c2cabe2493eb74eee05c51bbf793cbfbf0d1d9d4"),
        "2c2d4h4c": (14787866823, "0bc9dd8ace0294bb1026442f6b9aa2a9ceea568104f267b5c22bea87c3f43ef0"),
        "3d5h7s6c": (14648360341, "aa1a858743cc1904a7f92a7cb2c4d4102e9faf760bdd4fbd89d482268ad27897"),
    }),
    13: ("ln-iso-lmp_t_model-10v4wiz", "x b50 c", {
        "3c3d4hQh": (14789069340, "54b82571e69cdec7e4af578927ad5665deb8a89c4985fd6f31bdc81de78f4eec"),
        "3d5h7s6c": (14789472209, "bf8905ba2cc9d3eee0afac7e010bf46d7b8b4c8141ca7a331894efb09d8df5c1"),
        "3d8h8s5s": (14789845604, "dd89e2a7ff2547042b37392069258cad8979aa3b80fbcd91c6c6560e387c1a9b"),
    }),
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--rank", type=int, required=True, choices=SOURCES)
    args, remaining = parser.parse_known_args()
    model, line, boards = SOURCES[args.rank]
    main(model_id=model, rank=args.rank, flop_line=line, cases=boards, argv=remaining,
         schema="NL2_HU_B638_LIMPED_TURN_RESPONSES_V1")
