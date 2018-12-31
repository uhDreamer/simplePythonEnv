# @Date:   24-12-2017 @ 08:53:23
# @Filename: main.py
# @Last modified time: 24-12-2017 @ 10:10:38

import os
import sys
import time
import threading
import contextlib
from contextlib import contextmanager

from io import StringIO
import pickle as pkl
import tkinter as tk

@contextmanager
def stdoutIO(stdout=None):
    old = sys.stdout
    if stdout is None:
        stdout = StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old

class GUI():
    # TODO(dreamer): HOW DO I HANDLE USER INPUT????
    def __init__(self, window):
        self.engine = Engine.load()
        
        self.history = []
        
        self.state_str = tk.StringVar()
        self.state_str.set("Stopped")
        
        self.window = window
        self.window.protocol("WM_DELETE_WINDOW", self.quit)
        self.window.title("Python Engine")
        self.window.geometry("500x500")
        
        self.frame = tk.Frame(self.window)
        self.frame.pack_propagate(0)
        
        self.control_frame = tk.Frame(self.frame)
        self.state_lbl = tk.Label(self.control_frame, textvariable=self.state_str)
        self.state_lbl.grid(row=0, column=0)
        # self.start_stop_btn = tk.Button(self.control_frame, text="Start", command=self.startEngine)
        # self.start_stop_btn.grid(row=0, column=1)
        self.control_frame.grid(row=0, column=0)
        
        self.engine_frame = tk.Frame(self.frame)
        self.engine_sb = tk.Scrollbar(self.engine_frame)
        self.engine_text = tk.Text(self.engine_frame, height=13, width=60, yscrollcommand=self.engine_sb.set, wrap=tk.WORD, state=tk.DISABLED)
        self.engine_sb.config(command=self.engine_text.yview)
        self.engine_sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.engine_text.pack(side=tk.LEFT, fill=tk.BOTH)
        self.engine_frame.grid(row=1, column=0)
        
        self.code_frame = tk.Frame(self.frame)
        self.code_entry_frame = tk.Frame(self.code_frame)
        self.code_sb = tk.Scrollbar(self.code_entry_frame)
        self.code_text = tk.Text(self.code_entry_frame, height=13, width=60, yscrollcommand=self.code_sb.set, wrap=tk.WORD)
        self.code_sb.config(command=self.engine_text.yview)
        self.code_sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.code_text.bind("<Escape>", self.clearCodeText)
        self.code_text.pack(side=tk.LEFT, fill=tk.BOTH)
        self.code_entry_frame.grid(row=0, column=0)
        self.post_btn = tk.Button(self.code_frame, text="Post", command=self.postCode)
        self.post_btn.grid(row=1, column=0)
        self.code_frame.grid(row=2, column=0)
        
        self.frame.pack()
        self.window.after(0, self.startEngine)
        
    def quit(self):
        self.engine.stop()
        self.window.destroy()
        
    def update(self):
        selection = self.engine_text.curselection()
        if selection:
            self.engine_text.selection_clear(selection)
        self.window.after(50, self.update)
        
    def startEngine(self):
        self.engine.start()
        # self.start_stop_btn.configure(text="Stop", command=self.stopEngine)
        self.state_str.set("Running")
    #
    def stopEngine(self):
        self.engine.stop()
        Engine.save(self.engine)
        # self.start_stop_btn.configure(text="Start", command=self.startEngine)
        self.state_str.set("Stopped")
        
    def clearCodeText(self, event=None):
        self.code_text.delete(1.0, tk.END)
        
    def postCode(self):
        code = self.code_text.get(1.0, tk.END)
        self.clearCodeText()
        
        while code[-1] == "\n":
            code = code[:-1]
        code = code + "\n"
        
        self.log(code)
        if self.engine.running:
            self.engine.addToStack("""{}""".format(code))
            
    def log(self, val):
        # if val[-1] == "\n":
        #     val = val[:-1]
        if not self.engine_text.compare("end-1c", "==", "1.0"):
            val = "\n" + val
        
        
        self.engine_text.configure(state=tk.NORMAL)
        self.engine_text.insert(tk.END, val)
        
        self.engine_text.yview(tk.END)
        self.engine_text.configure(state=tk.DISABLED)

class Engine():
    SAVE_FOLDER = "data"
    SAVE_FILE = "saved.pkl"
    def __init__(self):
        self.startup = []
        self.stack = []
        self.history = []
        
        self.running = False
        self.thread = None
        
    def save(engine):
        save_path = Engine.SAVE_FOLDER + "\\" + Engine.SAVE_FILE
        if not os.path.exists(Engine.SAVE_FOLDER):
            os.mkdir(Engine.SAVE_FOLDER)
        with open(save_path, 'wb') as sf:
            pkl.dump(engine, sf)
        
    def load():
        save_path = Engine.SAVE_FOLDER + "\\" + Engine.SAVE_FILE
        if os.path.exists(save_path):
            with open(save_path, 'rb') as lf:
                return pkl.load(lf)
        engine = Engine()
        Engine.save(engine)
        return engine
        
    def addToStartup(self, code):
        self.startup.append(code)
        
    def addToStack(self, code):
        self.stack.append(code)
        
    def addToHistory(self, code):
        self.history.append(code)
        
    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self.run)
        self.thread.start()
            
    def stop(self):
        if not self.running:
            return
        self.running = False
        while self.thread.isAlive():
            try:
                self.thread.join(1)
            except:
                time.sleep(.01)
        self.thread = None
        
    def run(self):
        for i in range(len(self.startup)):
            code = self.startup[i]
            with stdoutIO() as out:
                try:
                    gui.log(code+"\n")
                    exec(code)
                except Exception as e:
                    gui.log(e)
                    del self.startup[i]
                    i -= 1
                finally:
                    self.history.append(code)
            gui.log(out.getvalue())
                
        while self.running:
            if self.stack:
                code = self.stack.pop()
                with stdoutIO() as out:
                    try:
                        exec(code)
                    except Exception as e:
                        gui.log(str(e))
                    finally:
                        self.addToHistory(code)
                gui.log(out.getvalue())
            else:
                time.sleep(.1)
    
root = tk.Tk()
gui = GUI(root)


root.mainloop()