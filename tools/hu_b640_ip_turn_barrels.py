"""Reproduce BTN and CO turn barrels versus the size-matched NL2 BB replies."""
import argparse

from hu_b590_rank3_barrels import main

SOURCES = {
    36: ("ln-ipfr-t_model-1ktwuv7", "x b100 c", {
        "6s9dJh3c": (14628385508, "36b9cbd95ffe8d0a6356a01876778e1e93ac4c1e4a046a59507ee92c9f45292b"),
        "4dQhKsTc": (14600212926, "e22ef0510366501905aee957468b60bd3c5b586adcf3fe2406db3b08beeba7e1"),
        "2d9hAsKd": (14599607198, "8f19dbd115e4b6260aecf3b22fb9d43fc27d9a8327885735d050f2e37b0983b3"),
    }),
    37: ("ln-ipfr-t_model-1u5hox2", "x b75 c", {
        "8dQhAs3c": (14528675947, "a0a58760b9197c5626f2d2b3e347310732185d5e6d5963ed7c358cc00be0b5d9"),
        "3d6h9sTs": (14530176503, "4a6a1cf475b97aec2e60d20d2ad3f36ba64d2bf5fada736cdc65fd375da8c252"),
        "4d9hJsTs": (14591863023, "3e938b4911d61697da9e1fe458f61153b56fa2da32ecd38f3b675f9a1a9b57c7"),
        "4dQhKsTc": (14591903053, "a91926766c28752b494da69e09d90ea001e7665c50643f15265faf152fbc9898"),
        "2s7sKs9d": (14531225991, "c68b5f8ccb94788a6ba82b2e4ba475fa702e96634a1778996894dc8de70c5b1d"),
    }),
    38: ("ln-ipfr-t_model-1xz5oyp", "x b33 c", {
        "3d8h8s5s": (14592317474, "e9f9b205d1ba876c0e713e0a62344865fc99adb87b8188e0c62dfa99b645ffdd"),
        "2d9hAsKd": (14599607198, "8f19dbd115e4b6260aecf3b22fb9d43fc27d9a8327885735d050f2e37b0983b3"),
        "4d9hJsTs": (14591863023, "3e938b4911d61697da9e1fe458f61153b56fa2da32ecd38f3b675f9a1a9b57c7"),
        "4dQhKsTc": (14591903053, "a91926766c28752b494da69e09d90ea001e7665c50643f15265faf152fbc9898"),
        "3d6h9sTs": (14530176503, "4a6a1cf475b97aec2e60d20d2ad3f36ba64d2bf5fada736cdc65fd375da8c252"),
    }),
    39: ("ln-ipfr-t_model-dzbacd", "x b50 c", {
        "4dQhKsTc": (14591903053, "a91926766c28752b494da69e09d90ea001e7665c50643f15265faf152fbc9898"),
        "4d9hJsTs": (14591863023, "3e938b4911d61697da9e1fe458f61153b56fa2da32ecd38f3b675f9a1a9b57c7"),
        "3d8h8s5s": (14592317474, "e9f9b205d1ba876c0e713e0a62344865fc99adb87b8188e0c62dfa99b645ffdd"),
        "2s7sKs9d": (14531225991, "c68b5f8ccb94788a6ba82b2e4ba475fa702e96634a1778996894dc8de70c5b1d"),
        "6s9dJh3c": (14628385508, "36b9cbd95ffe8d0a6356a01876778e1e93ac4c1e4a046a59507ee92c9f45292b"),
    }),
    59: ("ln-ipfr-t_model-1h05w49", "x b33 c", {
        "3d8h8s5s": (14593700327, "cba1ca92b3325f9ca09c8e57927e853eda511e3f5565f8df609f9b71b13130fe"),
        "2d9hAs5c": (14529315586, "8674e7e9a94119ffbec6a8407e0e7e97cff930faa26ffd2583fd2f56887360ad"),
        "4d9hJsTs": (14597934573, "247c05663e8edd668a317d3104c33b0ab780ce26722923bc76dc3cff4fea04ec"),
    }),
    60: ("ln-ipfr-t_model-hxdit", "x b50 c", {
        "4d9hJsTs": (14597934573, "247c05663e8edd668a317d3104c33b0ab780ce26722923bc76dc3cff4fea04ec"),
        "5d9hJsAh": (14706911239, "d1178390326551a5e9decbfd50f7f09864fd56c34941c80039b70d14c1467c4e"),
        "4s9sJs8c": (14729431007, "3c0cd00b9653960a59550e18f5c9c3bdce126c1ee6aa80a6d9f6dc5a42abeaf7"),
        "4d7h9sAd": (14729427685, "ce866813890586a85aee2def811bcdfa39c8544b29f5944f828387728f16d1d5"),
    }),
    61: ("ln-ipfr-t_model-qpx6tn", "x b100 c", {
        "4dQhKsTc": (14706219316, "cb7b0864f0e8dbf8b5ef084cdff6086d3ec935a92e7765a8d69c43b3076a1698"),
        "5d9hJsAh": (14707145219, "6048ed90e9d3f43c56682671ae38c5d8ec96ecbe5241c5ed8835028761d0f083"),
        "4dJhQs7s": (14718689983, "ee7f8e45559e41e0a2e2335493547ee2e92d84b4dd2c8499c564353159563123"),
    }),
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--rank", type=int, choices=SOURCES, required=True)
    args, remaining = parser.parse_known_args()
    model, line, boards = SOURCES[args.rank]
    main(model_id=model, rank=args.rank, flop_line=line, cases=boards, argv=remaining,
         schema="NL2_HU_B640_IP_TURN_BARRELS_V1")
