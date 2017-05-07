import sys
import logging

from tkinter import Frame, Scrollbar, Text, NSEW, RIGHT, INSERT, Menu, END, Tk
from tkinter.filedialog import askopenfile, asksaveasfile

from idlelib.ColorDelegator import ColorDelegator
from idlelib.MultiStatusBar import MultiStatusBar
from idlelib.Percolator import Percolator

from pyeditor.config import DEFAULT_FILETYPES, BASE_PATH, DEFAULTEXTENSION
from pyeditor.constants import BREAK
from pyeditor.example_scripts import DEFAULT_MCPI_SCRIPT, DEFAULT_SCRIPT
from pyeditor.minecraft_specials import MinecraftSpecials
from pyeditor.python_files import PythonFiles


log = logging.getLogger(__name__)


class EditorWindow:
    def __init__(self):
        self.root = Tk(className="EDITOR")

        self.python_files = PythonFiles()


        self.root.geometry("%dx%d+%d+%d" % (
            self.root.winfo_screenwidth() * 0.6, self.root.winfo_screenheight() * 0.6,
            self.root.winfo_screenwidth() * 0.1, self.root.winfo_screenheight() * 0.1
        ))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.base_title = "PyEditor"
        self.root.title(self.base_title)

        # self.top = top = windows.ListedToplevel(root, menu=self.menubar)

        self.text_frame = Frame(master=self.root)
        self.vbar = Scrollbar(self.text_frame, name='vbar')

        self.text = Text(master=self.root, background="white")
        self.text.bind("<Tab>", self.tab_event)
        self.text.grid(row=0, column=0, sticky=NSEW)

        #TODO: find a right height
        self.text1 = Text(master=self.root, height=20)
        self.text1.grid(row=1, column=0, sticky=NSEW)

        self.text.focus_set()

        # autocomplete_w.AutoCompleteWindow(self.text)

        p = Percolator(self.text)
        d = ColorDelegator()
        p.insertfilter(d)

        # add statusbar to window
        self.init_statusbar()

        # add menu to window
        self.init_menu()

        # Add special RPi/Minecraft features, if available
        self.rpi = MinecraftSpecials(self)

        if self.rpi.mcpi_available:
            # minecraft is available
            self.set_content(DEFAULT_MCPI_SCRIPT)
            if not self.rpi.is_running:
                self.rpi.startup_minecraft()
        else:
            # no minecraft available
            self.set_content(DEFAULT_SCRIPT)

        self.root.update()

    ###########################################################################
    # Status bar

    def init_statusbar(self):
        self.status_bar = MultiStatusBar(self.root)
        if sys.platform == "darwin":
            # Insert some padding to avoid obscuring some of the statusbar
            # by the resize widget.
            self.status_bar.set_label('_padding1', '    ', side=RIGHT)
        self.status_bar.grid(row=2, column=0)

        self.text.bind("<<set-line-and-column>>", self.set_line_and_column)
        self.text.event_add("<<set-line-and-column>>",
                            "<KeyRelease>", "<ButtonRelease>")
        self.text.after_idle(self.set_line_and_column)

    def set_line_and_column(self, event=None):
        line, column = self.text.index(INSERT).split('.')
        self.status_bar.set_label('column', 'Column: %s' % column)
        self.status_bar.set_label('line', 'Line: %s' % line)

    ###########################################################################
    # Menu

    def init_menu(self):
        self.menubar = Menu(self.root)
        filemenu = Menu(self.menubar, tearoff=0)

        self.menubar.add_command(label="Run", command=self.command_run)
        self.menubar.add_command(label="Load", command=self.command_load_file)
        # filemenu.add_command(label="Load", command=self.command_load_file)
        self.menubar.add_command(label="Save", command=self.command_save_file)
        self.menubar.add_command(label="Exit", command=self.root.quit)
        #
        # self.menubar.add_cascade(label="File", menu=filemenu)

        self.root.config(menu=self.menubar)

    def command_run(self):
        source_listing = self.get_content()
        self.python_files.run_source_listing(source_listing)

    def command_load_file(self):
        infile = askopenfile(
            parent=self.root,
            mode="r",
            title="Select a Python file to load",
            filetypes=DEFAULT_FILETYPES,
            initialdir=BASE_PATH,
        )
        if infile is not None:
            source_listing = infile.read()
            infile.close()
            self.set_content(source_listing)

            # self.setup_filepath(infile.name)

    def command_save_file(self):
        outfile = asksaveasfile(
            parent=self.root,
            mode="w",
            filetypes=DEFAULT_FILETYPES,
            defaultextension=DEFAULTEXTENSION,
            initialdir=BASE_PATH,
        )
        if outfile is not None:
            content = self.get_content()
            outfile.write(content)
            outfile.close()
            # self.setup_filepath(outfile.name)

    ###########################################################################

    def get_content(self):
        content = self.text.get("1.0", END)
        content = content.strip()
        return content

    def set_content(self, source_listing):
#        self.text.config(state=Tkinter.NORMAL)
        self.text.delete("1.0", END)

        log.critical("insert %i Bytes listing.", len(source_listing))
        self.text.insert(END, source_listing)

#        self.text.config(state=Tkinter.DISABLED)
        self.text.mark_set(INSERT, '1.0') # Set cursor at start
        self.text.focus()

    ###########################################################################

    indent_pad=" "*4
    def tab_event(self, event):
        log.debug("Tab event")
        self.text.insert("insert", self.indent_pad)
        return BREAK

    ###########################################################################