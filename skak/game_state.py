from dataclasses import dataclass
from enum import Enum
import numpy as np


class WHITE_PIECE(Enum):
    PAWN=ord('P')
    ROOK=ord('R')
    KNIGHT=ord('N')
    BISHOP=ord('B')
    QUEEN=ord('Q')
    KING=ord('K')


class BLACK_PIECE(Enum):
    PAWN=ord('p')
    ROOK=ord('r')
    KNIGHT=ord('n')
    BISHOP=ord('b')
    QUEEN=ord('q')
    KING=ord('k')


class OTHER_PIECE(Enum):
    EMPTY=ord(' ')
    OUT_OF_BOUNDS=ord('#')


class FILE(Enum):
    A=0
    B=1
    C=2
    D=3
    E=4
    F=5
    G=6
    H=7
    OUT_OF_BOUNDS=-1

    @classmethod
    def from_index(cls, index: int):
        if index >= 0 and index < 8:
            return cls(index)
        else:
            return cls.OUT_OF_BOUNDS


class RANK(Enum):
    _1=0
    _2=1
    _3=2
    _4=3
    _5=4
    _6=5
    _7=6
    _8=7
    OUT_OF_BOUNDS=-1

    @classmethod
    def from_index(cls, index: int):
        if index >= 0 and index < 8:
            return cls(index)
        else:
            return cls.OUT_OF_BOUNDS


@dataclass
class Delta:
    file: int
    rank: int

    def sign(self):
        fs = -1 if self.file < 0 else 1
        fr = -1 if self.rank < 0 else 1
        return Delta(fs, fr)

    def __abs__(self):
        return Delta(abs(self.file), abs(self.rank))

    def __mul__(self, other):
        if isinstance(other, int):
            return Delta(self.file * other, self.rank * other)
        else:
            raise NotImplementedError()

    def max(self):
        return max(self.file, self.rank)


@dataclass
class Square:
    file: FILE
    rank: RANK

    @classmethod
    def from_index(cls, file: int, rank: int):
        return cls(FILE.from_index(file), RANK.from_index(rank))

    def __sub__(self, other):
        return Delta(
            file = self.file.value - other.file.value,
            rank = self.rank.value - other.rank.value,
        )

    def __add__(self, other: Delta):
        file = self.file.value + other.file
        rank = self.rank.value + other.rank
        if file < 0 or file >= 8 or rank < 0 or rank >= 8:
            return InvalidSquare()
        return Square(
            file = FILE.from_index(file),
            rank = RANK.from_index(rank),
        )

    def __str__(self):
        return self.file.name.lower() + self.rank.name[1]


class InvalidSquare:
    pass


@dataclass
class Move:
    start: Square
    end: Square

    @property
    def delta(self):
        return self.end - self.start


class State:
    def __init__(self):
        self.whites_turn = True
        self.whites_short_castle = True
        self.whites_long_castle = True
        self.blacks_short_castle = True
        self.blacks_long_castle = True
        self.enpassant = None
        self.data = np.array([[OTHER_PIECE.EMPTY] * 8] * 8)
        self[FILE.A, RANK._1] = WHITE_PIECE.ROOK
        self[FILE.B, RANK._1] = WHITE_PIECE.KNIGHT
        self[FILE.C, RANK._1] = WHITE_PIECE.BISHOP
        self[FILE.D, RANK._1] = WHITE_PIECE.QUEEN
        self[FILE.E, RANK._1] = WHITE_PIECE.KING
        self[FILE.F, RANK._1] = WHITE_PIECE.BISHOP
        self[FILE.G, RANK._1] = WHITE_PIECE.KNIGHT
        self[FILE.H, RANK._1] = WHITE_PIECE.ROOK

        self[FILE.A, RANK._2] = WHITE_PIECE.PAWN
        self[FILE.B, RANK._2] = WHITE_PIECE.PAWN
        self[FILE.C, RANK._2] = WHITE_PIECE.PAWN
        self[FILE.D, RANK._2] = WHITE_PIECE.PAWN
        self[FILE.E, RANK._2] = WHITE_PIECE.PAWN
        self[FILE.F, RANK._2] = WHITE_PIECE.PAWN
        self[FILE.G, RANK._2] = WHITE_PIECE.PAWN
        self[FILE.H, RANK._2] = WHITE_PIECE.PAWN

        self[FILE.A, RANK._7] = BLACK_PIECE.PAWN
        self[FILE.B, RANK._7] = BLACK_PIECE.PAWN
        self[FILE.C, RANK._7] = BLACK_PIECE.PAWN
        self[FILE.D, RANK._7] = BLACK_PIECE.PAWN
        self[FILE.E, RANK._7] = BLACK_PIECE.PAWN
        self[FILE.F, RANK._7] = BLACK_PIECE.PAWN
        self[FILE.G, RANK._7] = BLACK_PIECE.PAWN
        self[FILE.H, RANK._7] = BLACK_PIECE.PAWN

        self[FILE.A, RANK._8] = BLACK_PIECE.ROOK
        self[FILE.B, RANK._8] = BLACK_PIECE.KNIGHT
        self[FILE.C, RANK._8] = BLACK_PIECE.BISHOP
        self[FILE.D, RANK._8] = BLACK_PIECE.QUEEN
        self[FILE.E, RANK._8] = BLACK_PIECE.KING
        self[FILE.F, RANK._8] = BLACK_PIECE.BISHOP
        self[FILE.G, RANK._8] = BLACK_PIECE.KNIGHT
        self[FILE.H, RANK._8] = BLACK_PIECE.ROOK

    def __getitem__(self, index: Square):
        if isinstance(index, InvalidSquare):
            return OTHER_PIECE.OUT_OF_BOUNDS
        file, rank = index.file, index.rank
        return self.data[file.value, rank.value]

    def __setitem__(
        self,
        index: tuple[FILE, RANK] | Square,
        value: WHITE_PIECE | BLACK_PIECE | OTHER_PIECE,
    ):
        if isinstance(index, tuple):
            file, rank = index
        elif isinstance(index, Square):
            file, rank = index.file, index.rank
        self.data[file.value, rank.value] = value

    def __repr__(self):
        fen = ""
        for rank in range(8):
            spaces = 0
            for file in range(8):
                square = Square.from_index(file, rank)
                piece = self[square]
                if piece == OTHER_PIECE.EMPTY:
                    spaces += 1
                elif isinstance(piece, (WHITE_PIECE, BLACK_PIECE)):
                    if spaces > 0:
                        fen += str(spaces)
                        spaces = 0
                    fen += chr(piece.value)
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
        new_state = State()
        new_state.whites_turn = self.whites_turn
        new_state.whites_short_castle = self.whites_short_castle
        new_state.whites_long_castle = self.whites_long_castle
        new_state.blacks_short_castle = self.blacks_short_castle
        new_state.blacks_long_castle = self.blacks_long_castle
        new_state.data = self.data.copy()
        return new_state

    def locate(self, piece: WHITE_PIECE | BLACK_PIECE | OTHER_PIECE):
        return [
            Square.from_index(file, rank)
            for file, rank in np.argwhere(self.data == piece)
        ]

    @property
    def oppo(self):
        return BLACK_PIECE if self.whites_turn else WHITE_PIECE

    @property
    def your(self):
        return WHITE_PIECE if self.whites_turn else BLACK_PIECE

    def is_free(self, square: Square):
        return self[square] == OTHER_PIECE.EMPTY

    def is_opponent(self, square: Square):
        piece = self[square]
        return isinstance(piece, self.oppo)

    def is_mine(self, square: Square):
        piece = self[square]
        return isinstance(piece, self.your)

    def check_pawn_move(self, move: Move):
        dir = 1 if self.whites_turn else -1
        delta = move.end - move.start
        if delta == Delta(0, 2 * dir) and move.start.rank == (RANK._2 if self.whites_turn else RANK._7):
            mid_square = move.start + Delta(0, dir)
            return self.is_free(mid_square) and self.is_free(move.end)
        elif delta == Delta(0, dir):
            return self.is_free(move.end)
        elif delta == Delta(1, dir) or delta == Delta(-1, dir):
            return self.is_opponent(move.end) or self.enpassant == move.end
        else:
            return False

    def check_rook_move(self, move: Move):
        delta = move.end - move.start
        if delta.file == 0:
            dir = 1 if delta.rank > 0 else -1
            return all([
                self.is_free(move.start + Delta(0, i * dir))
                for i in range(1, abs(delta.rank))
            ])
        elif delta.rank == 0:
            dir = 1 if delta.file > 0 else -1
            return all([
                self.is_free(move.start + Delta(i * dir, 0))
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
        return all([self.is_free(move.start + dir * i) for i in range(1, abs(delta.file))])

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
                        self.is_free(move.start + Delta(-3, 0)) and
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
                        self.is_free(move.start + Delta(-3, 0)) and
                        self.check_move(Move(move.start, move.start + Delta(-1, 0)))
                    )
                )
            )
        )

    def check_move(self, move: Move):
        if self.is_mine(move.end):
            return False
        elif self.is_move_self_check(move):
            return False
        elif self[move.start] == self.your.PAWN:
            return self.check_pawn_move(move)
        elif self[move.start] == self.your.ROOK:
            return self.check_rook_move(move)
        elif self[move.start] == self.your.KNIGHT:
            return self.check_knight_move(move)
        elif self[move.start] == self.your.BISHOP:
            return self.check_bishop_move(move)
        elif self[move.start] == self.your.QUEEN:
            return self.check_queen_move(move)
        elif self[move.start] == self.your.KING:
            return self.check_king_move(move)

    def is_check(self):
        king_square = self.locate(self.your.KING)[0]
        dir = 1 if self.whites_turn else -1
        if any([
            self[king_square + Delta(-1, dir)] in [self.oppo.PAWN, self.oppo.KING],
            self[king_square + Delta(1, dir)] in [self.oppo.PAWN, self.oppo.KING],
            self[king_square + Delta(-1, -dir)] == self.oppo.KING,
            self[king_square + Delta(1, -dir)] == self.oppo.KING,
            self[king_square + Delta(-1, 0)] == self.oppo.KING,
            self[king_square + Delta(1, 0)] == self.oppo.KING,
            self[king_square + Delta(0, -1)] == self.oppo.KING,
            self[king_square + Delta(0, 1)] == self.oppo.KING,
        ]):
            return True
        for dist_file, dist_rank in [(1, 2), (2, 1)]:
            for sign_file in [-1, 1]:
                for sign_rank in [-1, 1]:
                    delta = Delta(dist_file * sign_file, dist_rank * sign_rank)
                    if self[king_square + delta] == self.oppo.KNIGHT:
                        return True
        for sign_file in [-1, 1]:
            for sign_rank in [-1, 1]:
                for dist in range(1, 8):
                    delta = Delta(dist * sign_file, dist * sign_rank)
                    piece = self[king_square + delta]
                    if piece in [self.oppo.BISHOP, self.oppo.QUEEN]:
                        return True
                    elif piece != OTHER_PIECE.EMPTY:
                        break
        for sign_file, sign_rank in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            for dist in range(1, 8):
                delta = Delta(dist * sign_file, dist * sign_rank)
                piece = self[king_square + delta]
                if piece in [self.oppo.ROOK, self.oppo.QUEEN]:
                    return True
                elif piece != OTHER_PIECE.EMPTY:
                    break
        return False

    def is_move_self_check(self, move: Move):
        next_state = self.copy()
        next_state.move(move)
        next_state.whites_turn = not next_state.whites_turn
        return next_state.is_check()

    def is_mate(self):
        return self.is_check() and not self.is_any_move_legal()

    def is_stalemate(self):
        return not self.is_check() and not self.is_any_move_legal()

    def move(self, move: Move):
        next_enpassant = None
        if self[move.start] == WHITE_PIECE.PAWN:
            if move.delta == Delta(0, 2):
                next_enpassant = move.start + Delta(0, 1)
            elif abs(move.delta) == Delta(1, 1) and move.end == self.enpassant:
                self[move.start + Delta(move.delta.file, 0)] = OTHER_PIECE.EMPTY
        elif self[move.start] == BLACK_PIECE.PAWN:
            if move.delta == Delta(0, -2):
                next_enpassant = move.start + Delta(0, -1)
            elif abs(move.delta) == Delta(1, 1) and move.end == self.enpassant:
                self[move.start + Delta(move.delta.file, 0)] = OTHER_PIECE.EMPTY
        elif self[move.start] == WHITE_PIECE.ROOK:
            if move.start == Square(FILE.A, RANK._1):
                self.whites_long_castle = False
            elif move.start == Square(FILE.H, RANK._1):
                self.whites_short_castle = False
        elif self[move.start] == BLACK_PIECE.ROOK:
            if move.start == Square(FILE.A, RANK._8):
                self.blacks_long_castle = False
            elif move.start == Square(FILE.H, RANK._8):
                self.blacks_short_castle = False
        elif self[move.start] == WHITE_PIECE.KING:
            if self.whites_short_castle and move.delta == Delta(2, 0):
                self[Square(FILE.F, RANK._1)] = WHITE_PIECE.ROOK
                self[Square(FILE.H, RANK._1)] = OTHER_PIECE.EMPTY
            elif self.whites_long_castle and move.delta == Delta(-2, 0):
                self[Square(FILE.D, RANK._1)] = WHITE_PIECE.ROOK
                self[Square(FILE.A, RANK._1)] = OTHER_PIECE.EMPTY
            self.whites_short_castle = False
            self.whites_long_castle = False
        elif self[move.start] == BLACK_PIECE.KING:
            if self.blacks_short_castle and move.delta == Delta(2, 0):
                self[Square(FILE.F, RANK._8)] = BLACK_PIECE.ROOK
                self[Square(FILE.H, RANK._8)] = OTHER_PIECE.EMPTY
            elif self.blacks_long_castle and move.delta == Delta(-2, 0):
                self[Square(FILE.D, RANK._8)] = BLACK_PIECE.ROOK
                self[Square(FILE.A, RANK._8)] = OTHER_PIECE.EMPTY
            self.blacks_short_castle = False
            self.blacks_long_castle = False
        self[move.end] = self[move.start]
        self[move.start] = OTHER_PIECE.EMPTY
        self.whites_turn = not self.whites_turn
        self.enpassant = next_enpassant

    def generate_pawn_moves(self, square: Square):
        moves = []
        dir = 1 if self.whites_turn else -1
        for delta in [Delta(0, 2 * dir), Delta(0, dir), Delta(-1, dir), Delta(1, dir)]:
            end = square + delta
            if isinstance(end, InvalidSquare):
                continue
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
                if isinstance(end, InvalidSquare):
                    break
                move = Move(square, end)
                if self.check_move(move):
                    moves.append(move)
        return moves

    def generate_knight_moves(self, square: Square):
        moves = []
        for dist_file, dist_rank in [(1, 2), (2, 1)]:
            for sign_file in [-1, 1]:
                for sign_rank in [-1, 1]:
                    delta = Delta(dist_file * sign_file, dist_rank * sign_rank)
                    end = square + delta
                    if isinstance(end, InvalidSquare):
                        continue
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
                    if isinstance(end, InvalidSquare):
                        break
                    move = Move(square, end)
                    if self.check_move(move):
                        moves.append(move)
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
            if isinstance(end, InvalidSquare):
                continue
            move = Move(square, end)
            if self.check_move(move):
                moves.append(move)
        return moves

    def generate_moves(self, square: Square):
        moves = []
        pieces = WHITE_PIECE if self.whites_turn else BLACK_PIECE
        piece = self[square]
        if piece == pieces.PAWN:
            moves.extend(self.generate_pawn_moves(square))
        elif piece == pieces.ROOK:
            moves.extend(self.generate_rook_moves(square))
        elif piece == pieces.KNIGHT:
            moves.extend(self.generate_knight_moves(square))
        elif piece == pieces.BISHOP:
            moves.extend(self.generate_bishop_moves(square))
        elif piece == pieces.QUEEN:
            moves.extend(self.generate_queen_moves(square))
        elif piece == pieces.KING:
            moves.extend(self.generate_king_moves(square))
        return moves

    def generate_all_moves(self):
        moves = []
        pieces = WHITE_PIECE if self.whites_turn else BLACK_PIECE
        for rank in range(8):
            for file in range(8):
                square = Square.from_index(file, rank)
                moves.extend(self.generate_moves(square))
        return moves

    def is_any_move_legal(self):
        moves = []
        pieces = WHITE_PIECE if self.whites_turn else BLACK_PIECE
        for rank in range(8):
            for file in range(8):
                square = Square.from_index(file, rank)
                if not isinstance(self[square], pieces):
                    continue
                if self.generate_moves(square):
                    return True
        return False
