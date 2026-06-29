import tkinter as tk
from itertools import product
import winsound
from typing import cast, Callable
from model import Cell, GameModel, ShotResult, GamePhase, Winner


class BoardView(tk.Frame):
    """A játéktáblákat megjelenítő osztály, amely az emberi és gépi játékosok tábláinak közös metódusait definiálja."""

    def __init__(self, master, board_size: int) -> None:
        super().__init__(master)

        self._board_size = board_size if board_size > 10 else 10  # A klasszikus játék 10x10-es táblájánál nem lehet kisebb.
        self._cell_canvases: dict[Cell, tk.Canvas] = {}  # Az egyes cellák és azokat megjelenítő vászonobjektumok tárolása.
        self._create_cell_grid()

    def _create_cell_grid(self) -> None:
        """A játéktáblán létrehozza és megjeleníti a cellákat."""
        for row_index, column_index in product(range(self._board_size), repeat=2):
            grid_cell = Cell(row_index, column_index)
            cell_canvas = tk.Canvas(self, width='1.2c', height='1.2c', bg="#B3F0FF", bd=1, highlightthickness=0)
            cell_canvas.grid(row=row_index, column=column_index, padx=1, pady=1)
            self._cell_canvases[grid_cell] = cell_canvas

    def bind_cell_event(self, tk_event_descriptor: str, handler: Callable[[tk.Event], None]) -> None:
        """A cellákhoz rendeli a megadott eseményt és eseménykezelőt."""
        for cell_widget in self._cell_canvases.values():
            cell_widget.bind(tk_event_descriptor, handler)

    def update_on_shot(self, affected_cells: set[Cell], shot_result: ShotResult) -> None:
        """A játéktábla megadott celláinak megjelenését módosítja a lövés eredményének megfelelően.
        Ha nincs találat, akkor az első argumentum egyelemű, és e cellán egy kis fekete körlapot rajzol.
        Ha van találat, de még nem süllyed el a hajó, akkor az első argumentum egyelemű, és e cella színe
        szürkére változik, és egy piros X jel jelenik meg.
        Ha a lövés hatására a hajó elsüllyed, akkor az első argumentum legalább egyelemű, és e cellák fekete színűek lesznek.
        """
        match shot_result:
            case ShotResult.MISS:
                self._update_miss(affected_cells.pop())

            case ShotResult.HIT:
                self._update_hit(affected_cells.pop())

            case ShotResult.SUNK:
                self._update_sunk(affected_cells)

    def _update_miss(self, cell: Cell) -> None:
        """A megadott cellán egy kis fekete körlapot rajzol."""
        canvas = self._cell_canvases[cell]
        cnv_width, cnv_height = canvas.winfo_width(), canvas.winfo_height()
        canvas.create_oval(cnv_width * 0.4, cnv_height * 0.4, cnv_width * 0.6, cnv_height * 0.6, fill="black")

    def _update_hit(self, cell: Cell) -> None:
        """A megadott cella színe szürkére változik, és egy piros X jel jelenik meg benne."""
        canvas = self._cell_canvases[cell]
        cnv_width, cnv_height = canvas.winfo_width(), canvas.winfo_height()
        canvas.config(bg='grey75')
        canvas.create_line(0, 0, cnv_width, cnv_height, fill="red", width=4)
        canvas.create_line(0, cnv_height, cnv_width, 0, fill="red", width=4)

    def _update_sunk(self, cells: set[Cell]) -> None:
        """A megadott cellák fekete színűek lesznek."""
        for cell in cells:
            canvas = self._cell_canvases[cell]
            canvas.delete('all')
            canvas.config(bg='black')


class HumanBoardView(BoardView):
    """Az emberi játékos táblájának megjelenítésére szolgáló panel."""

    def mark_as_ship_cell(self, cell: Cell):
        """A megadott cellát mint a hajó egy részét színezéssel jeleníti meg."""
        self._cell_canvases[cell].config(bg="SeaGreen3")

    @staticmethod
    def play_ship_placement_sound() -> None:
        """Új hajó elhelyezésére felhívó hangjelzés."""
        winsound.PlaySound("SystemExclamation", winsound.SND_ASYNC)


class ComputerBoardView(BoardView):
    """A gépi játékos táblájának megjelenítésére szolgáló panel."""

    def mark_as_revealed_ship_cell(self, cell: Cell) -> None:
        """A még fel nem fedezett hajóhoz tartozó megadott cella színét módosítja."""
        self._cell_canvases[cell].config(bg='yellow')


class MessageView(tk.Frame):
    """A tájékoztató szövegeket megjelenítő panel."""

    def __init__(self, master, control_variable: tk.StringVar) -> None:
        super().__init__(master)
        message_lbl = tk.Label(self, textvariable=control_variable, bg='white', fg='red', font=('Tahoma', 14, 'bold'))
        message_lbl.pack(fill='both', expand=True)


class BattleshipGame(tk.Tk):
    """Az alkalmazás vezérlőobjektuma, amely egyben a GUI főablakát is reprezentálja.
    Feladata a modell és a nézetek létrehozása, az eseménykezelők regisztrálása, valamint a
    játékfolyamat koordinálása.
    """

    def __init__(self, board_size: int = 10) -> None:
        super().__init__()

        self.title("Torpedó játék")
        self.resizable(False, False)

        # A játék modell objektumának létrehozása.
        self._game_model = GameModel(board_size)

        # A megjelenítő panelek létrehozása és lehelyezése.
        human_board_title = tk.Label(self, text='Emberi játékos táblája', font=('Tahoma', 12, 'bold'))
        computer_board_title = tk.Label(self, text='Gépi játékos táblája', font=('Tahoma', 12, 'bold'))
        human_board_title.grid(row=0, column=0, padx=10, pady=(10, 0), sticky='news')
        computer_board_title.grid(row=0, column=1, padx=10, pady=(10, 0), sticky='news')

        self.human_board = HumanBoardView(self, board_size)
        self.computer_board = ComputerBoardView(self, board_size)

        self.human_board.grid(row=1, column=0, padx=10, pady=10)
        self.computer_board.grid(row=1, column=1, padx=10, pady=10)

        self.message = tk.StringVar(self, '')
        MessageView(self, self.message).grid(row=2, column=0, columnspan=2, padx=10, pady=(0, 10), sticky='news')

        # Meghatározzuk, hogy milyen, az emberi játékos által keltett eseményekre reagáljanak a játéktáblák cellái, és
        # ezek bekövetkezésekor mely metódusokat kell meghívni.
        self.human_board.bind_cell_event("<Button-1>", self._place_human_ship)
        self.computer_board.bind_cell_event("<Button-1>", self._process_shot_on_computer_board)
        self.computer_board.bind_cell_event("<Button-3>", self._reveal_undamaged_computer_ship_cells)

        # Induláskori üzenet, amely az első hajó lehelyezésére szólít fel.
        self.message.set(f'Helyezz el egy {self._game_model.get_next_human_ship_size()} méretű hajót.')

    # ----------------------------------- ESEMÉNYKEZELŐK --------------------------------

    def _place_human_ship(self, event: tk.Event) -> None:
        """A játék hajólehelyezési fázisában az emberi játékos tábláján az eseménnyel érintett celláról
        eldönti, hogy az hajó része-e. Ha igen, akkor ezt a cella kinézetének módosításával jelzi.
        Ha a cella a hajó utolsó cellája, vagyis a hajó teljesen elkészült, akkor egy hangjelzés jelzi, hogy
        egy következő hajót kell lehelyezni, aminek méretét szöveges kiírás mutatja.
        Ha nincs már több lehelyezenő hajó, akkor a játékot csata fázisba hozza.
        """
        cell_canvas = cast(tk.Canvas, event.widget)
        clicked_cell: Cell = Cell(cell_canvas.grid_info()['row'], cell_canvas.grid_info()['column'])

        if self._game_model.game_phase == GamePhase.PLACEMENT:
            cell_is_ship_body, ship_completed = self._game_model.human_make_ship(clicked_cell)

            if cell_is_ship_body:
                # Ha a kiválasztott cella a hajó része, akkor azt valamilyen módon vizuálisan jelezzük.
                self.human_board.mark_as_ship_cell(clicked_cell)

            if self._game_model.get_next_human_ship_size():
                if ship_completed:
                    # Ha a hajó teljesen elkészült, akkor egy hangjelzést követő kiírással jelezzük, hogy a következő
                    # hajónak mekkora mértetűnek kell lenni.
                    self.human_board.play_ship_placement_sound()
                    self.message.set(f'Helyezz el egy '
                                     f'{self._game_model.get_next_human_ship_size()} méretű hajót.')
            else:
                # Ha nincs már több elhelyezésre váró hajó, akkor a játék a csata fázisba lép, amit
                # egy kiírt üzenettel is jelzünk.
                self._game_model.game_phase = GamePhase.BATTLE
                self.message.set('Lőjél cellákra az ellenfél tábláján')

    def _process_shot_on_computer_board(self, event: tk.Event) -> None:
        """Az emberi játékos ellenfél táblájára leadott lövésének kiértékelése, ha még nem ért véget a játék.
        A lövés eredménye megjelenik a gépi játékos tábláján. Ha a lövéssel minden hajó elsüllyed, akkor a játék véget ér.
        """
        cell_canvas = cast(tk.Canvas, event.widget)
        clicked_cell: Cell = Cell(cell_canvas.grid_info()['row'], cell_canvas.grid_info()['column'])

        if self._game_model.game_phase == GamePhase.BATTLE:
            shot_result, affected_cells = self._game_model.human_shoot(clicked_cell)
            self.computer_board.update_on_shot(affected_cells, shot_result)
            self._notify_upon_wictory()
            # Miután az emberi játékos lőtt, következik a gépi játékos lövése.
            self._computer_shoot()

    def _reveal_undamaged_computer_ship_cells(self, event: tk.Event) -> None:
        """Megjeleníti a gépi játékos hajóinak azon celláit, amelyeket még nem ért találat.
        Hajólehelyezési fázisban nincs hatása.
        """
        if self._game_model.game_phase != GamePhase.PLACEMENT:
            for cell in self._game_model.get_undamaged_computer_ship_cells():
                self.computer_board.mark_as_revealed_ship_cell(cell)

    # ------------------------------------- SEGÉDMETÓDUSOK -----------------------------

    def _computer_shoot(self) -> None:
        """A gépi játékos lő az emberi játékos táblájának egy mezőjére, ha még nem ért véget a játék.
        A lövés eredménye megjelenik az emberi játékos tábláján. Ha a lövéssel minden hajó elsüllyed, akkor a játék véget ér.
        """
        if self._game_model.game_phase != GamePhase.VICTORY:
            shot_result, affected_cells = self._game_model.computer_shoot()
            self.human_board.update_on_shot(affected_cells, shot_result)
            self._notify_upon_wictory()

    def _notify_upon_wictory(self) -> None:
        """Ha valamelyik játékos nyer, akkor ezt szövegesen kijelzi, és a játékot befejező fázisba hozza."""
        if (winner := self._game_model.check_winner()) is not None:
            text = 'Te nyertél' if winner == Winner.HUMAN else 'A gép nyert'
            self.message.set(text)
            self._game_model.game_phase = GamePhase.VICTORY

    def run(self) -> None:
        """Elindítja a játékot."""
        self.mainloop()


if __name__ == '__main__':
    battleship_game = BattleshipGame()
    battleship_game.run()
