import sys

from skak.bit_state import State


def test_permutations(state: State, depth: int, max_depth: int):
    if depth == max_depth:
        return 1,  1 if state.is_mate() else 0
    total_perm = 0
    total_mat = 0
    for move in state.generate_all_moves():
        next_state = state.copy()
        next_state.move(move)
        perm, mat = test_permutations(next_state, depth+1, max_depth)
        total_perm += perm
        total_mat += mat
    return total_perm, total_mat


if __name__ == '__main__':
    max_depth = int(sys.argv[1])
    state = State()
    perms, mates = test_permutations(state, 0, max_depth)
    print(perms, mates)
