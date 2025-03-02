import numpy as np


# Piece encoding 8-bit
# which piece in one-hot bits 1-6
# |k|q|b|n|r|p|
PAWN   = 0b00_000001
ROOK   = 0b00_000010
KNIGHT = 0b00_000100
BISHOP = 0b00_001000
QUEEN  = 0b00_010000
KING   = 0b00_100000
# color is bits 7-8
# |w|b|
WHITE  = 0b01_000000
BLACK  = 0b10_000000

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

piece_char = {
    WHITE_PAWN:'P',
    WHITE_ROOK:'R',
    WHITE_KNIGHT:'N',
    WHITE_BISHOP:'B',
    WHITE_QUEEN:'Q',
    WHITE_KING:'K',
    BLACK_PAWN:'p',
    BLACK_ROOK:'r',
    BLACK_KNIGHT:'n',
    BLACK_BISHOP:'b',
    BLACK_QUEEN:'q',
    BLACK_KING:'k',
}

EMPTY = 0
OUT_OF_BOUNDS = 0b100_000000
PAD = 2

FILE_A = 2
FILE_B = 3
FILE_C = 4
FILE_D = 5
FILE_E = 6
FILE_F = 7
FILE_G = 8
FILE_H = 9
FILE_NAME = "qwabcdefghzx"


RANK_1 = 2
RANK_2 = 3
RANK_3 = 4
RANK_4 = 5
RANK_5 = 6
RANK_6 = 7
RANK_7 = 8
RANK_8 = 9


class Delta:
    def __init__(self, file: int, rank: int):
        self.file = file
        self.rank = rank

    def sign(self):
        fs = -1 if self.file < 0 else 1
        fr = -1 if self.rank < 0 else 1
        return Delta(fs, fr)

    def __abs__(self):
        return Delta(abs(self.file), abs(self.rank))

    def __mul__(self, other: int):
        return Delta(self.file * other, self.rank * other)

    def max(self):
        return max(self.file, self.rank)

    def __repr__(self):
        return f'{self.file}_{self.rank}'

    def __eq__(self, other):
        return (self.file==other.file) and (self.rank==other.rank)


class Square:
    def __init__(self, file: int, rank: int):
        self.file = file
        self.rank = rank

    def __sub__(self, other):
        return Delta(
            file = self.file - other.file,
            rank = self.rank - other.rank,
        )

    def __add__(self, other: Delta):
        file = self.file + other.file
        rank = self.rank + other.rank
        return Square(file=file, rank=rank)

    def __str__(self):
        return FILE_NAME[self.file] + str(self.rank + 1 - PAD)

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return self.file == other.file and self.rank == other.rank


class Move:
    def __init__(self, start: Square, end: Square):
        self.start = start
        self.end = end

    def delta(self):
        return self.end - self.start


class State:
    whites_turn: bool
    whites_short_castle: bool
    whites_long_castle: bool
    blacks_short_castle: bool
    blacks_long_castle: bool
    enpassant: Square | None
    data: np.ndarray
    mine: int
    oppo: int

    @classmethod
    def empty(cls, *args, **kwargs):
        instance = super().__new__(cls)
        return instance

    def __init__(self):
        self.whites_turn = True
        self.whites_short_castle = True
        self.whites_long_castle = True
        self.blacks_short_castle = True
        self.blacks_long_castle = True
        self.enpassant = None
        self.data = np.pad(
            np.array([[EMPTY] * 8] * 8),
            PAD,
            mode='constant',
            constant_values=OUT_OF_BOUNDS,
        )
        self[Square(FILE_A, RANK_1)] = WHITE_ROOK
        self[Square(FILE_B, RANK_1)] = WHITE_KNIGHT
        self[Square(FILE_C, RANK_1)] = WHITE_BISHOP
        self[Square(FILE_D, RANK_1)] = WHITE_QUEEN
        self[Square(FILE_E, RANK_1)] = WHITE_KING
        self[Square(FILE_F, RANK_1)] = WHITE_BISHOP
        self[Square(FILE_G, RANK_1)] = WHITE_KNIGHT
        self[Square(FILE_H, RANK_1)] = WHITE_ROOK

        self[Square(FILE_A, RANK_2)] = WHITE_PAWN
        self[Square(FILE_B, RANK_2)] = WHITE_PAWN
        self[Square(FILE_C, RANK_2)] = WHITE_PAWN
        self[Square(FILE_D, RANK_2)] = WHITE_PAWN
        self[Square(FILE_E, RANK_2)] = WHITE_PAWN
        self[Square(FILE_F, RANK_2)] = WHITE_PAWN
        self[Square(FILE_G, RANK_2)] = WHITE_PAWN
        self[Square(FILE_H, RANK_2)] = WHITE_PAWN

        self[Square(FILE_A, RANK_7)] = BLACK_PAWN
        self[Square(FILE_B, RANK_7)] = BLACK_PAWN
        self[Square(FILE_C, RANK_7)] = BLACK_PAWN
        self[Square(FILE_D, RANK_7)] = BLACK_PAWN
        self[Square(FILE_E, RANK_7)] = BLACK_PAWN
        self[Square(FILE_F, RANK_7)] = BLACK_PAWN
        self[Square(FILE_G, RANK_7)] = BLACK_PAWN
        self[Square(FILE_H, RANK_7)] = BLACK_PAWN

        self[Square(FILE_A, RANK_8)] = BLACK_ROOK
        self[Square(FILE_B, RANK_8)] = BLACK_KNIGHT
        self[Square(FILE_C, RANK_8)] = BLACK_BISHOP
        self[Square(FILE_D, RANK_8)] = BLACK_QUEEN
        self[Square(FILE_E, RANK_8)] = BLACK_KING
        self[Square(FILE_F, RANK_8)] = BLACK_BISHOP
        self[Square(FILE_G, RANK_8)] = BLACK_KNIGHT
        self[Square(FILE_H, RANK_8)] = BLACK_ROOK

        self.mine = WHITE
        self.oppo = BLACK

    def __getitem__(self, index: Square):
        return self.data[index.file, index.rank]

    def __setitem__(self, index: Square, value: int):
        self.data[index.file, index.rank] = value

    def __repr__(self):
        fen = ""
        for rank in range(RANK_1, RANK_8+1):
            spaces = 0
            for file in range(FILE_A, FILE_H+1):
                square = Square(file, rank)
                piece = self[square]
                if piece == EMPTY:
                    spaces += 1
                elif piece > 0:
                    if spaces > 0:
                        fen += str(spaces)
                        spaces = 0
                    fen += piece_char[piece]
            if spaces > 0:
                fen += str(spaces)
            fen += '/'
        fen = fen[:-1]
        fen += ' w ' if self.whites_turn else ' b '
        fen += 'K' if self.whites_short_castle else ''
        fen += 'Q' if self.whites_long_castle else ''
        fen += 'k' if self.blacks_short_castle else ''
        fen += 'q' if self.blacks_long_castle else ''
        if fen[-1] == ' ':
            fen += '-'
        fen += f' {str(self.enpassant)}' if self.enpassant is not None else ' -' 
        # TODO add clock counters
        return fen

    def copy(self):
        new_state = State.empty()
        new_state.whites_turn = self.whites_turn
        new_state.whites_short_castle = self.whites_short_castle
        new_state.whites_long_castle = self.whites_long_castle
        new_state.blacks_short_castle = self.blacks_short_castle
        new_state.blacks_long_castle = self.blacks_long_castle
        new_state.enpassant = self.enpassant
        new_state.data = self.data.copy()
        new_state.mine = self.mine
        new_state.oppo = self.oppo
        return new_state

    def locate(self, piece: int):
        return [
            Square(file, rank) 
            for file, rank in np.argwhere(self.data == piece)
        ]

    def is_mine(self, square: Square):
        return self[square] & self.mine

    def check_pawn_move(self, move: Move):
        dir = 1 if self.whites_turn else -1
        delta = move.end - move.start
        if (delta == Delta(0, 2 * dir)) and (move.start.rank == (RANK_2 if self.whites_turn else RANK_7)):
            mid_square = move.start + Delta(0, dir)
            return self[mid_square] == EMPTY and self[move.end] == EMPTY
        elif delta == Delta(0, dir):
            return self[move.end] == EMPTY
        elif delta == Delta(1, dir) or delta == Delta(-1, dir):
            return (self[move.end] & self.oppo) or (self.enpassant and self.enpassant == move.end)
        else:
            return False

    def check_rook_move(self, move: Move):
        delta = move.end - move.start
        if delta.file == 0:
            dir = 1 if delta.rank > 0 else -1
            return all([
                self[move.start + Delta(0, i * dir)] == EMPTY
                for i in range(1, abs(delta.rank))
            ])
        elif delta.rank == 0:
            dir = 1 if delta.file > 0 else -1
            return all([
                self[move.start + Delta(i * dir, 0)] == EMPTY
                for i in range(1, abs(delta.file))
            ])
        else:
            return False

    def check_knight_move(self, move: Move):
        delta = abs(move.end - move.start)
        return delta == Delta(2, 1) or delta == Delta(1, 2)

    def check_bishop_move(self, move: Move):
        delta = move.end - move.start
        if abs(delta.file) != abs(delta.rank):
            return False
        dir = delta.sign()
        return all([self[move.start + dir * i] == EMPTY for i in range(1, abs(delta.file))])

    def check_queen_move(self, move: Move):
        return self.check_rook_move(move) or self.check_bishop_move(move)

    def check_king_move(self, move: Move):
        delta = move.end - move.start
        return (
            abs(delta).max() == 1 or
            (
                self.whites_turn and
                (
                    (
                        self.whites_short_castle and
                        delta == Delta(2, 0) and
                        self.check_move(Move(move.start, move.start + Delta(1, 0)))
                    ) or
                    (
                        self.whites_long_castle and
                        delta == Delta(-2, 0) and
                        self[move.start + Delta(-3, 0)] == EMPTY and
                        self.check_move(Move(move.start, move.start + Delta(-1, 0)))
                    )
                )
            ) or
            (
                not self.whites_turn and 
                (
                    (
                        self.blacks_short_castle and
                        delta == Delta(2, 0) and
                        self.check_move(Move(move.start, move.start + Delta(1, 0)))
                    ) or 
                    (
                        self.blacks_long_castle and 
                        delta == Delta(-2, 0) and
                        self[move.start + Delta(-3, 0)] == EMPTY and
                        self.check_move(Move(move.start, move.start + Delta(-1, 0)))
                    )
                )
            )
        )

    def check_move(self, move: Move):
        if self[move.end] & (self.mine | OUT_OF_BOUNDS):
            return False
        elif self.is_move_self_check(move):
            return False
        elif self[move.start] == (self.mine | PAWN):
            return self.check_pawn_move(move)
        elif self[move.start] == (self.mine | ROOK):
            return self.check_rook_move(move)
        elif self[move.start] == (self.mine | KNIGHT):
            return self.check_knight_move(move)
        elif self[move.start] == (self.mine | BISHOP):
            return self.check_bishop_move(move)
        elif self[move.start] == (self.mine | QUEEN):
            return self.check_queen_move(move)
        elif self[move.start] == (self.mine | KING):
            return self.check_king_move(move)

    def is_mine_check(self):
        king_square = self.locate(self.mine | KING)[0]
        dir = 1 if self.whites_turn else -1
        if (
            self[king_square + Delta(-1, dir)] in [self.oppo | PAWN, self.oppo | KING] and
            self[king_square + Delta(1, dir)] in [self.oppo | PAWN, self.oppo | KING] and
            self[king_square + Delta(-1, -dir)] == (self.oppo | KING) and
            self[king_square + Delta(1, -dir)] == (self.oppo | KING) and
            self[king_square + Delta(-1, 0)] == (self.oppo | KING) and
            self[king_square + Delta(1, 0)] == (self.oppo | KING) and
            self[king_square + Delta(0, -1)] == (self.oppo | KING) and
            self[king_square + Delta(0, 1)] == (self.oppo | KING)
        ):
            return True
        for dist_file, dist_rank in [(1, 2), (2, 1)]:
            for sign_file in [-1, 1]:
                for sign_rank in [-1, 1]:
                    delta = Delta(dist_file * sign_file, dist_rank * sign_rank)
                    if self[king_square + delta] == (self.oppo | KNIGHT):
                        return True
        for sign_file in [-1, 1]:
            for sign_rank in [-1, 1]:
                for dist in range(1, 8):
                    delta = Delta(dist * sign_file, dist * sign_rank)
                    piece = self[king_square + delta]
                    if piece in [self.oppo | BISHOP, self.oppo | QUEEN]:
                        return True
                    elif piece != EMPTY:
                        break
        for sign_file, sign_rank in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            for dist in range(1, 8):
                delta = Delta(dist * sign_file, dist * sign_rank)
                piece = self[king_square + delta]
                if piece in [self.oppo | ROOK, self.oppo | QUEEN]:
                    return True
                elif piece != EMPTY:
                    break
        return False

    def is_oppo_check(self):
        king_square = self.locate(self.oppo | KING)[0]
        dir = -1 if self.whites_turn else 1
        if (
            self[king_square + Delta(-1, dir)] in [self.mine | PAWN, self.mine | KING] and
            self[king_square + Delta(1, dir)] in [self.mine | PAWN, self.mine | KING] and
            self[king_square + Delta(-1, -dir)] == (self.mine | KING) and
            self[king_square + Delta(1, -dir)] == (self.mine | KING) and
            self[king_square + Delta(-1, 0)] == (self.mine | KING) and
            self[king_square + Delta(1, 0)] == (self.mine | KING) and
            self[king_square + Delta(0, -1)] == (self.mine | KING) and
            self[king_square + Delta(0, 1)] == (self.mine | KING)
        ):
            return True
        for dist_file, dist_rank in [(1, 2), (2, 1)]:
            for sign_file in [-1, 1]:
                for sign_rank in [-1, 1]:
                    delta = Delta(dist_file * sign_file, dist_rank * sign_rank)
                    if self[king_square + delta] == (self.mine | KNIGHT):
                        return True
        for sign_file in [-1, 1]:
            for sign_rank in [-1, 1]:
                for dist in range(1, 8):
                    delta = Delta(dist * sign_file, dist * sign_rank)
                    piece = self[king_square + delta]
                    if piece in [self.mine | BISHOP, self.mine | QUEEN]:
                        return True
                    elif piece != EMPTY:
                        break
        for sign_file, sign_rank in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            for dist in range(1, 8):
                delta = Delta(dist * sign_file, dist * sign_rank)
                piece = self[king_square + delta]
                if piece in [self.mine | ROOK, self.mine | QUEEN]:
                    return True
                elif piece != EMPTY:
                    break
        return False

    def step(self):
        self.whites_turn = not self.whites_turn
        self.mine ^= 0b11_000000
        self.oppo ^= 0b11_000000

    def is_move_self_check(self, move: Move):
        next_state = self.copy()
        next_state.move(move)
        return next_state.is_oppo_check()

    def is_mate(self):
        return self.is_mine_check() and not self.is_any_move_legal()

    def is_stalemate(self):
        return not self.is_mine_check() and not self.is_any_move_legal()

    def move(self, move: Move):
        next_enpassant = None
        if self[move.start] == WHITE_PAWN:
            if move.delta() == Delta(0, 2):
                next_enpassant = move.start + Delta(0, 1)
            elif abs(move.delta()) == Delta(1, 1) and self.enpassant and move.end == self.enpassant:
                self[move.start + Delta(move.delta().file, 0)] = EMPTY
        elif self[move.start] == BLACK_PAWN:
            if move.delta() == Delta(0, -2):
                next_enpassant = move.start + Delta(0, -1)
            elif abs(move.delta()) == Delta(1, 1) and self.enpassant and move.end == self.enpassant:
                self[move.start + Delta(move.delta().file, 0)] = EMPTY
        elif self[move.start] == WHITE_ROOK:
            if move.start == Square(FILE_A, RANK_1):
                self.whites_long_castle = False
            elif move.start == Square(FILE_H, RANK_1):
                self.whites_short_castle = False
        elif self[move.start] == BLACK_ROOK:
            if move.start == Square(FILE_A, RANK_8):
                self.blacks_long_castle = False
            elif move.start == Square(FILE_H, RANK_8):
                self.blacks_short_castle = False
        elif self[move.start] == WHITE_KING:
            if self.whites_short_castle and move.delta() == Delta(2, 0):
                self[Square(FILE_F, RANK_1)] = WHITE_ROOK
                self[Square(FILE_H, RANK_1)] = EMPTY
            elif self.whites_long_castle and move.delta() == Delta(-2, 0):
                self[Square(FILE_D, RANK_1)] = WHITE_ROOK
                self[Square(FILE_A, RANK_1)] = EMPTY
            self.whites_short_castle = False
            self.whites_long_castle = False
        elif self[move.start] == BLACK_KING:
            if self.blacks_short_castle and move.delta() == Delta(2, 0):
                self[Square(FILE_F, RANK_8)] = BLACK_ROOK
                self[Square(FILE_H, RANK_8)] = EMPTY
            elif self.blacks_long_castle and move.delta() == Delta(-2, 0):
                self[Square(FILE_D, RANK_8)] = BLACK_ROOK
                self[Square(FILE_A, RANK_8)] = EMPTY
            self.blacks_short_castle = False
            self.blacks_long_castle = False
        self[move.end] = self[move.start]
        self[move.start] = EMPTY
        self.step()
        self.enpassant = next_enpassant

    def generate_pawn_moves(self, square: Square):
        moves = []
        dir = 1 if self.whites_turn else -1
        for delta in [Delta(0, 2 * dir), Delta(0, dir), Delta(-1, dir), Delta(1, dir)]:
            end = square + delta
            move = Move(square, square + delta)
            if self.check_move(move):
                moves.append(move)
        return moves

    def generate_rook_moves(self, square: Square):
        moves = []
        for sign_file, sign_rank in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            for dist in range(1, 8):
                delta = Delta(dist * sign_file, dist * sign_rank)
                end = square + delta
                move = Move(square, end)
                if self.check_move(move):
                    moves.append(move)
                elif self[end] == OUT_OF_BOUNDS:
                    break
        return moves

    def generate_knight_moves(self, square: Square):
        moves = []
        for dist_file, dist_rank in [(1, 2), (2, 1)]:
            for sign_file in [-1, 1]:
                for sign_rank in [-1, 1]:
                    delta = Delta(dist_file * sign_file, dist_rank * sign_rank)
                    end = square + delta
                    move = Move(square, end)
                    if self.check_move(move):
                        moves.append(move)
        return moves

    def generate_bishop_moves(self, square: Square):
        moves = []
        for sign_file in [-1, 1]:
            for sign_rank in [-1, 1]:
                for dist in range(1, 8):
                    delta = Delta(dist * sign_file, dist * sign_rank)
                    end = square + delta
                    move = Move(square, end)
                    if self.check_move(move):
                        moves.append(move)
                    elif self[end] == OUT_OF_BOUNDS:
                        break
        return moves

    def generate_queen_moves(self, square: Square):
        moves = []
        moves.extend(self.generate_rook_moves(square))
        moves.extend(self.generate_bishop_moves(square))
        return moves

    def generate_king_moves(self, square: Square):
        moves = []
        for dist_file, dist_rank in [
            (-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1),
            (1, -1), (1, 0), (1, 1), (-2, 0), (2, 0)
        ]:
            delta = Delta(dist_file, dist_rank)
            end = square + delta
            move = Move(square, end)
            if self.check_move(move):
                moves.append(move)
        return moves

    def generate_moves(self, square: Square):
        moves = []
        piece = self[square]
        if piece & self.mine:
            if piece & PAWN:
                moves.extend(self.generate_pawn_moves(square))
            elif piece & ROOK:
                moves.extend(self.generate_rook_moves(square))
            elif piece & KNIGHT:
                moves.extend(self.generate_knight_moves(square))
            elif piece & BISHOP:
                moves.extend(self.generate_bishop_moves(square))
            elif piece & QUEEN:
                moves.extend(self.generate_queen_moves(square))
            elif piece & KING:
                moves.extend(self.generate_king_moves(square))
        return moves

    def generate_all_moves(self):
        moves = []
        for rank in range(RANK_1, RANK_8+1):
            for file in range(FILE_A, FILE_H+1):
                square = Square(file, rank)
                moves.extend(self.generate_moves(square))
        return moves

    def is_any_move_legal(self):
        moves = []
        for rank in range(RANK_1, RANK_8+1):
            for file in range(FILE_A, FILE_H+1):
                square = Square(file, rank)
                moves = self.generate_moves(square)
                if moves:
                    return True
        return False

if __name__ == '__main__':
    state = State()

    a2i = dict(zip('abcdefgh',range(8)))

    def m2s(mov):
        a, b, c, d = mov
        return Move(
            Square(a2i[a]+PAD, int(b)-1+PAD),
            Square(a2i[c]+PAD, int(d)-1+PAD),
        )

    def m(mov):
        state.move(m2s(mov))
        print(state)

    m('e2e4')
    m('d7d5')
    m('e4e5')
    m('d5d4')
    m('c2c4')

    print(state.check_move(m2s('d4c3')))
