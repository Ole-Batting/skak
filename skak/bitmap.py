
PAWN   = 0b000001
ROOK   = 0b000010
KNIGHT = 0b000100
BISHOP = 0b001000
QUEEN  = 0b010000
KING   = 0b100000

WHITE  = 0b01_000000
BLACK  = 0b10_000000
FLIP   = 0b11_000000

WHITE_PAWN = WHITE | PAWN
WHITE_ROOK = WHITE | ROOK
WHITE_KNIGHT = WHITE | KNIGHT
WHITE_BISHOP = WHITE | BISHOP
WHITE_QUEEN = WHITE | QUEEN
WHITE_KING = WHITE | KING

BLACK_PAWN = BLACK | PAWN
BLACK_ROOK = BLACK | ROOK
BLACK_KNIGHT = BLACK | KNIGHT
BLACK_BISHOP = BLACK | BISHOP
BLACK_QUEEN = BLACK | QUEEN
BLACK_KING = BLACK | KING

EMPTY = 0

int2char = {
    EMPTY: '-',
    WHITE_PAWN: 'P',
    WHITE_ROOK: 'R',
    WHITE_KNIGHT: 'N',
    WHITE_BISHOP: 'B',
    WHITE_QUEEN: 'Q',
    WHITE_KING: 'K',
    BLACK_PAWN: 'p',
    BLACK_ROOK: 'r',
    BLACK_KNIGHT: 'n',
    BLACK_BISHOP: 'b',
    BLACK_QUEEN: 'q',
    BLACK_KING: 'k',
}

PAWN_THREATS = {WHITE: [0]*64, BLACK: [0]*64}
for i in range(64):
    mod8 = i % 8
    if i < 56: 
        if mod8 == 0:
            PAWN_THREATS[WHITE][i] = 1 << i + 9
        elif mod8 == 7:
            PAWN_THREATS[WHITE][i] = 1 << i + 7
        else:
            PAWN_THREATS[WHITE][i] = 5 << i + 7
    if i > 8:
        if mod8 == 0:
            PAWN_THREATS[BLACK][i] = 1 << i - 7
        elif mod8 == 7:
            PAWN_THREATS[BLACK][i] = 1 << i - 9
        else:
            PAWN_THREATS[BLACK][i] = 5 << i - 9

KNIGHT_THREATS = []
for i in range(64):
    bits = 0
    div8, mod8 = divmod(i, 8)
    if div8 >= 2 and mod8 >= 1:
        bits |= 1 << i - 17
    if div8 >= 2 and mod8 < 7:
        bits |= 1 << i - 15
    if div8 >= 1 and mod8 >= 2:
        bits |= 1 << i - 10
    if div8 >= 1 and mod8 < 6:
        bits |= 1 << i - 6
    if div8 < 7 and mod8 >= 2:
        bits |= 1 << i + 6
    if div8 < 7 and mod8 < 6:
        bits |= 1 << i + 10
    if div8 < 6 and mod8 >= 1:
        bits |= 1 << i + 15
    if div8 < 6 and mod8 < 7:
        bits |= 1 << i + 17
    KNIGHT_THREATS.append(bits)

KING_THREATS = []
for i in range(64):
    bits = 0
    div8, mod8 = divmod(i, 8)
    if div8 >= 1 and mod8 >= 1:
        bits |= 1 << i - 9
    if div8 >= 1:
        bits |= 1 << i - 8
    if div8 >= 1 and mod8 < 7:
        bits |= 1 << i - 7
    if mod8 >= 1:
        bits |= 1 << i - 1
    if mod8 < 7:
        bits |= 1 << i + 1
    if div8 < 7 and mod8 >= 1:
        bits |= 1 << i + 7
    if div8 < 7:
        bits |= 1 << i + 8
    if div8 < 7 and mod8 < 7:
        bits |= 1 << i + 9
    KING_THREATS.append(bits)

NORTH = 0
NORTHEAST = 1
EAST = 2
SOUTHEAST = 3
SOUTH = 4
SOUTHWEST = 5
WEST = 6
NORTHWEST = 7

DIRECTION_OFFSETS = [
    (0, 1),   # NORTH
    (1, 1),   # NORTHEAST
    (1, 0),   # EAST
    (1, -1),  # SOUTHEAST
    (0, -1),  # SOUTH
    (-1, -1), # SOUTHWEST
    (-1, 0),  # WEST
    (-1, 1)   # NORTHWEST
]

rays_to_edge = [[0] * 8 for _ in range(64)]

for square in range(64):
    rank, file = divmod(square, 8)
    for dir_idx, (delta_file, delta_rank) in enumerate(DIRECTION_OFFSETS):
        for i in range(1, 8):
            r = rank + delta_rank * i
            f = file + delta_file * i
            if 0 <= r < 8 and 0 <= f < 8:
                rays_to_edge[square][dir_idx] |= 1 << r * 8 + f
            else:
                break


def print_bm(bm, ch='x'):
    for i in range(7, -1, -1):
        for j in range(8):
            shift = i * 8 + j
            res = '-'
            if (bm >> shift) & 1:
                assert res == '-'
                res = ch
            print(res, end=' ')
        print()



class State:
    bitboard_lut: dict[int: int]
    piecelist_lut: dict[int: list[int]]
    piece_on_square: list[int]

    whites_turn: bool
    whites_short_castle: bool
    whites_long_castle: bool
    blacks_short_castle: bool
    blacks_long_castle: bool
    en_passant: int | None


    def __init__(self):
        # a:01,b:02,c:04,d:08,e:10,f:20,g:40,h:80
        self.bitboard_lut = {
            WHITE_PAWN: 0x0000_0000_0000_ff00,
            WHITE_ROOK: 0x0000_0000_0000_0081,
            WHITE_KNIGHT: 0x0000_0000_0000_0042,
            WHITE_BISHOP: 0x0000_0000_0000_0024,
            WHITE_QUEEN: 0x0000_0000_0000_0008,
            WHITE_KING: 0x0000_0000_0000_0010,
            BLACK_PAWN: 0x00ff_0000_0000_0000,
            BLACK_ROOK: 0x8100_0000_0000_0000,
            BLACK_KNIGHT: 0x4200_0000_0000_0000,
            BLACK_BISHOP: 0x2400_0000_0000_0000,
            BLACK_QUEEN: 0x0800_0000_0000_0000,
            BLACK_KING: 0x1000_0000_0000_0000,
        }

        self.piecelist_lut = {
            WHITE_PAWN: [8, 9, 10, 11, 12, 13, 14, 15],
            WHITE_ROOK: [0, 7],
            WHITE_KNIGHT: [1, 6],
            WHITE_BISHOP: [2, 5],
            WHITE_QUEEN: [3],
            WHITE_KING: [4],
            BLACK_PAWN: [48, 49, 50, 51, 52, 53, 54, 55],
            BLACK_ROOK: [56, 63],
            BLACK_KNIGHT: [57, 62],
            BLACK_BISHOP: [58, 61],
            BLACK_QUEEN: [59],
            BLACK_KING: [60],
        }

        self.piece_on_square = [
            WHITE_ROOK, WHITE_KNIGHT, WHITE_BISHOP, WHITE_QUEEN,
            WHITE_KING, WHITE_BISHOP, WHITE_KNIGHT, WHITE_ROOK,
        ] + [WHITE_PAWN] * 8 + [EMPTY] * 32 + [BLACK_PAWN] * 8 + [
            BLACK_ROOK, BLACK_KNIGHT, BLACK_BISHOP, BLACK_QUEEN,
            BLACK_KING, BLACK_BISHOP, BLACK_KNIGHT, BLACK_ROOK,
        ] 

        self.whites_turn = True
        self.whites_short_castle = True
        self.whites_long_castle = True
        self.blacks_short_castle = True
        self.blacks_long_castle = True
        self.en_passant = True

    @classmethod
    def empty(cls):
        return super().__new__(cls)

    def copy(self):
        state = self.empty()
        state.bitboard_lut = self.bitboard_lut.copy()
        state.piecelist_lut = {
            key: value.copy()
            for key, value in self.piecelist_lut.items()
        }
        state.piece_on_square = self.piece_on_square.copy()
        state.whites_turn = self.whites_turn
        state.whites_short_castle = self.whites_short_castle
        state.whites_long_castle = self.whites_long_castle
        state.blacks_short_castle = self.blacks_short_castle
        state.blacks_long_castle = self.blacks_long_castle
        state.en_passant = self.en_passant

        return state

    def move(self, start: int, target: int):
        start_piece = self.piece_on_square[start]
        target_piece = self.piece_on_square[target]
        delta = target - start
        en_passant = None

        if start_piece & WHITE_PAWN:
            if delta == 16:
                en_passant = start + 8

        start_bm_mask = 1 << start
        target_bm_mask = 1 << target
        self.bitboard_lut[start_piece] ^= start_bm_mask | target_bm_mask

        self.piecelist_lut[start_piece].remove(start)
        self.piecelist_lut[start_piece].append(target)

        self.piece_on_square[target] = start_piece
        self.piece_on_square[start] = EMPTY

        if target_piece != EMPTY:
            self.bitboard_lut[target_piece] &= ~target_bm_mask
            self.piecelist_lut[target_piece].remove(target)

        self.whites_turn = not self.whites_turn

    def check_pawn_move(self, start: int, target: int):
        delta = target - start
        target_piece = self.piece_on_square[target]
        return (
            self.whites_turn and (
                delta == 8 and target_piece == EMPTY or delta == 16 and start // 8 == 1 and
                self.piece_on_square[start + 8] | target_piece == EMPTY or
                (delta == 7 and start % 8 != 0 or delta == 9 and start % 8 != 7) and 
                (target_piece & BLACK or target == self.en_passant)
            ) or not self.whites_turn and (
                delta == -8 and target_piece == EMPTY or delta == -16 and start // 8 == 6 and
                self.piece_on_square[start - 8] | target_piece == EMPTY or
                (delta == -7 and start % 8 != 7 or delta == -9 and start % 8 != 0) and 
                (target_piece & WHITE or target == self.en_passant)
            )
        )

    def check_rook_move(self, start: int, target: int):
        delta = target - start
        target_piece = self.piece_on_square[target]
        lower = min(start, target)
        upper = max(start, target)
        return (
            target_piece == EMPTY or
            self.whites_turn and target_piece & BLACK or 
            not self.whites_turn and target_piece & WHITE
        ) and (
            start % 8 == target % 8 and
            all([self.piece_on_square[i] == EMPTY for i in range(lower + 8, upper, 8)]) or
            start // 8 == target // 8 and
            all([self.piece_on_square[i] == EMPTY for i in range(lower + 1, upper)])
        )

    def check_knight_move(self, start: int, target: int):
        abs_delta_file = abs(target % 8 - start % 8)
        abs_delta_rank = abs(target // 8 - start // 8)
        target_piece = self.piece_on_square[target]
        return (
            target_piece == EMPTY or
            self.whites_turn and target_piece & BLACK or
            not self.whites_turn and target_piece & WHITE
        ) and (
            abs_delta_file == 1 and abs_delta_rank == 2 or
            abs_delta_file == 2 and abs_delta_rank == 1
        )

    def check_bishop_move(self, start: int, target: int):
        target_piece = self.piece_on_square[target]
        lower = min(start, target)
        upper = max(start, target)
        return (
            target_piece == EMPTY or
            self.whites_turn and target_piece & BLACK or 
            not self.whites_turn and target_piece & WHITE
        ) and ( # add edge wrapping checks
            start % 7 == target % 7 and 
            all([self.piece_on_square[i] == EMPTY for i in range(lower + 7, upper, 7)]) or
            start % 9 == target % 9 and
            all([self.piece_on_square[i] == EMPTY for i in range(lower + 9, upper, 9)])
        )

    def check_queen_move(self, start: int, target: int):
        return self.check_rook_move(start, target) or self.check_bishop_move(start, target)

    def check_king_move(self, start: int, target: int):
        target_piece = self.piece_on_square[target]
        abs_delta = abs(target - start)
        return (
            target_piece == EMPTY or
            self.whites_turn and target_piece & BLACK or 
            not self.whites_turn and target_piece & WHITE
        ) and abs_delta == 1 or abs_delta > 6 and abs_delta < 10

    def check_move(self, start: int, target: int):
        start_piece = self.piece_on_square[start]
        if self.is_move_self_check(start, target):
            print('thats check bra')
            return False
        elif start_piece & PAWN:
            return self.check_pawn_move(start, target)
        elif start_piece & ROOK:
            return self.check_rook_move(start, target)
        elif start_piece & KNIGHT:
            return self.check_knight_move(start, target)
        elif start_piece & BISHOP:
            return self.check_bishop_move(start, target)
        elif start_piece & QUEEN:
            return self.check_queen_move(start, target)
        elif start_piece & KING:
            return self.check_king_move(start, target)
        else:
            print('dafuq')

    def is_king_in_check(self, color):
        king_square = self.piecelist_lut[color | KING][0]
        opponent = color ^ FLIP
        pawn_threats = PAWN_THREATS[color][king_square]
        if pawn_threats & self.bitboard_lut[opponent | PAWN]:
            return True
        knight_threats = KNIGHT_THREATS[king_square]
        if knight_threats & self.bitboard_lut[opponent | KNIGHT]:
            return True
        king_threats = KING_THREATS[king_square]
        if king_threats & self.bitboard_lut[opponent | KING]:
            return True
        occupied = 0
        for bb in self.bitboard_lut.values():
            occupied |= bb
        rook_threats = self.get_rook_threats(king_square, occupied)
        if rook_threats & (self.bitboard_lut[opponent | ROOK] | self.bitboard_lut[opponent | QUEEN]):
            return True
        bishop_threats = self.get_bishop_threats(king_square, occupied)
        if bishop_threats & (self.bitboard_lut[opponent | BISHOP] | self.bitboard_lut[opponent | QUEEN]):
            return True

    def get_rook_threats(self, square, occupied):
        threats = 0
        for dir_idx in [NORTH, EAST, SOUTH, WEST]:
            ray = rays_to_edge[square][dir_idx]
            threats |= ray
            blockers = ray & occupied
            if blockers:
                if dir_idx == NORTH or dir_idx == WEST:
                    blocker_square = 63 - (blockers.bit_length() - 1)
                else:
                    blocker_square = (blockers & -blockers).bit_length() - 1
                beyond_blocker = rays_to_edge[blocker_square][dir_idx]
                threats &= ~beyond_blocker
                threats |= 1 << blocker_square
        return threats

    def get_bishop_threats(self, square, occupied):
        threats = 0
        for dir_idx in [NORTHEAST, SOUTHEAST, SOUTHWEST, NORTHWEST]:
            ray = rays_to_edge[square][dir_idx]
            threats |= ray
            blockers = ray & occupied
            if blockers:
                if dir_idx == SOUTHEAST or dir_idx == SOUTHWEST:
                    blocker_square = blockers.bit_length() - 1
                else:
                    blocker_square = (blockers & -blockers).bit_length() - 1
                beyond_blocker = rays_to_edge[blocker_square][dir_idx]
                threats &= ~beyond_blocker
                threats |= 1 << blocker_square
        return threats

    def is_move_self_check(self, start: int, target: int):
        state = self.copy()
        state.move(start, target)
        return state.is_king_in_check(BLACK if state.whites_turn else WHITE)

    def bitboard_show(self):
        print('bitboard show')
        for i in range(7, -1, -1):
            for j in range(8):
                shift = i * 8 + j
                res = '-'
                for bm, ch in zip(self.bitboard_lut.values(), 'PRNBQKprnbqk'):
                    if (bm >> shift) & 1:
                        assert res == '-'
                        res = ch
                print(res, end=' ')
            print()

    def piecelist_show(self):
        print('piecelist show')
        out = ['-'] * 64
        for pl, ch in zip(self.piecelist_lut.values(), 'PRNBQKprnbqk'):
            for i in pl:
                assert out[i] == '-'
                out[i] = ch
        for i in range(7, -1, -1):
            for j in range(8):
                index = i * 8 + j
                print(out[index], end=' ')
            print()

    def piece_on_square_show(self):
        print('piece on square show')
        for i in range(7, -1, -1):
            for j in range(8):
                index = i * 8 + j
                piece_int = self.piece_on_square[index]
                piece = int2char[piece_int]
                print(piece, end=' ')
            print()


if __name__ == '__main__':
    state = State()
    state.bitboard_show()
    state.piecelist_show()
    state.piece_on_square_show()
