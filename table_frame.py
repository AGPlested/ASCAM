import tkinter as tk
from tkinter import ttk
import logging

import numpy as np


class TableFrame(ttk.Frame):
    def __init__(self, parent):
        logging.debug("being TableFrame.__init__")
        ttk.Frame.__init__(self, parent)
        self.parent = parent  # parent is TC_Frame
        self.ep_or_all = tk.IntVar()
        self.ep_or_all.set(0)  # 0 for episode 1 for series
        
        # self.cells = None

        self.create_widgets()
        # self.set_row_state(tk.DISABLED)

    def create_widgets(self):
        row = 1
        ttk.Label(self,
                  text=f"Episode {self.parent.parent.data.n_episode}"
                  ).grid(row=row, column=0)
        ttk.Radiobutton(
            self, variable=self.ep_or_all, value=0
        ).grid(row=row, column=1)
        ttk.Label(self,
                  text=f"All Episodes"
                  ).grid(row=row, column=2)
        ttk.Radiobutton(
            self, variable=self.ep_or_all, value=1
        ).grid(row=row, column=3)
        row += 1

        self.canvas = tk.Canvas(self)
        self.canvas.grid(row=row, column=0, columnspan=5, sticky="NESW")

        self.table = ttk.Frame(self.canvas)

        self.scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar.grid(column=5, row=row, sticky="NESW")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        def onFrameConfigure(canvas):
            '''Reset the scroll region to encompass the inner frame'''
            canvas.configure(scrollregion=canvas.bbox("all"))

        self.table.bind("<Configure>", lambda event, 
                        canvas=self.canvas: onFrameConfigure(self.canvas))

    def fill_table(self, table_array):
        n_rows, n_cols = np.shape(table_array)

        # self.cells = []
        for i in range(n_rows):
            # row = []
            for j in range(n_cols):
                cell = tk.Label(self.table, text=f"{table_array[i][j]:.3f}",
                                borderwidth=0, width=10)
                cell.grid(row=i, column=j, sticky="nsew", padx=1, pady=1)
                # row.append(cell)
            # self.cells.append(row)
        # for row in range(n_rows):
        #     self.grid_rowconfigure(row, weight=1)
        # for column in range(n_cols):
        #     self.grid_columnconfigure(column, weight=1)
        self.canvas.create_window((1, 1), window=self.table)

    def set_row_state(self, state):
        for w in self.children.values():
            if w.grid_info()["row"] == "1":
                w.config(state=state)

    # def change_val(self, val, row, col):
    #     """We will need this function if the table is supposed to be
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
