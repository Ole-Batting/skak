import pygame

from skak.bitmap import State, WHITE, BLACK
from skak.ui import Board


board = Board(piece_px=9, square_px=15, px_width=4)
old_state = None
state = State()
running = True
start_square = None


def is_mine(state, square):
    return (
        state.whites_turn and state.piece_on_square[square] & WHITE or
        not state.whites_turn and state.piece_on_square[square] & BLACK
    )


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            square = board.unloc(*pygame.mouse.get_pos())
            if is_mine(state, square):
                start_square = square
            elif start_square is not None:
                if state.check_move(start_square, square):
                    state.move(start_square, square)
                start_square = None
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and event.mod & pygame.KMOD_CTRL:
                old_state = state
                state = State()
            elif event.key == pygame.K_s and event.mod & pygame.KMOD_CTRL:
                tmp_state = state
                state = old_state
                old_state = tmp_state
            elif event.key == pygame.K_b:
                state.bitboard_show()
            elif event.key == pygame.K_p:
                state.piecelist_show()
            elif event.key == pygame.K_o:
                state.piece_on_square_show()

    board.reset()
    board.blit_state(state)
    # if start_square is not None:
    #     board.blit_moves(state, clicked_square)

    pygame.display.flip()

    board.clock.tick(60)

pygame.quit()
