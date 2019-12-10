import tkinter as tk
from tkinter import ttk
import logging

import numpy as np


class TableFrame(ttk.Frame):
    def __init__(self, parent):
        logging.debug("being TableFrame.__init__")
        ttk.Frame.__init__(self, parent)
        self.parent = parent  # parent is TC_Frame
        
        self.create_widgets()

    def create_widgets(self):
        row = 1
        # ttk.Label(self,
        #           text=f"Amplitude [{self.parent.parent.data.trace_unit}]"
        #           ).grid(row=row, column=0)
        # ttk.Label(self,
        #           text=f"Duration [{self.parent.parent.data.time_unit}]"
        #           ).grid(row=row, column=1)
        # ttk.Label(self,
        #           text=f"Start [{self.parent.parent.data.time_unit}]"
        #           ).grid(row=row, column=2)
        # ttk.Label(self,
        #           text=f"End [{self.parent.parent.data.time_unit}]"
        #           ).grid(row=row, column=3)
        # row += 1

        self.canvas = tk.Canvas(self)
        self.canvas.grid(row=row, column=0, columnspan=3, sticky="NESW")

        self.table = ttk.Frame(self.canvas)

        self.scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar.grid(column=3, row=row, sticky="NESW")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        def onFrameConfigure(canvas):
            '''Reset the scroll region to encompass the inner frame'''
            canvas.configure(scrollregion=canvas.bbox("all"))

        self.table.bind("<Configure>", lambda event, 
                        canvas=self.canvas: onFrameConfigure(self.canvas))

    def fill_table(self, table_array):
        n_rows, n_cols = np.shape(table_array)

        for i in range(n_rows):
            for j in range(n_cols):
                cell = tk.Label(self.table, text=f"{table_array[i][j]:.3f}",
                                borderwidth=0, width=10)
                cell.grid(row=i, column=j, sticky="nsew", padx=1, pady=1)
        self.canvas.create_window((1, 1), window=self.table)

    def update_table(self, *args):
        events = self.parent.parent.data.episode.get_events()
        self.fill_table(events)


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
