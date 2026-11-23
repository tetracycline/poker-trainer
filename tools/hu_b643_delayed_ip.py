"""Compare delayed IP turn c-bets and strict reach against measured SRP pool replies."""
import argparse
from hu_b590_rank3_barrels import main

SOURCES = {
    20: ("ln-ipfr-t_model-xbvh6", {
        "2s7sKs9d": (14531225991, "c68b5f8ccb94788a6ba82b2e4ba475fa702e96634a1778996894dc8de70c5b1d"),
        "8dQhAs3c": (14528675947, "a0a58760b9197c5626f2d2b3e347310732185d5e6d5963ed7c358cc00be0b5d9"),
        "6s9dJh3c": (14628385508, "36b9cbd95ffe8d0a6356a01876778e1e93ac4c1e4a046a59507ee92c9f45292b"),
        "5hAhAs8s": (14528850727, "0989215a4d7bbff1430413fdca3c115ae384b1d09b9e46ffef69027db4486cce"),
        "3d6h9sTs": (14530176503, "4a6a1cf475b97aec2e60d20d2ad3f36ba64d2bf5fada736cdc65fd375da8c252"),
    }),
    41: ("ln-ipfr-t_model-sxr0qa", {
        "2d9hAs5c": (14529315586, "8674e7e9a94119ffbec6a8407e0e7e97cff930faa26ffd2583fd2f56887360ad"),
        "3d8h8s5s": (14593700327, "cba1ca92b3325f9ca09c8e57927e853eda511e3f5565f8df609f9b71b13130fe"),
        "4d9hJsTs": (14597934573, "247c05663e8edd668a317d3104c33b0ab780ce26722923bc76dc3cff4fea04ec"),
    }),
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--rank", type=int, choices=SOURCES, required=True)
    args, remaining = parser.parse_known_args()
    model, cases = SOURCES[args.rank]
    main(model_id=model, rank=args.rank, flop_line="x x", cases=cases, argv=remaining,
         schema="NL2_HU_B643_IP_DELAYED_TURN_RESPONSES_V1")
