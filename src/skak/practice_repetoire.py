import argparse
import os
import time

import chess
import chess.pgn
import pygame

from skak.ui import Ui
from skak.utils import get_lines_stack


def is_move_correct(move: chess.Move, node: chess.pgn.GameNode):
    board = node.board()
    if board.is_legal(move):
        if node.next().move == move:
            return "correct"
        return "incorrect"
    return "illegal"


def requires_promoting(move: chess.Move, board: chess.Board):
    piece = board.piece_at(move.from_square)
    if piece.piece_type != chess.PAWN:
        return False
    rank_idx = move.to_square // 8
    if board.turn == chess.WHITE:
        return rank_idx == 7
    else:
        return rank_idx == 0


def from_square_loop(ui: Ui, board: chess.Board):
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True, None
            elif event.type == pygame.MOUSEBUTTONDOWN:
                from_square = ui.unloc(*pygame.mouse.get_pos())
                piece = board.piece_at(from_square)
                if piece is not None and piece.color == board.turn:
                    quitval, move = to_square_loop(ui, board, from_square)
                    if quitval or move:
                        return quitval, move

        ui.reset()
        ui.blit_state(board)
        pygame.display.flip()
        ui.tick()


def to_square_loop(ui: Ui, board: chess.Board, from_square: chess.Square):
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True, None
            elif event.type == pygame.MOUSEBUTTONDOWN:
                to_square = ui.unloc(*pygame.mouse.get_pos())
                move = chess.Move(from_square=from_square, to_square=to_square)
                if requires_promoting(move, board):
                    move.promotion = chess.QUEEN
                    if board.is_legal(move):
                        quitval, move = promotion_loop(ui, board, move)
                        if quitval or move:
                            return quitval, move
                else:
                    if board.is_legal(move):
                        return False, move
                    return False, None

        ui.reset()
        ui.blit_state(board)
        ui.blit_moves(board, from_square)
        pygame.display.flip()
        ui.tick()


def promotion_loop(ui: Ui, board: chess.Board, move: chess.Move):
    while True:
        for event in pygame.event.get():
            if even.type == pygame.QUIT:
                return True, None
            elif event.type == pygame.MOUSEBUTTONDOWN:
                click = ui.unloc(*pygame.mouse.get_pos())
                match click:
                    case chess.D5:
                        move.promotion = chess.QUEEN
                    case chess.E5:
                        move.promotion = chess.ROOK
                    case chess.D4:
                        move.promotion = chess.BISHOP
                    case chess.E4:
                        move.promotion = chess.KNIGHT
                    case _:
                        return False, None
                return False, move
        ui.reset()
        ui.blit_state(board)
        ui.blit_promotion(board.turn)
        pygame.display.flip()
        ui.tick()


def replay_until_node_loop(ui: Ui, node: chess.pgn.GameNode):
    stack = [node]
    while node.parent:
        node = node.parent
        stack.append(node)
    node = stack.pop()
    board = node.board()
    quitval = False
    while stack:
        node = stack.pop()
        quitval = ui.anim_move(board, node.move)
        if quitval:
            break
        board = node.board()
    return quitval


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("name", type=str, default="tmp")
    args = parser.parse_args()

    assert os.path.exists(f"data/{args.name}.pgn"), "oops"
    with open(f"data/{args.name}.pgn") as pgn:
        game = chess.pgn.read_game(pgn)
    lines_stack = []
    get_lines_stack(game, lines_stack)
    lines_stack = [(elem, False) for elem in lines_stack]
    print(len(lines_stack))
    color = getattr(chess, game.headers["color"].upper())
    node, is_retry = lines_stack.pop(0)
    board = node.board()

    ui = Ui(piece_px=9, square_px=15, px_width=4, orientation=color)

    while True:
        if color == board.turn:
            quitval, move = from_square_loop(ui, board)
            if quitval:
                break
            retval = is_move_correct(move, node)
            if retval == "correct":
                if len(lines_stack) == 0:
                    break
                next_node, is_retry = lines_stack.pop(0)
                if node.is_end() or is_retry:
                    print("yankie")
                    if ui.idle():
                        break
                    if replay_until_node_loop(ui, next_node):
                        break
                else:
                    if ui.anim_move(board, next_node.move):
                        break
                node = next_node
                board = node.board()
            elif node not in lines_stack:
                lines_stack.append((node, True))
            print(retval, len(lines_stack))
        else:
            if len(lines_stack) == 0:
                break
            next_node, is_retry = lines_stack.pop(0)
            if node.is_end() or is_retry:
                print("oscar")
                if ui.idle():
                    break
                if replay_until_node_loop(ui, next_node):
                    break
            else:
                if ui.anim_move(board, next_node.move):
                    break
            print('oppo', len(lines_stack))
            node = next_node
            board = node.board()

        ui.reset()
        ui.blit_state(board)
        pygame.display.flip()
        ui.tick()
    pygame.quit()
