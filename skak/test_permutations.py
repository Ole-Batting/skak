import sys

from skak.bit_state import State


def test_permutations(state: State, depth: int, max_depth: int):
    if depth == max_depth:
        fen = repr(state)
        perm = [fen]
        mat = [fen] if state.is_mate() else list()
        return perm, mat
    total_perm = list()
    total_mat = list()
    for move in state.generate_all_moves():
        next_state = state.copy()
        next_state.move(move)
        perm, mat = test_permutations(next_state, depth+1, max_depth)
        total_perm.extend(perm)
        total_mat.extend(mat)
    # if len(total_perm) == 0:
    #     fen = repr(state)
    #     perm = {fen}
    #     mat = {fen} if state.is_mate() else set()
    #     return perm, mat
    return total_perm, total_mat


if __name__ == '__main__':
    max_depth = int(sys.argv[1])
    state = State()
    perms, mates = test_permutations(state, 0, max_depth)
    print(len(perms), len(mates))
