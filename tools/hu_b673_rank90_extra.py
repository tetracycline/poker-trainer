"""Complete rank90 with a fresh, preregistered third native flop.

The two B666 workers are already complete and must not be rerun.  This
worker reuses their unchanged source and reach gates on a distinct flop.
"""

import hu_b666_solve


if __name__ == "__main__":
    hu_b666_solve.TURNS = {"Ad9c5h": ["Kc", "7s"], "As8d4h": ["Kc", "6h"]}
    hu_b666_solve.main()
