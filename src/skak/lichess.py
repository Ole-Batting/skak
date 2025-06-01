import os
import time

import requests
from pydantic import BaseModel


LC_N_MOVES = 12


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


class WdbMixin(BaseModel):
    white: int
    draws: int
    black: int

    def sum(self) -> int:
        return self.white + self.draws + self.black


class OpeningMixin(BaseModel):
    opening: OpeningInfo | None

    def opening_name(self) -> str:
        if self.opening:
            return self.opening.name
        return ""

class MoveInfo(WdbMixin, OpeningMixin):
    uci: str
    san: str
    averageRating: int
    game: GameInfo | None
    opening: OpeningInfo | None


class PositionInfo(WdbMixin, OpeningMixin):
    opening: OpeningInfo | None
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
            ratings="1000,1200,1400",
            moves=LC_N_MOVES,
            topGames=0,
            recentGames=0,
        ),
        response_model=PositionInfo,
    )


def get_lichess_info(fen: str):
    return _get_lichess_(
        endpoint="https://explorer.lichess.ovh/lichess",
        params=dict(
            variant="standard",
            fen=fen,
            speeds="blitz,rapid,classical",
            ratings="1000,1200,1400",
            moves=0,
            topGames=0,
            recentGames=0,
        ),
        response_model=PositionInfo,
    )
