import wx
import subprocess
import threading
import pandas as pd
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import re
import os
import sys
import time

class MainFrame(wx.Frame):
    """
    Versión final y definitiva de la aplicación de escritorio para ejecutar simulaciones
    de un protocolo QZKP, con todas las funcionalidades solicitadas.
    """
    def __init__(self):
        super().__init__(None, title="Quantum ZKP Simulator", size=(1200, 750))
        self.panel_controls = {}
        self.scripts = {
            "1. Basic Protocol": "QZKP_barebones.py",
            "2. Ideal Attack (Iterative)": "QZKP_attack_ideal.py",
            "3. Damping Noise (Iterative)": "QZKP_noise_damping.py",
            "4. Flip Noise (Iterative)": "QZKP_noise_flip.py"
        }
        self.start_time = 0
        self.latest_results_file = None

        self.update_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_update_timer, self.update_timer)

        self.CreateStatusBar()
        self.SetStatusText("Ready")

        main_panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        control_panel = self._create_control_panel(main_panel)
        output_panel = self._create_output_panel(main_panel)
        main_sizer.Add(control_panel, 1, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(output_panel, 3, wx.EXPAND | wx.ALL, 10)
        main_panel.SetSizer(main_sizer)
        
        self.on_script_select(None)
        self.Centre()
        self.Show()

    def _create_control_panel(self, parent):
        self.control_panel = wx.Panel(parent)
        top_sizer = wx.BoxSizer(wx.VERTICAL)
        
        selection_box = wx.StaticBox(self.control_panel, label="Simulation Selection")
        selection_sizer = wx.StaticBoxSizer(selection_box, wx.VERTICAL)
        self.script_selector = wx.Choice(self.control_panel, choices=list(self.scripts.keys()))
        self.script_selector.SetSelection(0)
        selection_sizer.Add(self.script_selector, 0, wx.EXPAND | wx.ALL, 5)
        top_sizer.Add(selection_sizer, 0, wx.EXPAND | wx.BOTTOM, 10)

        params_box = wx.StaticBox(self.control_panel, label="Specific Parameters")
        self.params_box_sizer = wx.StaticBoxSizer(params_box, wx.VERTICAL)
        self._create_param_panels(params_box)
        top_sizer.Add(self.params_box_sizer, 0, wx.EXPAND)

        self.save_box = wx.StaticBox(self.control_panel, label="Save Data & Plot")
        save_box_sizer = wx.StaticBoxSizer(self.save_box, wx.VERTICAL)
        self._populate_save_box(self.save_box, save_box_sizer)
        top_sizer.Add(save_box_sizer, 0, wx.EXPAND | wx.TOP, 10)

        top_sizer.AddStretchSpacer(prop=1)
        
        progress_labels_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.percent_label = wx.StaticText(self.control_panel, label="")
        self.time_label = wx.StaticText(self.control_panel, label="")
        progress_labels_sizer.Add(self.percent_label, 0, wx.ALIGN_CENTER_VERTICAL)
        progress_labels_sizer.AddStretchSpacer(prop=1)
        progress_labels_sizer.Add(self.time_label, 0, wx.ALIGN_CENTER_VERTICAL)
        top_sizer.Add(progress_labels_sizer, 0, wx.EXPAND | wx.TOP, 5 | wx.LEFT | wx.RIGHT, 2)
        
        self.run_button = wx.Button(self.control_panel, label="▶ Run Simulation")
        self.progress_bar = wx.Gauge(self.control_panel, range=100, style=wx.GA_HORIZONTAL)
        top_sizer.Add(self.run_button, 0, wx.EXPAND | wx.TOP, 5)
        top_sizer.Add(self.progress_bar, 0, wx.EXPAND | wx.TOP, 5)

        self.control_panel.SetSizer(top_sizer)

        self.Bind(wx.EVT_CHOICE, self.on_script_select, self.script_selector)
        self.Bind(wx.EVT_BUTTON, self.on_run_simulation, self.run_button)
        return self.control_panel

    def _populate_save_box(self, parent, sizer):
        grid_sizer = wx.FlexGridSizer(2, 3, 5, 5)
        grid_sizer.AddGrowableCol(1, 1)
        plot_format_label = wx.StaticText(parent, label="Plot Format:")
        self.plot_format_choice = wx.Choice(parent, choices=['PNG (*.png)', 'PDF (*.pdf)', 'SVG (*.svg)', 'EPS (*.eps)'])
        self.plot_format_choice.SetSelection(0)
        save_plot_button = wx.Button(parent, label="Save Plot...")
        data_format_label = wx.StaticText(parent, label="Data Format:")
        self.data_format_choice = wx.Choice(parent, choices=['CSV (*.csv)', 'JSON (*.json)', 'Excel (*.xlsx)'])
        self.data_format_choice.SetSelection(0)
        save_data_button = wx.Button(parent, label="Save Data...")
        grid_sizer.Add(plot_format_label, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)
        grid_sizer.Add(self.plot_format_choice, 1, wx.EXPAND)
        grid_sizer.Add(save_plot_button, 0)
        grid_sizer.Add(data_format_label, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)
        grid_sizer.Add(self.data_format_choice, 1, wx.EXPAND)
        grid_sizer.Add(save_data_button, 0)
        sizer.Add(grid_sizer, 1, wx.EXPAND | wx.ALL, 5)
        self.Bind(wx.EVT_BUTTON, self.on_save_plot, save_plot_button)
        self.Bind(wx.EVT_BUTTON, self.on_save_data, save_data_button)

    def _create_param_panels(self, parent):
        self.param_panels = {}
        script_names = list(self.scripts.keys())
        panel_builders = {script_names[i]: builder for i, builder in enumerate([self._build_panel_basic, self._build_panel_attack, self._build_panel_damping, self._build_panel_flip])}
        for name, builder in panel_builders.items():
            panel, controls = builder(parent)
            self.params_box_sizer.Add(panel, 0, wx.EXPAND | wx.ALL, 5)
            self.param_panels[name] = panel
            self.panel_controls[name] = controls
        
    def _build_panel_basic(self, parent):
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        # Se eliminó la CheckBox de modo verboso
        sizer, controls = self._build_common_controls(panel, show_iter=False)
        panel.SetSizer(sizer)
        return panel, controls

    def _build_panel_attack(self, parent):
        panel = wx.Panel(parent)
        sizer, controls = self._build_common_controls(panel, show_iter=True)
        panel.SetSizer(sizer)
        return panel, controls

    def _build_common_controls(self, panel, show_iter=True):
        sizer = wx.BoxSizer(wx.VERTICAL)
        key_lbl = wx.StaticText(panel, label="Key Length:")
        key_ctrl = wx.TextCtrl(panel, value="64")
        sizer.Add(key_lbl, 0, wx.EXPAND)
        sizer.Add(key_ctrl, 0, wx.EXPAND | wx.BOTTOM, 5)
        controls = {'key': key_ctrl}
        if show_iter:
            iter_lbl = wx.StaticText(panel, label="No. of Iterations:")
            iter_ctrl = wx.TextCtrl(panel, value="200")
            sizer.Add(iter_lbl, 0, wx.EXPAND)
            sizer.Add(iter_ctrl, 0, wx.EXPAND | wx.BOTTOM, 5)
            controls['iter'] = iter_ctrl
        return sizer, controls

    def _build_panel_damping(self, parent):
        panel, controls = self._build_panel_attack(parent)
        sizer = panel.GetSizer()
        attacker_ctrl = wx.CheckBox(panel, label="Enable Attacker")
        attacker_ctrl.SetValue(True)
        sizer.Add(attacker_ctrl, 0, wx.TOP, 10)
        gamma_sizer, gamma_ctrl = self._create_labeled_slider(panel, "Gamma (Amp Damping):", 1, max_val_float=0.5)
        lam_sizer, lam_ctrl = self._create_labeled_slider(panel, "Lambda (Phase Damping):", 2, max_val_float=0.5)
        sizer.Add(gamma_sizer, 0, wx.EXPAND | wx.TOP, 10)
        sizer.Add(lam_sizer, 0, wx.EXPAND | wx.TOP, 10)
        panel.SetSizer(sizer)
        controls.update({'attacker': attacker_ctrl, 'gamma': gamma_ctrl, 'lam': lam_ctrl})
        return panel, controls

    def _build_panel_flip(self, parent):
        panel, controls = self._build_panel_attack(parent)
        sizer = panel.GetSizer()
        attacker_ctrl = wx.CheckBox(panel, label="Enable Attacker")
        attacker_ctrl.SetValue(True)
        sizer.Add(attacker_ctrl, 0, wx.TOP, 10)
        pbit_sizer, pbit_ctrl = self._create_labeled_slider(panel, "Bit-Flip Probability:", 1, max_val_float=0.1)
        pphase_sizer, pphase_ctrl = self._create_labeled_slider(panel, "Phase-Flip Probability:", 2, max_val_float=0.1)
        sizer.Add(pbit_sizer, 0, wx.EXPAND | wx.TOP, 10)
        sizer.Add(pphase_sizer, 0, wx.EXPAND | wx.TOP, 10)
        panel.SetSizer(sizer)
        controls.update({'attacker': attacker_ctrl, 'pbit': pbit_ctrl, 'pphase': pphase_ctrl})
        return panel, controls
        
    def _create_labeled_slider(self, parent, label_text, initial_value, max_val_float=0.5):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        label_sizer = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(parent, label=label_text)
        value_label = wx.StaticText(parent, label=f"{initial_value/100:.2f}")
        value_label.SetFont(wx.Font(wx.DEFAULT, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        label_sizer.Add(label, 1, wx.ALIGN_CENTER_VERTICAL)
        label_sizer.Add(value_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        main_sizer.Add(label_sizer, 0, wx.EXPAND)
        slider_sizer = wx.BoxSizer(wx.HORIZONTAL)
        min_label = wx.StaticText(parent, label="0.0")
        max_int_val = int(max_val_float * 100)
        slider = wx.Slider(parent, value=initial_value, minValue=0, maxValue=max_int_val)
        max_label = wx.StaticText(parent, label=f"{max_val_float}")
        slider_sizer.Add(min_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        slider_sizer.Add(slider, 1, wx.EXPAND)
        slider_sizer.Add(max_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        main_sizer.Add(slider_sizer, 0, wx.EXPAND)
        slider.Bind(wx.EVT_SLIDER, lambda event: self.on_slider_update(event, value_label))
        return main_sizer, slider

    def on_slider_update(self, event, label_to_update):
        slider = event.GetEventObject()
        value = slider.GetValue()
        float_value = value / 100.0
        label_to_update.SetLabel(f"{float_value:.2f}")

    def on_script_select(self, event):
        selected_script = self.script_selector.GetStringSelection()
        is_iterative = "Iterative" in selected_script
        
        for name, panel in self.param_panels.items():
            panel.Show(name == selected_script)
        
        self.save_box.Show(is_iterative)
        
        if is_iterative:
            self.output_book.ChangeSelection(0)
        else:
            self.output_book.ChangeSelection(1)
        
        self.params_box_sizer.Fit(self.params_box_sizer.GetStaticBox())
        self.control_panel.Layout()

    def _create_output_panel(self, parent):
        output_panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.output_book = wx.Simplebook(output_panel)
        plot_page = self._create_plot_page(self.output_book)
        console_page = self._create_console_page(self.output_book)
        self.output_book.AddPage(plot_page, "plot")
        self.output_book.AddPage(console_page, "console")
        sizer.Add(self.output_book, 1, wx.EXPAND)
        output_panel.SetSizer(sizer)
        return output_panel

    def _create_plot_page(self, parent):
        plot_panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(plot_panel, -1, self.fig)
        sizer.Add(self.canvas, 1, wx.EXPAND)
        plot_panel.SetSizer(sizer)
        return plot_panel

    def _create_console_page(self, parent):
        console_panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.console_output = wx.TextCtrl(console_panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)
        sizer.Add(self.console_output, 1, wx.EXPAND)
        
        # --- NUEVO: Botón para guardar el log de la consola ---
        save_log_button = wx.Button(console_panel, label="Save Log to .txt...")
        sizer.Add(save_log_button, 0, wx.ALL | wx.ALIGN_RIGHT, 5)
        self.Bind(wx.EVT_BUTTON, self.on_save_console, save_log_button)

        console_panel.SetSizer(sizer)
        self.console_output.AppendText("Welcome to the Quantum Simulator.\nSelect a script and press 'Run'.\n")
        return console_panel

    def on_save_plot(self, event):
        selection = self.plot_format_choice.GetStringSelection()
        file_ext = selection[selection.find('*.')+2:selection.find(')')]
        wildcard = f"{selection.split(' ')[0]} files (*.{file_ext})|*.{file_ext}"
        with wx.FileDialog(self, "Save plot as...", wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL: return
            pathname = fileDialog.GetPath()
            try:
                self.fig.savefig(pathname)
                self.SetStatusText(f"Plot saved to: {pathname}")
            except Exception as e:
                self.SetStatusText(f"Error saving plot: {e}")
                wx.MessageBox(f"Could not save plot to '{pathname}'.\nError: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def on_save_data(self, event):
        if not self.latest_results_file or not os.path.exists(self.latest_results_file):
            wx.MessageBox("No data to save. Please run an iterative simulation first.", "No Data", wx.OK | wx.ICON_INFORMATION)
            return
        selection = self.data_format_choice.GetStringSelection()
        file_ext = selection[selection.find('*.')+2:selection.find(')')]
        wildcard = f"{selection.split(' ')[0]} files (*.{file_ext})|*.{file_ext}"
        with wx.FileDialog(self, "Save data as...", wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL: return
            pathname = fileDialog.GetPath()
            try:
                df = pd.read_csv(self.latest_results_file)
                if file_ext == 'csv':
                    df.to_csv(pathname, index=False)
                elif file_ext == 'json':
                    df.to_json(pathname, orient='records', indent=4)
                elif file_ext == 'xlsx':
                    df.to_excel(pathname, index=False)
                self.SetStatusText(f"Data saved to: {pathname}")
            except Exception as e:
                self.SetStatusText(f"Error saving data: {e}")
                wx.MessageBox(f"Could not save data to '{pathname}'.\nError: {e}", "Error", wx.OK | wx.ICON_ERROR)
    
    def on_save_console(self, event):
        """Guarda el contenido de la consola de texto en un archivo .txt."""
        with wx.FileDialog(self, "Save console log as...", wildcard="Text files (*.txt)|*.txt", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL: return
            pathname = fileDialog.GetPath()
            try:
                content = self.console_output.GetValue()
                with open(pathname, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.SetStatusText(f"Console log saved to: {pathname}")
            except Exception as e:
                self.SetStatusText(f"Error saving log: {e}")
                wx.MessageBox(f"Could not save log to '{pathname}'.\nError: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def on_update_timer(self, event):
        if self.start_time > 0:
            elapsed_seconds = time.time() - self.start_time
            self.time_label.SetLabel(f"Elapsed: {elapsed_seconds:.1f}s")

    def on_run_simulation(self, event):
        self.run_button.Disable()
        self.run_button.SetLabel("Running...")
        self.SetStatusText("Running simulation...")
        self.progress_bar.SetValue(0)
        self.percent_label.SetLabel("0.0%")
        self.time_label.SetLabel("Elapsed: 0.0s")
        self.control_panel.Layout()
        
        self.console_output.Clear()
        self.console_output.AppendText("Starting simulation...\n\n")
        
        self.start_time = time.time()
        self.update_timer.Start(100)
        
        thread = threading.Thread(target=self._run_simulation_thread)
        thread.daemon = True
        thread.start()

    def _run_simulation_thread(self):
        script_name = self.script_selector.GetStringSelection()
        script_file = self.scripts[script_name]
        active_controls = self.panel_controls[script_name]
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            full_script_path = os.path.join(script_dir, script_file)
            command = [sys.executable, "-u", full_script_path]
            key_length = active_controls['key'].GetValue()
            if not key_length.isdigit() or int(key_length) == 0: raise ValueError("Key length must be a positive integer")
            command.append(key_length)
            is_iterative = "Iterative" in script_name
            if is_iterative:
                num_iter = active_controls['iter'].GetValue()
                if not num_iter.isdigit() or int(num_iter) == 0: raise ValueError("No. of iterations must be a positive integer")
                command.append(num_iter)
                if "Damping" in script_name:
                    command.append(f"{active_controls['gamma'].GetValue() / 100:.4f}")
                    command.append(f"{active_controls['lam'].GetValue() / 100:.4f}")
                    command.append(str(active_controls['attacker'].GetValue()))
                elif "Flip" in script_name:
                    command.append(f"{active_controls['pbit'].GetValue() / 100:.4f}")
                    command.append(f"{active_controls['pphase'].GetValue() / 100:.4f}")
                    command.append(str(active_controls['attacker'].GetValue()))
            # --- CAMBIO: El modo verboso ahora está hardcodeado ---
            elif "Basic" in script_name:
                command.append("v")
        except (ValueError, KeyError) as e:
            wx.CallAfter(self.update_timer.Stop)
            wx.CallAfter(self.SetStatusText, f"Parameter error: {e}")
            wx.CallAfter(self.console_output.AppendText, f"Error: {e}\n")
            wx.CallAfter(self.run_button.Enable)
            wx.CallAfter(self.run_button.SetLabel, "▶ Run Simulation")
            return
        
        proc_env = os.environ.copy()
        proc_env["PYTHONUNBUFFERED"] = "1"
        
        kwargs = {'env': proc_env}
        if sys.platform != "win32":
            kwargs['close_fds'] = True
        
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True, **kwargs)
        
        for line in iter(process.stdout.readline, ''):
            wx.CallAfter(self.console_output.AppendText, line)
            
            progress_match = re.search(r'(\d+\.\d+)%', line)
            if progress_match:
                percent_str = progress_match.group(1)
                wx.CallAfter(self.progress_bar.SetValue, int(float(percent_str)))
                wx.CallAfter(self.percent_label.SetLabel, f"{percent_str}%")
        
        process.wait()
        
        wx.CallAfter(self.update_timer.Stop)
        total_time = time.time() - self.start_time
        
        stderr_output = process.stderr.read()
        if stderr_output:
            wx.CallAfter(self.console_output.AppendText, f"\n--- ERRORS ---\n{stderr_output}")
        
        wx.CallAfter(self.SetStatusText, "Simulation finished. Ready.")
        wx.CallAfter(self.run_button.Enable)
        wx.CallAfter(self.run_button.SetLabel, "▶ Run Simulation")
        
        if is_iterative:
            wx.CallAfter(self.progress_bar.SetValue, 100)
            wx.CallAfter(self.percent_label.SetLabel, "100.0%")
            wx.CallAfter(self.time_label.SetLabel, f"Total time: {total_time:.1f}s")
            wx.CallAfter(self.find_and_plot_results)
        else:
             wx.CallAfter(self.progress_bar.SetValue, 0)
             wx.CallAfter(self.percent_label.SetLabel, "")
             wx.CallAfter(self.time_label.SetLabel, "")

    def find_and_plot_results(self):
        try:
            files = [f for f in os.listdir('.') if f.endswith('.csv')]
            if not files:
                self.console_output.AppendText("No results CSV file found.\n")
                return
            latest_file = max(files, key=os.path.getctime)
            self.latest_results_file = latest_file
            self.console_output.AppendText(f"Plotting results from: {latest_file}\n")
            self.plot_data(latest_file)
        except Exception as e:
            self.console_output.AppendText(f"Error plotting results: {e}\n")
            self.SetStatusText(f"Error plotting: {e}")

    def plot_data(self, csv_file):
        df = pd.read_csv(csv_file)
        self.ax.clear()
        if 'Decision' in df.columns:
            honest_df = df[df['Decision'] == 0]
            dishonest_df = df[df['Decision'] == 1]
            self.ax.scatter(honest_df['Iteration'], honest_df['Percentages'], label='Honest (Dec=0)', color='#3498db', marker='o', alpha=0.8, s=20)
            self.ax.scatter(dishonest_df['Iteration'], dishonest_df['Percentages'], label='Dishonest (Dec=1)', color='#e74c3c', marker='x', alpha=0.8, s=20)
            self.ax.legend()
        else:
             self.ax.scatter(df['Iteration'], df['Percentages'], label='Results', color='#3498db', marker='o', alpha=0.8, s=20)
        self.ax.set_title('Success Rate per Iteration')
        self.ax.set_xlabel('Iteration')
        self.ax.set_ylabel('Success Rate (%)')
        self.ax.grid(True, linestyle='--', alpha=0.6)
        min_y = max(0, df['Percentages'].min() - 10)
        max_y = min(100, df['Percentages'].max() + 10)
        self.ax.set_ylim(min_y, max_y)
        self.canvas.draw()

if __name__ == "__main__":
    try:
        import wx
        import pandas
        import matplotlib
        import openpyxl 
    except ImportError:
        print("Error: One or more dependencies are missing.")
        print("Please install the required libraries by running:")
        print("pip install wxPython pandas matplotlib openpyxl")
        sys.exit()

    app = wx.App(False)
    frame = MainFrame()
    app.MainLoop()