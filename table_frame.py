import tkinter as tk
from tkinter import ttk
import logging

import numpy as np


class TableFrame(ttk.Frame):
    def __init__(self, parent, table_array=None):
        logging.debug("being TableFrame.__init__")
        ttk.Frame.__init__(self, parent)
        self.parent = parent  # parent is TC_Frame
        
        self.table_array = np.array([[1,1,1],[1,2,3],[5,6,7]])

        self.cells = None

        if (self.table_array is None and
            self.parent.parent.data.episode.idealization is not None
            ):
            self.table_array = self.parent.parent.data.get_events()

        if self.table_array is not None:
            self.create_widgets()

    def create_widgets(self):
        self.create_table(self.table_array)
        
        self.scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.scrollbar.grid(column=2, row=1, rowspan=3, sticky="NESW")

    def create_table(self, table_array):
        n_rows, n_cols = np.shape(table_array)
        self.table = ttk.Frame(self)
        self.table.grid(row=1, column=1, rowspan=3)

        self.cells = []
        for i in range(n_rows):
            row = []
            for j in range(n_cols):
                cell = tk.Label(self.table, text=f"{self.table_array[i,j]:.2f}",
                                 borderwidth=0, width=10)
                cell.grid(row=i, column=j, sticky="nsew", padx=1, pady=1)
                row.append(cell)
            self.cells.append(row)
        # for column in range(n_cols):
        #     self.grid_columnconfigure(column, weight=1)

    # def change_val(self, val, row, col):
    #     """We will need this function is the table is supposed to be
    #     editable."""
    #     cell = self.table[row][col]
    #     if type(val) == float:
    #         val = f"{val:.2f}"
    #     cell.configure(text=f"{val}")


if __name__ == "__main__":
    class ExampleApp(tk.Tk):
        def __init__(self):
            tk.Tk.__init__(self)
            arr = np.random.normal(size=(3,5))
            t = TableFrame(self, arr)
            t.pack(side="top", fill="x")
            t.change_val("lol", 0, 0)

    app = ExampleApp()
    app.mainloop()
