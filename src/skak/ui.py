import chess
import numpy as np
import pygame


FPS = 60
IDLE_STEPS = 10


def easingsine(a, b, t: float, dtype=int):
    d = b-a
    z = (1 - np.cos(np.pi * t)) / 2
    return dtype(a + z * d)


class Ui:
    def __init__(
        self,
        piece_px: int,
        square_px: int,
        px_width: int,
        orientation: chess.Color,
    ):
        # TODO: Board orientation
        # TODO: refactor lines stack to avoid oppo beind alone
        self.piece_px = piece_px
        self.square_px = square_px
        self.px_width = px_width
        self.offset = 3 * px_width
        self.piece_width = self.piece_px * self.px_width
        self.square_width = self.square_px * self.px_width
        self.board_width = self.square_width * 8
        self.orientation = orientation

        pygame.init()

        checker_board = np.array([[(i+j)%2 for i in range(8)]for j in range(8)])
        self.blank = np.ones((8,8,3)) * np.array([220, 200, 180])
        self.blank -= checker_board.reshape(8,8,1) * np.array([60, 80, 80])
        self.blank = pygame.surfarray.make_surface(self.blank)
        self.blank = pygame.transform.scale_by(self.blank, self.square_width)
        self.piece_images = {
            chess.BLACK: {
                chess.KING: self.load_piece("piece_images/black_king.png"),
                chess.QUEEN: self.load_piece("piece_images/black_queen.png"),
                chess.BISHOP: self.load_piece("piece_images/black_bishop.png"),
                chess.KNIGHT: self.load_piece("piece_images/black_knight.png"),
                chess.ROOK: self.load_piece("piece_images/black_rook.png"),
                chess.PAWN: self.load_piece("piece_images/black_pawn.png"),
            },
            chess.WHITE: {
                chess.KING: self.load_piece("piece_images/white_king.png"),
                chess.QUEEN: self.load_piece("piece_images/white_queen.png"),
                chess.BISHOP: self.load_piece("piece_images/white_bishop.png"),
                chess.KNIGHT: self.load_piece("piece_images/white_knight.png"),
                chess.ROOK: self.load_piece("piece_images/white_rook.png"),
                chess.PAWN: self.load_piece("piece_images/white_pawn.png"),
            },
        }
        self.move_overlay = self.load_piece("piece_images/move.png")
        self.capture_overlay = self.load_piece("piece_images/capture.png")
        self.mate_overlay = self.load_piece("piece_images/mate.png")
        self.stalemate_overlay = self.load_piece("piece_images/stalemate.png")

        self.screen = pygame.display.set_mode((self.board_width, self.board_width))
        self.clock = pygame.time.Clock()

    def load_piece(self, path):
        image = pygame.image.load(path)
        image = pygame.transform.scale(image, (self.piece_px, self.piece_px))
        image = pygame.transform.scale_by(image, self.px_width)
        return image

    def reset(self):
        self.screen.blit(self.blank, (0, 0))

    def tick(self):
        self.clock.tick(FPS)

    def blit_state(self, board: chess.Board):
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is None:
                continue
            self.place(self.piece_images[piece.color][piece.piece_type], square)
        if board.is_checkmate():
            self.place_center(self.mate_overlay)
        elif board.is_stalemate():
            self.place_center(self.stalemate_overlay)

    def blit_moves(self, board: chess.Board, square: chess.Square):
        for move in board.legal_moves:
            if move.from_square != square:
                continue
            if board.piece_at(move.to_square) is None:
                self.place(self.move_overlay, move.to_square)
            else:
                self.place(self.capture_overlay, move.to_square)

    def blit_promotion(self, color):
        self.place(self.piece_images[color][chess.QUEEN], chess.D5)
        self.place(self.piece_images[color][chess.ROOK], chess.E5)
        self.place(self.piece_images[color][chess.BISHOP], chess.D4)
        self.place(self.piece_images[color][chess.KNIGHT], chess.E4)
        self.place(self.move_overlay, chess.D5)
        self.place(self.move_overlay, chess.E5)
        self.place(self.move_overlay, chess.D4)
        self.place(self.move_overlay, chess.E4)

    def place(self, surf, square: chess.Square):
        rank, file = divmod(square, 8)
        x, y = self.loc(file, rank)
        self.screen.blit(surf, (x + self.offset, y + self.offset))

    def place_center(self, surf):
        x = 3.5 * self.square_width + 3 * self.px_width
        self.screen.blit(surf, (x, x))

    def loc(self, file, rank):
        if self.orientation == chess.WHITE:
            inverted_rank = 7 - rank
            return np.array([file, inverted_rank]) * self.square_width
        else:
            inverted_file = 7 - file
            return np.array([inverted_file, rank]) * self.square_width

    def unloc(self, x, y):
        if self.orientation == chess.WHITE:
            file, inverted_rank = np.array([x, y]) // self.square_width
            rank = 7 - inverted_rank
            return chess.Square(file + 8 * rank)
        else:
            inverted_file, rank = np.array([x, y]) // self.square_width
            file = 7 - inverted_file
            return chess.Square(file + 8 * rank)

    def idle(self):
        for _ in range(IDLE_STEPS):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return True
            self.tick()
        return False


    def anim_move(self, board: chess.Board, move: chess.Move, steps: int = 20, end: int = 2):
        piece = board.piece_at(move.from_square)
        piece_image = self.piece_images[piece.color][piece.piece_type]
        from_rank, from_file = divmod(move.from_square, 8)
        to_rank, to_file = divmod(move.to_square, 8)
        from_x, from_y = self.loc(from_file, from_rank)
        to_x, to_y = self.loc(to_file, to_rank)
        t_space = np.linspace(0, 1, steps).tolist()
        for t in t_space + [1] * end:
            x = easingsine(from_x, to_x, t)
            y = easingsine(from_y, to_y, t)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return True

            self.reset()
            for s in range(64):
                p = board.piece_at(s)
                if p is None or s == move.from_square:
                    continue
                self.place(self.piece_images[p.color][p.piece_type], s)
            self.screen.blit(piece_image, (x + self.offset, y+ self.offset))
            pygame.display.flip()
            self.tick()
        return False

