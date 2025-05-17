import os
import time

import requests
from pydantic import BaseModel
from stockfish import Stockfish
from tqdm import tqdm

from skak.v1.state import State, Move, WHITE, BLACK
from skak.v1.carver import viz, viz2, fraction


PGN_DEPTH = 9 #19
SF_DEPTH = 16 #18
SF_N_TOP = 3
LC_N_TOP = 6 #12
LC_RARITY_A = 80 #100
LC_PREVALENCE_A = 1/LC_RARITY_A
LC_RARITY_B = 40 #60
LC_PREVALENCE_B = 1/LC_RARITY_B


sf = Stockfish(
    "/usr/local/Cellar/stockfish/17/bin/stockfish",
    depth=SF_DEPTH,
    parameters={"Threads": 3, "Hash": 4096},
)


class PlayerInfo(BaseModel):
    name: str
    rating: int


class GameInfo(BaseModel):
    id: str
    winner: str
    black: PlayerInfo
    white: PlayerInfo
    year: int
    month: str


class OpeningInfo(BaseModel):
    eco: str
    name: str


class MoveInfo(BaseModel):
    uci: str
    san: str
    averageRating: int
    white: int
    draws: int
    black: int
    game: GameInfo | None
    opening: OpeningInfo | None


class PositionInfo(BaseModel):
    opening: OpeningInfo | None
    white: int
    draws: int
    black: int
    moves: list[MoveInfo]


def _get_lichess_(endpoint: str, params: dict, response_model: BaseModel):
    for retry in range(3):
        response = requests.get(
            endpoint,
            params=params,
            headers=dict(Authorization=f"Bearer {os.getenv("LICHESS_API_TOKEN")}"),
        )
        if response.status_code == 200:
            return response_model.model_validate(response.json())
        elif response.status_code == 429:
            print("sleeping for rate limit")
            time.sleep(61)
            continue
        else:
            raise ValueError(f"{response.status_code} status code not handled")


def get_lichess_moves(fen: str):
    return _get_lichess_(
        endpoint="https://explorer.lichess.ovh/lichess",
        params=dict(
            variant="standard",
            fen=fen,
            speeds="blitz,rapid,classical",
            ratings="1200,1400,1600",
            moves=LC_N_TOP,
            topGames=0,
            recentGames=0,
        ),
        response_model=PositionInfo,
    )


def build(max_depth: int):
    state = State()
    return _build(state, 1, 0, max_depth)


def possum(obj):
    return obj.white + obj.draws + obj.black


def opename(obj):
    if obj.opening:
        return obj.opening.name
    return None


class TreeNode(BaseModel):
    fen: str
    opening_name: str | None
    ratio: float
    children: dict[str, tuple[str, int, 'TreeNode']]


# TODO: refactor to avoid tuples in the tree and use the models directly
def _build(state: State, ratio: float, depth: int, max_depth: int):
    fen = repr(state)
    posinfo = get_lichess_moves(fen)
    if depth == max_depth:
        return TreeNode(fen=fen, opening_name=opename(posinfo), ratio=ratio, children={})
    sum_games = possum(posinfo)
    out = {}
    if state.whites_turn:
        move_lan, _ = pick_move(
            state=state,
            posinfo=posinfo,
            lc_wdb_stats=max(0, 250 - 20 * state.fullmovecounter),
            lc_popularity=max(0, 350 - 40 * state.fullmovecounter),
            sf_top_moves=max(0, 100 * state.fullmovecounter - 300),
            sf_wdb_stats=max(0, 100 * state.fullmovecounter - 600),
        )
        move_state = state.copy()
        move_state.move(Move.from_lan(move_lan, move_state.whites_turn))
        move_san = state.to_san(move_lan)
        out[move_lan] = (
            move_san,
            WHITE if state.whites_turn else BLACK,
            _build(move_state, ratio, depth+1, max_depth),
        )
    else:
        for move in tqdm(posinfo.moves, desc=str(depth//2), position=depth//2, leave=None):
            move_state = state.copy()
            move_state.move(Move.from_lan(move.uci, move_state.whites_turn))
            move_ratio = possum(move) / sum_games
            if ratio > LC_PREVALENCE_B and len(out) < 2:
                pass
            elif ratio * move_ratio < LC_PREVALENCE_A:
                continue
            out[move.uci] = (
                move.san,
                WHITE if state.whites_turn else BLACK,
                _build(move_state, ratio*move_ratio, depth+1, max_depth),
            )
    return TreeNode(fen=fen, opening_name=opename(posinfo), ratio=ratio, children=out)


class TreeNode2(BaseModel):
    fen: str
    san: str
    opening_name: str | None
    engine_eval: int | None
    average_rating: int | None
    ratio: float
    children: dict[str, 'TreeNode2']


def build2(max_depth: int):
    state = State()
    root = TreeNode2(
        fen=repr(state),
        san="",
        opening_name=None,
        engine_eval=None,
        average_rating=None,
        ratio=1,
        children={},
    )
    _build2(root, state, 1, 0, max_depth)
    return root


def _build2(node: TreeNode2, state: State, ratio: float, depth: int, max_depth: int):
    if depth == max_depth:
        return node
    posinfo = get_lichess_moves(repr(state))
    totalgames = possum(posinfo)
    if state.whites_turn:
        move_lan, move_info = pick_move(
            state=state,
            posinfo=posinfo,
            lc_wdb_stats=max(0, 250 - 20 * state.fullmovecounter),
            lc_popularity=max(0, 350 - 40 * state.fullmovecounter),
            sf_top_moves=max(0, 100 * state.fullmovecounter - 300),
            sf_wdb_stats=max(0, 100 * state.fullmovecounter - 600),
        )
        move_state = state.copy()
        move_state.move(Move.from_lan(move_lan, move_state.whites_turn))
        move_san = state.to_san(move_lan)
        move_node = TreeNode2(
            fen=repr(move_state),
            san=move_san,
            opening_name=opename(move_info) if move_info is not None else None,
            engine_eval=None,
            average_rating=None,
            ratio=ratio,
            children={},
        )
        node.children[move_lan] = move_node
        _build2(move_node, move_state, ratio, depth+1, max_depth)
    else:
        for move in tqdm(posinfo.moves, desc=str(depth//2), position=depth//2, leave=None):
            move_state = state.copy()
            move_state.move(Move.from_lan(move.uci, move_state.whites_turn))
            move_ratio = possum(move) / totalgames
            if ratio > LC_PREVALENCE_B and len(node.children) < 2:
                pass
            elif ratio * move_ratio < LC_PREVALENCE_A:
                continue
            move_node = TreeNode2(
                fen=repr(move_state),
                san=state.to_san(move.uci),
                opening_name=opename(move),
                engine_eval=None,
                average_rating=None,
                ratio=ratio * move_ratio,
                children={},
            )
            node.children[move.uci] = move_node
            _build2(move_node, move_state, ratio * move_ratio, depth+1, max_depth)


def white_draws_black_sf(state: State):
    sf.set_fen_position(repr(state))
    wins, draws, losses = sf.get_wdl_stats()
    if state.whites_turn:
        return wins, draws, losses
    else:
        return losses, draws, wins


def white_draws_black_lc(move_lan: str, posinfo: PositionInfo):
    for moveinfo in posinfo.moves:
        if move_lan == moveinfo.uci:
            return moveinfo.white, moveinfo.draws, moveinfo.black
    return 1, 1, 1


def pick_move(
    state: State,
    posinfo: PositionInfo,
    lc_wdb_stats: int,
    lc_popularity: int,
    sf_top_moves: int,
    sf_wdb_stats: int,
) -> MoveInfo:
    fen = repr(state)
    assert sf.is_fen_valid(fen)
    sf.set_fen_position(fen)

    centipawns = {}
    stats = {}
    moveinfodict = {}

    if (lc_wdb_stats + lc_popularity) > 0:
        sum_games = possum(posinfo)
        for moveinfo in posinfo.moves:
            move_lan = moveinfo.uci
            white, draws, black = white_draws_black_lc(move_lan, posinfo)
            stats[move_lan] = {}
            stats[move_lan]["wdb_lc"] = (white, draws, black)
            moveinfodict[move_lan] = moveinfo

            if lc_wdb_stats > 0:
                ratio = (white - black) / (white + draws + black)
                stats[move_lan]["ratio_lc"] = ratio
                centipawns[move_lan] = lc_wdb_stats * ratio

            if lc_popularity > 0:
                popularity = (white + draws + black) / sum_games
                stats[move_lan]["popularity"] = popularity
                centipawns[move_lan] = lc_popularity * popularity

    if (sf_top_moves + sf_wdb_stats) > 0:
        for result in sf.get_top_moves(SF_N_TOP):
            move_lan = result["Move"]
            

            if result["Mate"]:
                return move_lan

            if move_lan not in centipawns:
                centipawns[move_lan] = 0
                stats[move_lan] = {}

            if sf_top_moves > 0:
                centipawns[move_lan] += result["Centipawn"]
                stats[move_lan]["centi"] = result["Centipawn"]

            if sf_wdb_stats:
                move_state = state.copy()
                move_state.move(Move.from_lan(move_lan, move_state.whites_turn))
                white, draws, black = white_draws_black_sf(move_state)
                stats[move_lan]["wdb_sf"] = (white, draws, black)
                ratio = (white - black) / (white + draws + black)
                stats[move_lan]["ratio_sf"] = ratio
                centipawns[move_lan] += sf_wdb_stats * ratio

    if state.whites_turn:
        best_move_lan = max(centipawns, key=centipawns.get)
    else:
        best_move_lan = min(centipawns, key=centipawns.get)

    return best_move_lan, moveinfodict.get(best_move_lan, None)


def count_moves_in_tree(tree):
    if len(tree.children) == 0:
        return 1
    return sum(count_moves_in_tree(child) for _, _, child in tree.children.values()) + 1


def count_moves_in_tree2(tree):
    if len(tree.children) == 0:
        return 1
    return sum(count_moves_in_tree2(child) for child in tree.children.values()) + 1


def count_lines_in_tree(tree):
    if len(tree.children) == 0:
        return 1
    return sum(count_lines_in_tree(child) for _, _, child in tree.children.values())


def count_lines_in_tree2(tree):
    if len(tree.children) == 0:
        return 1
    return sum(count_lines_in_tree2(child) for child in tree.children.values())


def get_coverage(tree, depth=0, stat=list()):
    if len(stat) <= depth:
        stat.append(tree.ratio)
    else:
        stat[depth] += tree.ratio
    for _, _, child in tree.children.values():
        get_coverage(child, depth+1, stat)
    return stat


def get_coverage2(tree, depth=0, stat=list()):
    if len(stat) <= depth:
        stat.append(tree.ratio)
    else:
        stat[depth] += tree.ratio
    for child in tree.children.values():
        get_coverage2(child, depth+1, stat)
    return stat


def generate_pgn(tree, ply=0, mainline=True):
    if not tree.children:
        return ""
    move_number = 1 + (ply // 2)
    pgn = ""
    first = True
    first_child = None
    for san, color, child in tree.children.values():
        prefix = ""
        if color == WHITE:
            prefix = f"{move_number}. "
        else:
            prefix = f"{move_number}... "
        if first:
            pgn += prefix + san
            first = False
            first_child = child
        else:
            pgn += f" ({prefix}{san} " + generate_pgn(child, ply+1, mainline=False) + ")"
    pgn += " " + generate_pgn(first_child, ply+1) if tree.children else ""
    return pgn.strip()



def save_as_pgn(tree, tag: str = ""):
    pgn = generate_pgn(tree)
    with open(f"repetoire{tag}_d{PGN_DEPTH}_sf:d{SF_DEPTH},n{SF_N_TOP}_lc:n{LC_N_TOP},a{LC_RARITY_A},b{LC_RARITY_B}.pgn", "w") as outfile:
        outfile.write(pgn)


def load_pgn_to_tree(filepath):
    with open(filepath, 'r') as infile:
        pass


if __name__ == "__main__":
    tree = build(PGN_DEPTH)
    viz(tree)
    print(count_moves_in_tree(tree))
    print(count_lines_in_tree(tree))
    stat = get_coverage(tree)
    for i, s in enumerate(stat):
        print(f"move {i//2:2d} ply {i:2d} coverage={s:.3f}")
    # save_as_pgn(tree)

    tree = build2(PGN_DEPTH)
    viz2(tree)
    print(count_moves_in_tree2(tree))
    print(count_lines_in_tree2(tree))
    stat = get_coverage2(tree)
    for i, s in enumerate(stat):
        print(f"move {i//2:2d} ply {i:2d} coverage={s:.3f}")
    # save_as_pgn(tree)
