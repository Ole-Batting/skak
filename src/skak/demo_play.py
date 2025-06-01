import chess
import pygame

from skak.ui import Ui


def push_if_legal(move: chess.Move, board: chess.Board):
    if board.is_legal(move):
        board.push(move)


def requires_promoting(move: chess.Move, board: chess.Board):
    piece = board.piece_at(move.from_square)
    if piece.piece_type != chess.PAWN:
        return False
    rank_idx = move.to_square // 8
    if board.turn == chess.WHITE:
        return rank_idx == 7
    else:
        return rank_idx == 0


def handle_click(click: chess.Square, stack: list[chess.Square], board: chess.Board):
    piece = board.piece_at(click)

    if len(stack) == 2:
        promotion = None
        match click:
            case chess.D5:
                promotion = chess.QUEEN
            case chess.E5:
                promotion = chess.ROOK
            case chess.D4:
                promotion = chess.BISHOP
            case chess.E4:
                promotion = chess.KNIGHT
        if promotion is not None:
            from_square, to_square = stack
            move = chess.Move(from_square, to_square, promotion)
            push_if_legal(move, board)

    elif piece is not None and piece.color == board.turn:
        return [click]

    elif len(stack) == 1:
        move = chess.Move(stack[0], click)
        if requires_promoting(move, board):
            guinea_pig_move = chess.Move(from_square=stack[0], to_square=click, promotion=chess.QUEEN)
            if board.is_legal(guinea_pig_move):
                return stack + [click]
            else:
                print("heeeell noa")
                print(click, stack)
                print(
                    chess.SQUARE_NAMES[stack[0]],
                    chess.SQUARE_NAMES[click],
                )
                print(guinea_pig_move)
        else:
            push_if_legal(move, board)
    return []


def main() -> None:
    ui = Ui(piece_px=9, square_px=15, px_width=4)
    board = chess.Board()
    running = True
    stack = []

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running=False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                click = ui.unloc(*pygame.mouse.get_pos())
                stack = handle_click(click, stack, board)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and event.mod & pygame.KMOD_CTRL:
                    board = chess.Board()

        ui.reset()
        ui.blit_state(board)
        if len(stack) == 1:
            ui.blit_moves(board, stack[0])
        if len(stack) == 2:
            ui.blit_promotion(board.turn)

        pygame.display.flip()

        ui.clock.tick(60)

    pygame.quit()
