class FirstActivationFrame(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent #parent is main window
        self.fa_threshold = tk.StringVar()
        self.fa_threshold.trace('w', self.change_threshold)

        if self.parent.data.fa_threshold is None and np.any(parent.data._TC_thresholds):
            self.fa_threshold.set(str(parent.data._TC_thresholds[0]))
        else:
            self.fa_threshold.set(str(np.mean(self.parent.data.episode.trace)))
        self.create_widgets()

        self.parent.plots.draw_fa_line(draw=False)
        self.parent.data.detect_fa()
        self.parent.plots.draw_fa_mark(draw=False)
        self.parent.n_episode.set(0)

        self.tracking_on = False

    def change_threshold(self, *args):
        self.parent.data.fa_threshold = float(self.fa_threshold.get())

    def toggle_tracking(self):
        if not self.tracking_on:
            self.plot_track_cid = self.parent.plots.fig.canvas.mpl_connect(
                                                          'motion_notify_event',
                                                          self.track_cursor)
        else:
            self.parent.plots.fig.canvas.mpl_disconnect(self.plot_track_cid)
        self.tracking_on = not self.tracking_on

    def track_cursor(self, event):
        if (self.parent.plots.toolbar._active is None
            and event.button==1
            and event.inaxes is not None
            ):
            self.fa_threshold.set(str(event.ydata))
            self.parent.data.detect_fa()
            self.parent.plots.update_fa_mark(draw=False)
            self.parent.plots.update_fa_line()

    def create_widgets(self):
        self.toggle_button = ttk.Button(self, text='Set Threshold', command=self.toggle_tracking)
        self.toggle_button.grid()
        ttk.Entry(self, textvariable=self.fa_threshold, width=10).grid(row=0,column=1)
        ttk.Button(self, text='OK', command=self.ok_click).grid(row=1)
        ttk.Button(self,text="Cancel", command=self.click_cancel).grid(row=1,column=1)

    def click_cancel(self):
        self.close_frame()

    def ok_click(self):
        self.close_frame()

    def close_frame(self):
        log.debug(f"TC_Frame.close_frame")
        #unbind idealization callback from episode list
        self.parent.episodeList.episodelist.unbind('<<ListboxSelect>>',
                                                    self.eplist_track_id)
        #return plot to previous settings
        self.parent.plots.show_command.set(self.previous_show_command)
        self.parent.plots.show_piezo.set(self.previous_show_piezo)
        self.parent.plots.show_hist.set(self.previous_show_hist)
        #hide TC parameters
        self.parent.plots.show_thetas.set(0)
        self.parent.plots.show_amp.set(0)
        self.parent.plots.update_plots()
        self.parent.plots.fig.canvas.mpl_disconnect(self.plot_track_cid)
        #remove reference in main window
        self.parent.tc_frame = None
        self.destroy()
