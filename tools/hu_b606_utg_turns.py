"""Replay measured OOP preflop-raiser turn and river replies for UTG against CO."""
import argparse
from hu_b590_rank3_barrels import main

# The archive ID and GitHub SHA identify each original GTO flop and turn.
SOURCES = {
    31: ("ln-opfr-t_model-1xzqrwx", "b75 c", {
        "3dKhAs8s": (14528342851, "1262ef0fbae94fe1ae0e54f1acf919362fefa0f9a5bd0960f44a69657dc49a4c"),
        "2d7hKs9d": (14593222610, "7278ba34b2899846aba8269d54177a3dd4b7848a4d8afcc740bb1bdb732995ea"),
        "3d6h9sTs": (14664221752, "8b457be1f4ef13e6628fe865bb2ceb1e57e53881d82f07446faa45926272d777"),
    }),
    32: ("ln-opfr-t_model-qx9t0u", "b100 c", {
        "3dKhAs8s": (14780587650, "6d07644a5832da09afa353dfa5c1631f610ce378fea809afe5640b138dc3ce36"),
        "2d7hKs9d": (14780922318, "061c0742940602848c2a7d8d12887338f75dc7fd743c9dad52313c4c6d2b53ef"),
        "4dQhKsTc": (14780374050, "88cbb7f32b3e947687a3837eb5c2c76151cd18ebfec23ea9f05399c22bc2891a"),
    }),
    33: ("ln-opfr-t_model-1ocorr7", "x x", {
        "3d6h9sTs": (14664258709, "bb35a382491c0767517fb2151c20eb69c8c93d0a878451a11fdd76d29b2e66ef"),
        "3dKhAsQh": (14528342851, "1262ef0fbae94fe1ae0e54f1acf919362fefa0f9a5bd0960f44a69657dc49a4c"),
        "2d7hKs9d": (14593222610, "7278ba34b2899846aba8269d54177a3dd4b7848a4d8afcc740bb1bdb732995ea"),
    }),
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--rank", required=True, type=int, choices=SOURCES)
    opts, rest = parser.parse_known_args()
    model, line, cases = SOURCES[opts.rank]
    main(model_id=model, rank=opts.rank, flop_line=line, cases=cases, argv=rest)
