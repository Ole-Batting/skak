import pygame

from skak.v1.state import State, Move, FILE_D, FILE_E, RANK_4, RANK_5, QUEEN, ROOK, BISHOP, KNIGHT
from skak.v1.ui import Ui


ui = Ui(piece_px=9, square_px=15, px_width=4)
old_state = None
state = State()
running = True
clicked_square = None
promoting_move = None

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            click = ui.unloc(*pygame.mouse.get_pos())
            if promoting_move is not None:
                if FILE_D <= click.file <= FILE_E and RANK_4 <= click.rank <= RANK_5:
                    if click.file == FILE_D and click.rank == RANK_5:
                        promoting_move.promote = state.mine | QUEEN
                    elif click.file == FILE_E and click.rank == RANK_5:
                        promoting_move.promote = state.mine | ROOK
                    elif click.file == FILE_D:
                        promoting_move.promote = state.mine | BISHOP
                    else:
                        promoting_move.promote = state.mine | KNIGHT
                    state.move(promoting_move)
                promoting_move = None
            elif state.is_mine(click):
                clicked_square = click
            elif clicked_square is not None:
                move = Move(clicked_square, click)
                if state.check_move(move):
                    state.move(move)
                    print(state)
                elif state.move_must_promote(move):
                    promoting_move = move
                    promoting_move.promote = state.mine | QUEEN
                    if state.check_move(promoting_move):
                        promoting_move.promote = None
                    else:
                        promoting_move = None
                clicked_square = None
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and event.mod & pygame.KMOD_CTRL:
                old_state = state
                state = State()
            if event.key == pygame.K_s and event.mod & pygame.KMOD_CTRL:
                tmp_state = state
                state = old_state
                old_state = tmp_state

    ui.reset()
    ui.blit_state(state)
    if clicked_square is not None:
        ui.blit_moves(state, clicked_square)
    if promoting_move is not None:
        ui.blit_promotion(state.whites_turn)

    pygame.display.flip()

    ui.clock.tick(60)

pygame.quit()
