import random

import chess
import pandas as pd


def comment_dumps(d: dict):
    return ";".join([f"{key}={val}" for key, val in d.items()])


def comment_loads(s: str):
    d = dict()
    for elem in s.split(";"):
        key, val = elem.split("=")
        d[key] = val 
    return d


def get_nodes_table(game: chess.pgn.Game) -> pd.DataFrame:
    df = pd.DataFrame(columns=["node", "depth"])
    stack = [game]
    while len(stack) > 0:
        node = stack.pop(0)
        df.loc[-1] = (node, node.ply())
        for child in node.variations:
            stack.append(child)
    return df


def get_lines_stack(node: chess.pgn.GameNode, stack: list[chess.pgn.GameNode]):
    stack.append(node)
    vars = node.variations
    random.shuffle(vars)
    for child in vars:
        get_lines_stack(child, stack)
