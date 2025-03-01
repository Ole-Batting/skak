import einops
import numpy as np
import pygame

from skak.bit_state import (
    Square, State, EMPTY, PAD,
    WHITE_PAWN, WHITE_ROOK, WHITE_KNIGHT, WHITE_BISHOP, WHITE_QUEEN, WHITE_KING,
    BLACK_PAWN, BLACK_ROOK, BLACK_KNIGHT, BLACK_BISHOP, BLACK_QUEEN, BLACK_KING,
)


class Board:
    def __init__(self, piece_px, square_px, px_width):
        self.piece_px = piece_px
        self.square_px = square_px
        self.px_width = px_width
        self.piece_width = self.piece_px * self.px_width
        self.square_width = self.square_px * self.px_width
        self.board_width = self.square_width * 8

        pygame.init()

        self.blank = np.array([[(i+j)%2 for i in range(8)]for j in range(8)]) * 64 + 128 - 32
        self.blank = einops.repeat(self.blank, 'h w -> h w c', c=3)
        self.blank = pygame.surfarray.make_surface(self.blank)
        self.blank = pygame.transform.scale_by(self.blank, self.square_width)
        self.black_king = self.load_piece("piece_images/black_king.png")
        self.black_queen = self.load_piece("piece_images/black_queen.png")
        self.black_bishop = self.load_piece("piece_images/black_bishop.png")
        self.black_knight = self.load_piece("piece_images/black_knight.png")
        self.black_rook = self.load_piece("piece_images/black_rook.png")
        self.black_pawn = self.load_piece("piece_images/black_pawn.png")
        self.white_king = self.load_piece("piece_images/white_king.png")
        self.white_queen = self.load_piece("piece_images/white_queen.png")
        self.white_bishop = self.load_piece("piece_images/white_bishop.png")
        self.white_knight = self.load_piece("piece_images/white_knight.png")
        self.white_rook = self.load_piece("piece_images/white_rook.png")
        self.white_pawn = self.load_piece("piece_images/white_pawn.png")
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

    def blit_state(self, state: State):
        for rank in range(PAD, 8+PAD):
            for file in range(PAD, 8+PAD):
                piece = state[Square(file, rank)]
                if piece == EMPTY:
                    continue
                elif piece == BLACK_KING:
                    self.place(self.black_king, file, rank)
                elif piece == BLACK_QUEEN:
                    self.place(self.black_queen, file, rank)
                elif piece == BLACK_BISHOP:
                    self.place(self.black_bishop, file, rank)
                elif piece == BLACK_KNIGHT:
                    self.place(self.black_knight, file, rank)
                elif piece == BLACK_ROOK:
                    self.place(self.black_rook, file, rank)
                elif piece == BLACK_PAWN:
                    self.place(self.black_pawn, file, rank)
                elif piece == WHITE_KING:
                    self.place(self.white_king, file, rank)
                elif piece == WHITE_QUEEN:
                    self.place(self.white_queen, file, rank)
                elif piece == WHITE_BISHOP:
                    self.place(self.white_bishop, file, rank)
                elif piece == WHITE_KNIGHT:
                    self.place(self.white_knight, file, rank)
                elif piece == WHITE_ROOK:
                    self.place(self.white_rook, file, rank)
                elif piece == WHITE_PAWN:
                    self.place(self.white_pawn, file, rank)
        if state.is_mate():
            self.place_center(self.mate_overlay)
        elif state.is_stalemate():
            self.place_center(self.stalemate_overlay)

    def blit_moves(self, state: State, square: Square):
        for move in state.generate_moves(square):
            if state[move.end] & state.oppo:
                self.place(self.capture_overlay, move.end.file, move.end.rank)
            else:
                self.place(self.move_overlay, move.end.file, move.end.rank)

    def place(self, surf, file, rank):
        x, y = self.loc(file, rank)
        offset = 3 * self.px_width
        self.screen.blit(surf, (x + offset, y + offset))

    def place_center(self, surf):
        x = 3.5 * self.square_width + 3 * self.px_width
        self.screen.blit(surf, (x, x))

    def loc(self, file, rank):
        file -= PAD
        rank -= PAD
        inverted_rank = 7 - rank
        return np.array([file, inverted_rank]) * self.square_width

    def unloc(self, x, y):
        file, inverted_rank = np.array([x, y]) // self.square_width
        rank = 7 - inverted_rank
        file += PAD
        rank += PAD
        return Square(file, rank)

