import pygame

from skak.game_state import State, Move
from skak.ui_board import Board


board = Board(piece_px=9, square_px=15, px_width=4)
old_state = None
state = State()
running = True
clicked_square = None


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            click = board.unloc(*pygame.mouse.get_pos())
            if state.is_mine(click):
                clicked_square = click
            elif clicked_square is not None:
                move = Move(clicked_square, click)
                if state.check_move(move):
                    state.move(move)
                    print(state)
                clicked_square = None
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and event.mod & pygame.KMOD_CTRL:
                old_state = state
                state = State()
            if event.key == pygame.K_s and event.mod & pygame.KMOD_CTRL:
                tmp_state = state
                state = old_state
                old_state = tmp_state

    board.reset()
    board.blit_state(state)
    if clicked_square is not None:
        board.blit_moves(state, clicked_square)

    pygame.display.flip()

    board.clock.tick(60)

pygame.quit()
