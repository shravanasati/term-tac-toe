from dataclasses import dataclass
import random
from typing import Optional

from rich import print
from rich.align import Align
from rich.emoji import Emoji
from rich.panel import Panel
from rich.prompt import Prompt
from rich.style import Style
from rich.table import Table
from rich.text import Text

# emoji constants
TADA_EMOJI = ":tada:"
PENSIVE_FACE_EMOJI = ":pensive_face:"
WHITE_FLAG_EMOJI = ":white_flag:"
QUESTION_MARK_EMOJI = ":white_question_mark:"
CHECK_MARK_EMOJI = ":white_check_mark:"
CROSS_MARK_EMOJI = ":cross_mark:"


class GameplayError(Exception):
    """
    Raised when there's an internal logic error in game.
    """


@dataclass(frozen=True, order=True)
class CheckWinResult:
    victory: bool
    winner: Optional[str] = None
    coordinates: list[tuple[int, int]] = None


class TicTacToe:
    """
    Gameplay class.

    # 0 -> empty
    # 1 -> filled by player1
    # 2 -> filled by player2
    """

    def __init__(self) -> None:
        """
        Constructs the game.
        """
        self.position_to_coordinates = {
            1: (0, 0),
            2: (0, 1),
            3: (0, 2),
            4: (1, 0),
            5: (1, 1),
            6: (1, 2),
            7: (2, 0),
            8: (2, 1),
            9: (2, 2),
        }
        self.coordinates_to_position = {
            v: k for k, v in self.position_to_coordinates.items()
        }
        self.board = self.create_board()

    @staticmethod
    def create_board() -> list[list[int]]:
        """
        Creates the initial board.
        """
        board = []
        for _ in range(3):
            board.append([0, 0, 0])

        return board

    def get_board_row(self, row_number: int) -> list[int]:
        """
        Returns the given row number from the board.
        Requested row number must be between 1 and 3 inclusive.
        """
        if row_number not in range(1, 4):
            raise GameplayError(
                f"Requested get_board_row({row_number}) which is out of bounds. 1 <= row_number <= 3."
            )

        row_number -= 1
        return self.board[row_number]

    def get_board_column(self, col_number: int) -> list[int]:
        """
        Returns the given column number from the board.
        Requested column number must be between 1 and 3 inclusive.
        """
        if col_number not in range(1, 4):
            raise GameplayError(
                f"Requested get_board_column({col_number}) which is out of bounds. 1 <= col_number <= 3."
            )

        col_number -= 1
        requested_column = []
        for row in self.board:
            requested_column.append(row[col_number])

        return requested_column

    def get_board_diagonal(self, diagonal_number: int) -> list[int]:
        """
        Returns the given diagonal number from the board.
        diagonal_number must be 1 for left to right diagonal and -1 for right to left diagonal.
        """
        if diagonal_number == 1:
            board = self.board
            length = len(board)
            return [board[i][i] for i in range(length)]

        elif diagonal_number == -1:
            board = self.board
            length = len(board)
            return [board[i][length - i - 1] for i in range(length)]

        else:
            raise GameplayError(
                f"Requested get_board_diagonal({diagonal_number}) which is out of bounds. Diagonal number belongs to {{-1, 1}}."
            )

    def get_available_spaces(self) -> list[tuple[int, int]]:
        available = []
        for nrow, row in enumerate(self.board):
            for ncol, col in enumerate(row):
                if col == 0:
                    available.append((nrow, ncol))

        if len(available) == 0:
            raise GameplayError(
                "no available places in the board to fill. game should be over by now"
            )

        return available

    def fill_player_space(self, position: int, marker: int) -> bool:
        """
        Fills the board at the given position.

        Position ranges from 1 to 9. Raises an error otherwise.

        marker -> 1: player1, 2: player2

        Returns true if the entered position can be filled.
        """
        if position not in range(1, 10):
            raise GameplayError(
                f"The given position `{position}` is invalid for fill_player_space. The board can only fill spaces on position ranging from 1 to 9 (inclusive). This should be handled by rich input."
            )

        row, column = self.position_to_coordinates.get(position)
        if (row, column) in self.get_available_spaces():
            self.board[row][column] = marker
            return True

        return False

    def check_completion(self) -> bool:
        """
        Checks if the board is filled, to finish the game in case of draw.
        """
        counter = 0
        for row in self.board:
            if row.count(0) == 0:
                counter += 1

        return counter == 3

    def check_win(self) -> CheckWinResult:
        """
        Checks the board vertically, horizontally and diagonally for win.
        """
        # horizontal check
        for i in range(1, 4):
            row = self.get_board_row(i)
            if len(set(row)) == 1 and 0 not in row:
                winner = "computer" if row[0] == 1 else "player"
                return CheckWinResult(
                    victory=True,
                    winner=winner,
                    coordinates=[(i - 1, j) for j in range(0, 3)],
                )

        # vertical check
        for i in range(1, 4):
            column = self.get_board_column(i)
            if len(set(column)) == 1 and 0 not in column:
                winner = "computer" if next(iter(column)) == 1 else "player"
                return CheckWinResult(
                    victory=True,
                    winner=winner,
                    coordinates=[(j, i - 1) for j in range(0, 3)],
                )

        # diagonal check
        for i in range(-1, 2, 2):
            diagonal = self.get_board_diagonal(i)
            diagonal = set(diagonal)
            if len(diagonal) == 1 and 0 not in diagonal:
                winner = "computer" if next(iter(diagonal)) == 1 else "player"

                if i == 1:
                    return CheckWinResult(
                        victory=True,
                        winner=winner,
                        coordinates=[(j, j) for j in range(0, 3)],
                    )
                else:
                    return CheckWinResult(
                        victory=True,
                        winner=winner,
                        coordinates=[(j, 2 - j) for j in range(0, 3)],
                    )

        return CheckWinResult(victory=False)

    def display_board(self, result: Optional[CheckWinResult] = None):
        """
        Prints the current board on the console.

        The result param is optional. Pass it to highlight the row/column/diagonal for winning ref.
        """
        emoji_mappings = {
            0: QUESTION_MARK_EMOJI,  # empty
            1: CROSS_MARK_EMOJI,  # computer
            2: CHECK_MARK_EMOJI,  # user
        }

        t = Table(show_lines=True, show_header=False)
        for i in range(1, 4):
            t.add_column(str(i))

        for nrow, row in enumerate(self.board):
            table_row = list(map(lambda x: emoji_mappings.get(x), row))

            if result and result.coordinates:
                for ncol in range(0, 3):
                    for c in result.coordinates:
                        if c == (nrow, ncol):
                            prev = Text(Emoji.replace(table_row[ncol]))
                            prev.stylize(Style(bgcolor="yellow"))
                            table_row[ncol] = prev

            t.add_row(*table_row)

        print(t)

    def position_input(self) -> int:
        """
        Uses rich to nicely ask the user about position.
        """
        pos = Prompt.ask(
            "Choose position",
            choices=[
                f"{self.coordinates_to_position.get(i)}"
                for i in self.get_available_spaces()
            ],
        )
        return int(pos)

    def game_outcome(self) -> bool:
        result = self.check_win()
        if result.victory:
            self.display_board(result=result)
            if result.winner == "player":
                print(f"[green]{TADA_EMOJI} Congratulations! You win the game. [/]")
            else:
                print(
                    f"[red]{PENSIVE_FACE_EMOJI} Oh no, you lost! Better luck next time.[/]"
                )
            return True

        if self.check_completion():
            self.display_board(result=result)
            print(f"{WHITE_FLAG_EMOJI} It's a draw. Better luck next time.")
            return True

        return False

    def play(self):
        """
        Main game loop.
        """
        starter = "computer" if random.randint(1, 10) % 3 == 0 else "player"
        print(
            f"[cyan bold][underline]{starter.capitalize()}[/] is making the first move.[/]"
        )

        if starter == "computer":
            self.fill_computer_space()

        while True:
            self.display_board()
            pos = self.position_input()

            if not self.fill_player_space(pos):
                raise GameplayError(
                    "This should never happen. Player has entered a position which is impossible to fill because it's either already filled or position is not in range (1 to 9). Rich input should handle this."
                )
            # check if player won
            if self.game_outcome():
                break

            self.fill_computer_space()

            # check if computer won
            if self.game_outcome():
                break


def main():
    panel = Panel(Text("Tic Tac Toe", style="#e5eb34 on #3492eb"), padding=1)
    print(Align(panel, "center"))

    print("[bold blue underline]Before you proceed:[/]")

    print(f"{QUESTION_MARK_EMOJI} -> empty space, can be chosen to place marker")
    print(f"{CROSS_MARK_EMOJI} -> mark filled by computer")
    print(f"{CHECK_MARK_EMOJI} -> mark filled by you, the player \n")

    print("[bold blue underline]Positions:[/]")

    t = Table("a", "b", "c", show_lines=True, show_header=False)
    for i in range(1, 10, 3):
        t.add_row(*[f"{j}" for j in range(i, i + 3)])

    print(t)
    input("Press enter once you've read the instructions.")

    # todo choosing difficulty level here, using Prompt with choices

    game = TicTacToe()
    game.play()


# todo difficulty parameter in the game, so fill_computer_spaces should behave properly


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print("[green]\nbyeee[/]")

    except GameplayError as g:
        print(f"[red]the game developer made a mistake in game logic:\n{g}[/]")

    except Exception as e:
        print(f"[red]fatal error: {e}[/]")
        # todo write traceback to log file