import argparse
from typing import Literal

import chess
import chess.pgn
import tqdm
from stockfish import Stockfish

from skak.lichess import get_lichess_moves, get_lichess_info, PositionInfo
from skak.utils import comment_dumps, comment_loads

SF_DEPTH = 16
SF_N_MOVES = 3
LC_RARITY_MOVE = 80
LC_RARITY_POS = 60
LC_RARITY_MIN = 2 * LC_RARITY_MOVE
LC_RATIO_MOVE = 1/LC_RARITY_MOVE
LC_RATIO_POS = 1/LC_RARITY_POS
LC_RATIO_MIN = 1/LC_RARITY_MIN

sf = Stockfish(
    "/usr/local/Cellar/stockfish/17/bin/stockfish",
    depth=SF_DEPTH,
    parameters={"Threads": 3, "Hash": 4096},
)


def diff_score_sf(fen: str):
    sf.set_fen_position(fen)
    wins, draws, losses = sf.get_wdl_stats()
    return (wins - losses) / (wins + draws + losses)


def diff_score_lc(info, color: chess.Color):
    if info.sum() == 0:
        return 0
    elif color == chess.WHITE:
        return (info.white - info.black) / info.sum()
    else:
        return (info.black - info.white) / info.sum()


def var_factor(a: int, b: int, outer):
    def inner(x):
        return outer(a * x + b)
    return inner


score_sf_factor = var_factor(50, -300, lambda x: min(300, max(0, x)))  # OG: 100, -600, max
score_lc_factor = var_factor(-20, 300, lambda x: max(0, x))  # OG: -20, 250, max
popularity_factor = var_factor(0, 300, lambda x: int(x==2))  # OG: -40, 350, max


def pick_move(
    board: chess.Board,
    pos_info: PositionInfo,
    scale_score_sf: float,
    scale_score_lc: float,
    scale_popularity: float,
):
    fen = board.fen()
    sf.set_fen_position(fen)

    best_eval = None
    best_dict = None

    for res in sf.get_top_moves(SF_N_MOVES):
        var_uci = res["Move"]
        var_move = chess.Move.from_uci(var_uci)

        if res["Mate"]:
            return var_move

        var_board = board.copy()
        var_board.push(var_move)
        var_fen = var_board.fen()
        score_sf = diff_score_sf(var_fen)
        var_info = get_lichess_info(var_fen)
        score_lc = diff_score_lc(var_info, board.turn)
        popularity = var_info.sum() / pos_info.sum()
        color_flip = 1 if board.turn == chess.WHITE else -1
        var_eval = (
            color_flip * res["Centipawn"] 
            + scale_score_sf * score_sf 
            + scale_score_lc * score_lc 
            + scale_popularity * popularity
        )

        if best_eval is None or var_eval > best_eval:
            best_eval = var_eval
            best_dict = dict(
                move=var_move,
                info=var_info,
                cp=res["Centipawn"],
                score_sf=score_sf,
                score_lc=score_lc,
                popularity=popularity,
                eval=var_eval,
            )

    return best_dict


def build(node: chess.pgn.GameNode, ratio:float, max_depth: int, color: chess.Color):
    if 2 * max_depth + int(color == chess.WHITE) == node.ply():
        return

    board = node.board()
    pos_info = get_lichess_moves(board.fen())
    total_games = pos_info.sum()
    fullmove = board.fullmove_number

    if board.turn == color:
        var = pick_move(
            board=board,
            pos_info=pos_info,
            scale_score_sf=score_sf_factor(fullmove),
            scale_score_lc=score_lc_factor(fullmove),
            scale_popularity=popularity_factor(fullmove),
        )
        var_node = node.add_variation(
            var["move"],
            comment=comment_dumps(
                dict(
                    ratio=ratio,
                    opening=var["info"].opening_name(),
                    cp=var["cp"],
                    eval=var["eval"],
                )
            ),
        )
        build(var_node, ratio, max_depth, color)

    else:
        for var_info in tqdm.tqdm(pos_info.moves, desc=str(fullmove), position=fullmove-1, leave=None):
            var_move = chess.Move.from_uci(var_info.uci)
            var_ratio = var_info.sum() / total_games

            if ratio * var_ratio < LC_RATIO_MIN:
                continue
            elif ratio > LC_RATIO_POS and len(node.variations) < 2:
                pass
            elif ratio * var_ratio < LC_RATIO_MOVE:
                continue

            var_node = node.add_variation(
                var_move,
                comment=comment_dumps(dict(ratio=var_ratio * ratio, opening=var_info.opening_name())),
            )
            build(var_node, ratio * var_ratio, max_depth, color)


UD = u'\u2551'
UR = u'\u255a'
LRD = u'\u2566'
URD = u'\u2560'
LR = u'\u2550'


def fraction(ratio: float):
    return round(1 / ratio, 0)


def pad(s=""):
    return s + " "*(6-len(s))


def padsan(san):
    return san + LR*(5-len(san))


def node_san(node: chess.pgn.GameNode):
    if node.move is None:
        return ""
    return node.parent.board().san(node.move)


def viz(node: chess.pgn.GameNode, x, b, linename):
    if x==0:
        print()
    if len(node.variations) == 0:
        meta = comment_loads(node.comment)
        print(
            (
                f"1/{fraction(float(meta["ratio"])):.0f} cp={float(meta["cp"])/100:.2f} "
                f"te:{float(meta["eval"])/100:.2f} {linename}"
            ), 
            end="",
        )
    else:
        for i, child in enumerate(node.variations):
            meta = comment_loads(child.comment)
            next_linename = meta["opening"] or linename
            san = node_san(child)
            if meta["opening"] is None:
                next_linename += f",{san}"
            san = padsan(san)
            if i != 0:
                c = b+(1<<x)
                print("\n", end="")
                for j in range(x + 1):
                    if (c >> j) & 0x1:
                        print(pad(UD), end="")
                    else:
                        print(pad(), end="")
                print()
                for j in range(x):
                    if (c >> j) & 0x1:
                        print(pad(UD), end="")
                    else:
                        print(pad(), end="")
            if len(node.variations) == 1:
                print(f"{LR}{san}", end="")
            elif i == 0:
                print(f"{LRD}{san}", end="")
            elif i == len(node.variations)-1:
                print(f"{UR}{san}", end="")
            else:
                print(f"{URD}{san}", end="")
            viz(child, x+1, b+(int(i!=len(node.variations)-1)<<x), next_linename)
    if x==0:
        print()


def get_num_nodes(node: chess.pgn.GameNode):
    return sum(get_num_nodes(child) for child in node.variations) + 1


def get_num_lines(node: chess.pgn.GameNode):
    if len(node.variations) == 0:
        return 1
    return sum(get_num_lines(child) for child in node.variations)


def get_coverage(node: chess.pgn.GameNode, stat=list()):
    ratio = float(comment_loads(node.comment or 'ratio=1')["ratio"])
    if len(stat) <= node.ply():
        stat.append(ratio)
    else:
        stat[node.ply()] += ratio
    for child in node.variations:
        get_coverage(child, stat)
    return stat


def get_headers(color: str, moves: int) -> dict[str,str]:
    return dict(
        color=color,
        moves=str(moves),
        sf_depth=str(SF_DEPTH),
        sf_n_moves=str(SF_N_MOVES),
        lc_rarity_move=str(LC_RARITY_MOVE),
        lc_rarity_pos=str(LC_RARITY_POS),
        lc_rarity_min=str(LC_RARITY_MIN),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("color", type=str, default="white")
    parser.add_argument("moves", type=int, default=2)
    parser.add_argument("name", type=str, default="tmp")
    args = parser.parse_args()

    game = chess.pgn.Game(headers=get_headers(args.color, args.moves))
    build(game, 1, args.moves, getattr(chess, args.color.upper()))
    viz(game, 0, 0, "")
    print(get_num_nodes(game))
    print(get_num_lines(game))
    stat = get_coverage(game)
    for i, s in enumerate(stat):
        print(f"move {i//2:2d} ply {i:2d} coverage={s:.6f}")

    with open(f"data/{args.name}.pgn", "w") as outfile:
        print(game, file=outfile, end="\n\n")

