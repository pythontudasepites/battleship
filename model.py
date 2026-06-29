from dataclasses import dataclass
from enum import StrEnum, auto
from itertools import product
from random import randint, choice
from typing import Iterator


@dataclass(frozen=True)
class Cell:
    row: int
    column: int

    def __add__(self, t: tuple[int, int]) -> Cell:
        return Cell(self.row + t[0], self.column + t[1])


class ShotResult(StrEnum):
    HIT = auto()
    MISS = auto()
    SUNK = auto()


class GamePhase(StrEnum):
    PLACEMENT = auto()
    BATTLE = auto()
    VICTORY = auto()


class Winner(StrEnum):
    HUMAN = auto()
    COMPUTER = auto()


class InvalidShipShape(ValueError):
    pass


class ShipOverlapError(ValueError):
    pass


class Board:
    """A játékosok tábláját modellezi."""

    def __init__(self, size: int, ship_sizes: tuple[int, ...]) -> None:
        self.size = size  # A tábla sorainak és oszlopainak száma.
        self.ship_sizes = ship_sizes  # A táblán elhelyezendő hajók méretei.
        self._remaining_ship_sizes = list(self.ship_sizes)  # A még fennmaradó elhelyezendő hajóméretek.
        self._ships: list[Ship] = []  # A táblán elhelyezett hajók.
        self.shots_received: set[Cell] = set()  # A tábla valamely cellájára már leadott lövések coordinátáit tárolja.

    def __contains__(self, cell: Cell) -> bool:
        """True értékkel tér vissza, ha a megadott cellát a tábla tartalmazza."""
        return 0 <= cell.row < self.size and 0 <= cell.column < self.size

    def __iter__(self) -> Iterator[Ship]:
        """Egymás után kiadja a táblán elhelyzetett hajókat."""
        yield from self._ships

    def add_ship(self, ship: Ship):
        """Eltárolja a megadott hajót amennyiben a hajótest nincs átfedésben más, korábban elhelyezett hajóval.
        A hajó méretét kiveszi a még elhelyezendő hajóméretek közül."""
        if not ship.can_be_placed_on(self):
            raise ShipOverlapError("The ship overlaps with an already placed ship.")

        if self._remaining_ship_sizes:
            self._ships.append(ship)
            self._remaining_ship_sizes.remove(ship.size)

    def get_cells(self) -> set[Cell]:
        return {Cell(row_index, column_index) for row_index, column_index in product(range(self.size), repeat=2)}

    def get_cells_available_to_target(self) -> set[Cell]:
        """Azon cellákat adja vissza, amelyek nem azonosak az elsüllyedt hajók effectíven elfoglalt celláival."""
        return self.get_cells() - {cell for sunken_ship in self.get_sunken_ships()
                                   for cell in sunken_ship.get_occupied_area()}

    def get_ship(self, cell: Cell) -> Ship | None:
        """Az adott cellát tartalmazó hajót adja vissza. Ha nincs ilyen hajó, akkor None-t."""
        return next((ship for ship in self if cell in ship), None)

    def get_sunken_ships(self) -> set[Ship]:
        return {ship for ship in self if ship.is_sunk()}

    def process_shot(self, target_cell: Cell) -> ShotResult:
        """Visszaadja a játéktábla adott cellájára irányuló lövés eredményét."""

        self.shots_received.add(target_cell)

        ship = self.get_ship(target_cell)
        if ship is not None:
            return ship.evaluate_shot(target_cell)

        return ShotResult.MISS

    def all_ships_sunk(self) -> bool:
        """True értékkel tér vissza, ha a játéktáblán minden hajó elsüllyedt."""
        return all(ship.is_sunk() for ship in self)

    def all_ships_placed(self) -> bool:
        """True értékkel tér vissza, ha minden hajó le lett helyezve a játéktáblára."""
        return not self._remaining_ship_sizes


class Ship:
    """A hajót modellező osztály."""

    def __init__(self, cells: set[Cell]):
        if not self.valid_ship_shape(cells):
            raise InvalidShipShape('A megadott cellákból nem lehet hajót készíteni.')

        # A hajót alkotó cellák, amikhez rendelt True érték azt jelzi, hogy az a hajórész találatot kapott.
        self._cells_with_hit_states: dict[Cell, bool] = {cell: False for cell in cells}

    def __repr__(self) -> str:
        return f'{type(self).__name__}({set(self._cells_with_hit_states)})'

    def __str__(self) -> str:
        coords = {(c.row, c.column) for c in self._cells_with_hit_states.keys()}
        return f'{type(self).__name__}({coords})'

    def __contains__(self, cell: Cell) -> bool:
        """True értékkel tér vissza, ha a megadott cella a hajó által lefedett."""
        return cell in self._cells_with_hit_states

    @property
    def size(self) -> int:
        return len(self._cells_with_hit_states)

    @property
    def cells(self) -> set[Cell]:
        return set(self._cells_with_hit_states.keys())

    def get_occupied_area(self) -> set[Cell]:
        return self._cells_with_hit_states.keys() | self._get_buffer_cells()

    def has_cells(self, *cells: Cell) -> bool:
        """True értékkel tér vissza, ha a cellák a hajó által lefedettek."""
        return set(cells) <= self._cells_with_hit_states.keys()

    @staticmethod
    def valid_ship_shape(cells: set[Cell]) -> bool:
        """Ellenőrzi, hogy a cellák vizszintes vagy függőleges elrendezésűek-e és hézagmentesen egymást követik."""
        if not cells:
            return False
        rows = {cell.row for cell in cells}
        cols = {cell.column for cell in cells}

        is_horizontal = len(rows) == 1  # A viszintes elrendezés feltétele: minden cella sorindexe azonos
        is_vertical = len(cols) == 1  # A függőleges elrendezés feltétele: minden cella oszlopindexe azonos

        if is_horizontal:
            return max(cols) - min(cols) + 1 == len(cols)  # Az oszlopindexek számtani sorozatot alkotnak.
        if is_vertical:
            return max(rows) - min(rows) + 1 == len(rows)  # # A sorindexek számtani sorozatot alkotnak.
        return False

    def _get_buffer_cells(self) -> set[Cell]:
        """Visszaadja a hajó puffercelláit. Puffercellák azok a cellák a hajó körül, amelyeken nem szabad, hogy
        egy másik hajó része legyen.
        """
        buffer_cells = set()
        for cell in self._cells_with_hit_states:
            for shift in [(-1, -1), (0, -1), (+1, -1), (+1, 0),
                          (+1, +1), (0, +1), (-1, +1), (-1, 0)]:
                neighbor = cell + shift
                if neighbor not in self._cells_with_hit_states:
                    buffer_cells.add(neighbor)
        return buffer_cells

    def can_be_placed_on(self, board: Board) -> bool:
        """True értékkel tér vissza, ha a hajó lehelyezhető a táblára, azaz nincs átfedésben más, korábban
        elhelyezett hajóval.
        """
        return (all(cell in board for cell in self._cells_with_hit_states)
                and not any(self.is_overlapped(_ship) for _ship in board))

    def evaluate_shot(self, target_cell: Cell) -> ShotResult:
        """Kiértékeli, hogy a hajóra leadott lövés talált-e vagy sem. Ha talált a hajó elsüllyedt-e."""
        if target_cell not in self._cells_with_hit_states:
            return ShotResult.MISS
        self._cells_with_hit_states[target_cell] = True
        return ShotResult.SUNK if self.is_sunk() else ShotResult.HIT

    def cell_is_damaged(self, cell: Cell) -> bool:
        """True értékkel tér vissza, ha a megadott cellával azonosított hajórész találatot kapott."""
        return False if cell not in self._cells_with_hit_states else self._cells_with_hit_states[cell]

    def is_sunk(self) -> bool:
        """True értékkel tér vissza, ha a hajó elsüllyedt."""
        return all(self._cells_with_hit_states.values())

    def is_overlapped(self, ship: Ship) -> bool:
        """Visszatérési értéke True, ha a self törzsét alkotó egy vagy több cellája megegyezik a ship hajótestet alkotó vagy
        pufferzóna celláival. Más szóval, ha a self részben vagy egészben érintkezik vagy átfedésben van a ship példánnyal.
        """
        return bool(self._cells_with_hit_states.keys() & ship._cells_with_hit_states.keys() or
                    self._cells_with_hit_states.keys() & ship._get_buffer_cells())


class ComputerFleetFactory:
    """A gépi játékos hajóinak előállításáért felelős osztály."""

    def __init__(self, computer_board: Board):
        self.board = computer_board

    def _create_ship_cells(self, ship_size: int) -> set[Cell]:
        """Véletlenszerűen létrehozza egy vízszintes vagy függőleges helyzetű, adott méretű hajó celláit a
        játéktábla méretein belül.
        """
        horizontal = choice([True, False])

        if horizontal:
            row_index = randint(0, self.board.size - 1)
            col_index = randint(0, self.board.size - ship_size)  # Balról az első cella oszlopindexe.
            return {Cell(row_index, col_index + i) for i in range(ship_size)}
        else:
            row_index = randint(0, self.board.size - ship_size)  # Fentről az első cella sorindexe.
            col_index = randint(0, self.board.size - 1)
            return {Cell(row_index + i, col_index) for i in range(ship_size)}

    def produce_ships(self) -> None:
        """Létrehozza a teljes flotta hajóit elhelyezve a táblán."""
        for ship_size in self.board.ship_sizes:
            placed = False
            while not placed:
                cells = self._create_ship_cells(ship_size)
                ship = Ship(cells)
                try:
                    self.board.add_ship(ship)
                except ShipOverlapError:
                    continue  # Ütközés esetén újra próbálkozunk.
                else:
                    placed = True  # Sikeres elhelyezés.


class ComputerPlayer:
    """Gépi játékos, ami a hajókat véletlenszerűen elhelyezi és leadja a lövéseket az ellenfél játéktáblájára."""

    def __init__(self, computer_board: Board):
        self.computer_board = computer_board
        self._human_ship_damaged_cells: list[Cell] = []
        self._cells_already_shot: set[Cell] = set()

    def place_ships(self):
        factory = ComputerFleetFactory(self.computer_board)
        factory.produce_ships()

    def shoot(self, human_board: Board) -> tuple[ShotResult, set[Cell]]:
        """Véletlenszerű célpont választás a humán játékos tábláján, ami nem ismétli ugyanazt a cellát.
        Ha sikerül egy hajót eltalálni, akkor a további lövések az eltalált hajó elsüllyesztéséig tartanak, és csak
        utána lesz egy új célpont megint véletlenszerű.
        """
        # Ha nincs még eltalált cella, akkor véletlenszerűen választunk célpontot, egyébként pedig az eltalált hajóra
        # lövünk mindaddig, amíg el nem süllyed.
        if not self._human_ship_damaged_cells:
            # Célcella véletlenszerű kiválasztása, ami nem lehet egy már korábbi.
            target_cell = self._choose_random_target_cell(human_board)
        else:
            target_cell = self._choose_target_cell_to_sink(human_board)

        shot_result = human_board.process_shot(target_cell)

        if shot_result == ShotResult.HIT:
            self._human_ship_damaged_cells.append(target_cell)
        if shot_result == ShotResult.SUNK:
            self._human_ship_damaged_cells.clear()

        affected_cells = set()
        if shot_result == ShotResult.MISS or shot_result == ShotResult.HIT:
            affected_cells = {target_cell}
        elif shot_result == ShotResult.SUNK:
            ship = human_board.get_ship(target_cell)
            assert ship is not None  # Ha a hajó elsüllyedt, akkor a target_cell biztosan egy hajó része.
            affected_cells = set(ship.cells)

        return shot_result, affected_cells

    @staticmethod
    def _choose_random_target_cell(human_board: Board) -> Cell:
        """Véletlenszerű célpont választása az emberi játékos tábláján, ami nem ismétli ugyanazt a cellát.
        A célpont olyan cella sem lesz, amely a már elsüllyedt hajók foglalt területére esik.
        """
        target_cell = choice(list(human_board.get_cells_available_to_target() - human_board.shots_received))
        return target_cell

    def _choose_target_cell_to_sink(self, human_board: Board) -> Cell:
        """Célpont választása az emberi játékos tábláján úgy, hogy ha eltalált egy hajót, akkor a következő
        célpontok úgy lesznek meghatározva, hogy a hajó elsüllyedjen.
        """
        potential_target_cells: tuple[Cell, ...] = ()

        if len(self._human_ship_damaged_cells) == 1:
            # Ha még csak egy céllát ért találat, akkor a következő célpont az oldalakkal szomszédos négy cella
            # valamelyike lehet.
            left_cell, right_cell = self._human_ship_damaged_cells[0] + (-1, 0), self._human_ship_damaged_cells[0] + (+1, 0)
            top_cell, bottom_cell = self._human_ship_damaged_cells[0] + (0, -1), self._human_ship_damaged_cells[0] + (0, +1)
            potential_target_cells = (left_cell, right_cell, top_cell, bottom_cell)

        elif len(self._human_ship_damaged_cells) > 1:
            # Ha egynél több cellát ért találat, akkor a következő célpont a vízszitesen vagy függőlegesen
            # egymás mellett levő cellák két végponti oldalával szomszédos két cella valamelyike lehet.

            if len({cell.row for cell in self._human_ship_damaged_cells}) == 1:
                # Vízszintes cellák esetén a bal és jobb végek melleti cellákra kell lőni.
                left_cell = min(self._human_ship_damaged_cells, key=lambda c: c.column) + (0, -1)
                right_cell = max(self._human_ship_damaged_cells, key=lambda c: c.column) + (0, +1)
                potential_target_cells = (left_cell, right_cell)

            elif len({cell.column for cell in self._human_ship_damaged_cells}) == 1:
                # Függőleges cellák esetén a felső és alsó végek melleti cellákra kell lőni.
                top_cell = min(self._human_ship_damaged_cells, key=lambda c: c.row) + (-1, 0)
                bottom_cell = max(self._human_ship_damaged_cells, key=lambda c: c.row) + (+1, 0)
                potential_target_cells = (top_cell, bottom_cell)

        # A célpontként szóbajöhető cellák a játéktáblán kell, hogy legyenek.
        selectable_cells = [cell for cell in potential_target_cells if cell in human_board]

        while True:
            target_cell = choice(selectable_cells)
            if target_cell not in human_board.shots_received:
                return target_cell


class HumanFleetFactory:
    """Az emberi játékos hajóinak előállításáért felelős osztály."""
    def __init__(self, human_board: Board):
        self.board = human_board
        self.ship_sizes_to_build = list(self.board.ship_sizes)
        self.current_ship_size_to_build: int = self.ship_sizes_to_build[0]

        self._selected_human_ship_cells: list[Cell] = []

    def assemble_ship(self, cell: Cell) -> tuple[bool, bool]:
        if cell in self._selected_human_ship_cells:
            return False, False

        cell_is_ship_body, ship_completed = False, False

        if not self.board.all_ships_placed():
            self._selected_human_ship_cells.append(cell)
            self.current_ship_size_to_build = self.ship_sizes_to_build[0]

            alowed_cells = self._get_possible_human_ship_cells(self.current_ship_size_to_build,
                                                               *self._selected_human_ship_cells)

            if any(cell in _cells for _cells in alowed_cells):
                cell_is_ship_body = True
                if len(self._selected_human_ship_cells) == self.current_ship_size_to_build:
                    self.board.add_ship(Ship(set(self._selected_human_ship_cells)))
                    ship_completed = True
                    self._selected_human_ship_cells.clear()
                    self.ship_sizes_to_build.pop(0)

            else:
                self._selected_human_ship_cells.pop()

        return cell_is_ship_body, ship_completed

    def _get_possible_human_ship_cells(self, size: int, *cells: Cell) -> tuple[set[Cell], ...]:
        """Visszaadja az összes adott méretű lehelyezhető hajó celláit, amelyek tartalmazzák a megadott cellákat."""
        r0, c0 = cells[0].row, cells[0].column
        # Összes lehetséges vízszintesen elhelyezhető hajó, amely tartalmazza a megadottak közül az első cellát.
        all_hor_possible_ships1 = [ship for i in range(-(size - 1), 1)
                                   if (ship := Ship({Cell(r0, c0 + s + i)
                                                     for s in range(size)})).can_be_placed_on(self.board)]
        # Összes lehetséges vízszintesen elhelyezhető hajó, amely a többi megadott cellát is tartalmazza.
        all_hor_possible_ships2 = [ship for ship in all_hor_possible_ships1 if ship.has_cells(*cells)]

        # Összes lehetséges függőlegesen elhelyezhető hajó, amely tartalmazza a megadottak közül az első cellát.
        all_ver_possible_ships1 = [ship for i in range(-(size - 1), 1)
                                   if (ship := Ship({Cell(r0 + s + i, c0)
                                                     for s in range(size)})).can_be_placed_on(self.board)]
        # Összes lehetséges függőlegesen elhelyezhető hajó, amely a többi megadott cellát is tartalmazza.
        all_ver_possible_ships2 = [ship for ship in all_ver_possible_ships1 if ship.has_cells(*cells)]

        return tuple(ship.cells for ship in all_hor_possible_ships2 + all_ver_possible_ships2)


class GameModel:
    def __init__(self, board_size=10):
        self.board_size = board_size if board_size > 10 else 10  # A játéktáblák sorainak és oszlopainak száma.
        self.ship_sizes = (4, 3, 3, 2, 2, 2, 1, 1, 1, 1)  # A lehelyezendő hajók cellaszámban mért méretei.
        self.current_shipsize_to_build = self.ship_sizes[0]

        # Az emberi és gépi játékosok tábláinak létrehozása.
        self.human_board = Board(self.board_size, self.ship_sizes)
        self.computer_board = Board(self.board_size, self.ship_sizes)

        # A gépi játékost modellező objektum létrehozása.
        self.computer_player = ComputerPlayer(self.computer_board)
        self.game_phase = GamePhase.PLACEMENT  # A játék kezdő, azaz hajólehelyezési fázisba állítása.

        # A gépi játékos elhelyezi a hajóit.
        self.computer_player.place_ships()
        # Ahhoz, hogy az emberi játékos hajókat tudjon elhelyezni, létrehozzuk a hajók előállítására képes objektumot.
        self.human_fleet_factory = HumanFleetFactory(self.human_board)

    def human_make_ship(self, cell: Cell) -> tuple[bool, bool]:
        """Megállapítja, hogy az emberi játékos táblján a megadott cella lehet-e az aktuálisan létrehozandó hajó része.
        Ezt jelzi a visszatérési érték első eleme. A második elem pedig azt, hogy ezzel a hajó el is készül.
        Ha ez utóbbi igaz, akkor létre is jön a hajó.
        Ha az emberi játékos minden hajója elkészült, a játékot a csata fázisba lépteti.
        """
        if self.human_board.all_ships_placed():
            self.game_phase = GamePhase.BATTLE
            return False, False

        return self.human_fleet_factory.assemble_ship(cell)

    def human_shoot(self, target_cell: Cell) -> tuple[ShotResult, set[Cell]]:
        """Az emberi játékosnak az ellenfél táblájának egy cellájára leadott lövését értékeli ki.
        Visszaadja a lövés eredményét és a lövéssel érintett cellát, ha nem talált vagy talált, de nem süllyedt, vagy
        a hajó összes celláját, ha a lövés következtében a hajó elsüllyedt.
        """
        shot_result = self.computer_board.process_shot(target_cell)

        affected_cells = set()
        if shot_result == ShotResult.MISS or shot_result == ShotResult.HIT:
            affected_cells = {target_cell}
        elif shot_result == ShotResult.SUNK:
            ship = self.computer_board.get_ship(target_cell)
            assert ship is not None  # Ha a hajó elsüllyedt, akkor a target_cell biztosan egy hajó része.
            affected_cells = set(ship.cells)

        return shot_result, affected_cells

    def computer_shoot(self) -> tuple[ShotResult, set[Cell]]:
        """A gépi játékos ellenfél táblájának egy cellájára leadott lövését értékeli ki.
        Visszaadja a lövés eredményét és a megcélzott cellát.
        """
        return self.computer_player.shoot(self.human_board)

    def check_winner(self) -> Winner | None:
        """Ha van nyertes, visszaadja, hogy ki az, egyébként None a vissztérési érték."""
        if self.human_board.all_ships_sunk():
            return Winner.COMPUTER
        elif self.computer_board.all_ships_sunk():
            return Winner.HUMAN
        else:
            return None

    def get_undamaged_computer_ship_cells(self) -> set[Cell]:
        """Visszaadja a gépi játékos hajóinak azon celláit, amelyeket még nem ért találat."""
        return set(cell for ship in self.computer_board
                   for cell in ship.cells if not ship.cell_is_damaged(cell))

    def get_next_human_ship_size(self) -> int | None:
        """Visszaadja az emberi játékos következő megépítendő és lehelyezendő hajójának méretét.
        Ha nincs már ilyen hajó, akkor a visszatérési érték None.
        """
        return next(iter(self.human_fleet_factory.ship_sizes_to_build), None)
