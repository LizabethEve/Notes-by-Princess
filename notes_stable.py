import os
import json
import sys
import customtkinter as ctk
import tkinter as tk
from PIL import Image
from Images.recolor import batch_recolor_fast
import tkinter.font as tkfont

# constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NOTES_DIR = os.path.join(BASE_DIR, "notes")
THEME_FILE = os.path.join(BASE_DIR, "theme_state.json")
FONT_FILE = os.path.join(BASE_DIR, "font_state.json")
IMAGES = os.path.join(BASE_DIR, "Images")
os.makedirs(NOTES_DIR, exist_ok=True)

BULLETS = ("• ", "- ", "* ")



# >>>>>>>>>>>>>>>>>>>>>>>>
# Initialization
# <<<<<<<<<<<<<<<<<<<<<<<<


class ThemedDialog(ctk.CTkToplevel):
    def __init__(self, app, owner, title, width=500, height=400):
        super().__init__(app)

        self.owner = owner

        self.title(title)
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)
        self.transient(app)
        self.after(20, self.grab_set)

        # THEME
        self.configure(fg_color=self.owner.background_color)

        # main container
        self.container = ctk.CTkFrame(
            self,
            fg_color=self.owner.background_color
        )
        self.container.pack(fill="both", expand=True, padx=10, pady=10)


class FileDialog(ThemedDialog):
    def __init__(self, app, owner, mode="open", initial_dir=None):
        super().__init__(app, owner, "Select File", 600, 500)

        self.mode = mode
        self.current_dir = initial_dir or NOTES_DIR
        self.selected_file = None

        # path label
        self.path_label = ctk.CTkLabel(
            self.container,
            text=self.current_dir,
            text_color=self.owner.text_color,
            fg_color=self.owner.background_color,
            corner_radius=5,
        )
        self.path_label.pack(anchor="w", pady=(0, 5))

        # file list
        self.listbox = tk.Listbox(
            self.container,
            bg=self.owner.background_color,
            fg=self.owner.text_color,
            #text_color=self.owner.text_color,
            selectbackground=self.owner.hover_color,
            relief="flat"
        )
        self.listbox.pack(fill="both", expand=True)

        self.listbox.bind("<Double-Button-1>", self.on_double_click)

        # filename entry (for save)
        if mode == "save":
            self.filename_entry = ctk.CTkEntry(
                self.container,
                justify="center",
                fg_color=self.owner.background_color,
                state="normal",
                text_color=self.owner.text_color,
                border_color=self.owner.frame_color,
                placeholder_text="Enter filename..."
            )
            self.filename_entry.pack(fill="x", pady=5)

        # buttons
        btn_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        btn_frame.pack(fill="x", pady=5)

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            border_width=0,
            text_color=self.owner.text_color,
            fg_color=self.owner.button_color,
            hover_color=self.owner.hover_color,
            command=self.destroy
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Select",
            border_width=0,
            text_color=self.owner.text_color,
            fg_color=self.owner.button_color,
            hover_color=self.owner.hover_color,
            command=self.select
        ).pack(side="right")

        try:
            self.load_files()
        except:
            print("\n\nError: load_files failed completely.\n\n")

    def load_files(self):
        self.listbox.delete(0, tk.END)

        # add parent dir
        if os.path.dirname(self.current_dir):
            self.listbox.insert(tk.END, "..")

        for f in os.listdir(self.current_dir):
            self.listbox.insert(tk.END, f)

    def on_double_click(self, event):
        selection = self.listbox.get(tk.ACTIVE)
        path = os.path.join(self.current_dir, selection)

        if selection == "..":
            self.current_dir = os.path.dirname(self.current_dir)
        elif os.path.isdir(path):
            self.current_dir = path
        else:
            self.selected_file = path
            self.destroy()
            return

        self.path_label.configure(text=self.current_dir)
        self.load_files()

    def select(self):
        selection = self.listbox.get(tk.ACTIVE)

        if self.mode == "open":
            path = os.path.join(self.current_dir, selection)
            if os.path.isfile(path):
                self.selected_file = path

        elif self.mode == "save":
            name = self.filename_entry.get()
            if name:
                self.selected_file = os.path.join(self.current_dir, name)

        self.destroy()


class ColorPicker(ThemedDialog):
    def __init__(self, app, owner):
        super().__init__(app, owner, "Pick Color", 350, 400)

        self.color = "#ffffff"
        self.temp_color = self.color
        self.confirmed = False

        self.r = tk.IntVar(value=255)
        self.g = tk.IntVar(value=255)
        self.b = tk.IntVar(value=255)

        for label, var in [("R", self.r), ("G", self.g), ("B", self.b)]:
            ctk.CTkLabel(self.container, text=label,
                         fg_color=self.owner.background_color,
                         text_color=self.owner.text_color,
                         ).pack()
            ctk.CTkSlider(
                self.container,
                from_=0,
                to=255,
                variable=var,
                border_width=0,
                #border_color=self.owner.text_color,
                fg_color=self.owner.background_color,
                progress_color=self.owner.highlight_color,
                button_color=self.owner.text_color,
                button_hover_color=self.owner.hover_color,
                command=lambda e: self.update_color()
            ).pack(fill="x", padx=10)

        self.preview = ctk.CTkFrame(self.container, height=50,
                                    border_width=0,
                                    fg_color=self.owner.background_color,
                                    )
        self.preview.pack(fill="x", padx=10, pady=10)

        self.hex_entry = ctk.CTkEntry(self.container,
                                    justify="center",
                                    fg_color=self.owner.background_color,
                                    state="normal",
                                    text_color=self.owner.text_color,
                                    border_color=self.owner.frame_color,
                                    )
        self.hex_entry.pack(fill="x", padx=10)

        ctk.CTkButton(
            self.container,
            text="Select",
            border_width=0,
            text_color=self.owner.text_color,
            fg_color=self.owner.button_color,
            hover_color=self.owner.hover_color,
            command=self.confirm
        ).pack(pady=10)

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.update_color()

    def update_color(self):
        self.temp_color = f"#{self.r.get():02x}{self.g.get():02x}{self.b.get():02x}"
        self.preview.configure(fg_color=self.temp_color)
        self.hex_entry.delete(0, "end")
        self.hex_entry.insert(0, self.temp_color)

    def confirm(self):
        self.confirmed = True
        self.color = self.hex_entry.get()
        self.destroy()

    def cancel(self):
        # do NOT update self.color
        self.destroy()


class Notes():
    def __init__(self):
        # define ctk
        self.app = ctk.CTk()
        self.app.title("Notes")
        self.app.geometry("1920x1080")
        if sys.platform == "win32":
            self.app.iconbitmap("App.ico")
        elif sys.platform == "darwin":
            pass
        else:
            app_image_path = os.path.join(BASE_DIR, "App.png")
            self.app_image = tk.PhotoImage(file=app_image_path)
            self.app.iconphoto(True, self.app_image)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # define variables and all that other good stuff
        self.current_file = None
        self.active_tags = {"bold": False, "italic": False, "bold_italic": False}
        self.font_tags = {}
        self.themes = {
            "purple": ["#38323b", "#9a6bd6", "#38323b", "#efdefa", "#9a6bd6", "#cab0db", "#efdefa", "#38323b"],
            "yellow": ["#3b3b32", "#d6d56b", "#3b3b32", "#faf9de", "#d6d56b", "#dbd9b0", "#faf9de", "#3b3b32"],
            "red": ["#3b3232", "#d66b6b", "#3b3232", "#fadede", "#d66b6b", "#dbb0b0", "#fadede", "#3b3232"],
            "green": ["#343b32", "#70d66b", "#343b32", "#dffade", "#70d66b", "#b2dbb0", "#dffade", "#343b32"],
            "blue": ["#32323b", "#6b7cd7", "#32323b", "#dedffa", "#6b7cd7", "#b0b2db", "#dedffa", "#32323b"],
            "custom": ["#", "#", "#", "#", "#", "#", "#", "#"],
            }
        self.elements = [
            ("Background Color", "background_color"),
            ("Hover Color", "hover_color"),
            ("Button Color", "button_color"),
            ("Frame Color", "frame_color"),
            ("Divider Color", "divider_color"),
            ("Highlight Color", "highlight_color"),
            ("Text Color", "text_color"),
            ("Highlighted Text Color", "highlighted_text_color"),
            ]
        self.default = self.themes["purple"]
        self.background_color = self.default[0]
        self.hover_color = self.default[1]
        self.button_color = self.default[2]
        self.frame_color = self.default[3]
        self.divider_color = self.default[4]
        self.highlight_color = self.default[5]
        self.text_color = self.default[6]
        self.highlighted_text_color = self.default[7]

        self.fonts_shown = False
        self.bottom_shown = False
        self.app_font_customize = False

        # call functions
        self.load_theme_state()
        self.load_font_state()
        self.app.protocol("WM_DELETE_WINDOW", self.close_app)
        self.app.configure(fg_color=self.background_color)

        # widgets outside of the main frame
        self.paned = tk.PanedWindow(self.app, orient="horizontal", sashwidth=2, bd=1, bg=self.divider_color)
        self.paned.pack(fill="both", expand=True)

        self.sidebar = ctk.CTkFrame(self.paned, width=200, fg_color=self.background_color, corner_radius=5)
        self.paned.add(self.sidebar, minsize=150)

        self.sidebar_label = ctk.CTkLabel(self.sidebar,
                                        text="Saved Notes",
                                        font=(self.app_font_name, 16),
                                        text_color=self.text_color,
                                        fg_color=self.background_color
                                        )
        self.sidebar_label.pack(pady=5)

        self.file_frame = ctk.CTkScrollableFrame(self.sidebar,
                                                corner_radius=5,
                                                border_width=0,
                                                fg_color=self.background_color,
                                                scrollbar_fg_color=self.background_color,
                                                scrollbar_button_color=self.frame_color,
                                                scrollbar_button_hover_color=self.hover_color,
                                                )
        self.file_frame.pack(fill="both", expand=True, padx=2, pady=2)

        self.main_frame = tk.PanedWindow(
            self.paned,
            orient="vertical",
            sashwidth=2,
            bd=0,
            bg=self.divider_color
            )
        #self.main_frame.pack(fill="both", expand=True)

        # create the main frame inside paned and refresh file window
        #self.main_frame = ctk.CTkFrame(self.paned, fg_color=self.background_color, corner_radius=5)
        self.paned.add(self.main_frame, minsize=300)
        try:
            self.refresh_file_frame()
        except:
            print("Error: self.refresh_file_frame() failed completely.")


# >>>>>>>>>>>>>>>>>>>>>>>>
# UI
# <<<<<<<<<<<<<<<<<<<<<<<<

    # function called on app open or on main screen
    def show_welcome(self):
        # clear all widgets attatched to the main frame
        try:
            self.clear_main()
        except:
            print("Error: self.clear_main() failed completely.")

        self.main_bg = ctk.CTkFrame(self.main_frame,
                                    bg_color=self.background_color,
                                    fg_color=self.background_color,
                                    corner_radius=5,
                                    border_width=0,)
        self.main_frame.add(self.main_bg)

        # welcome screen widgets
        self.title = ctk.CTkLabel(self.main_bg,
                             text="Notes by Princess",
                             font=(self.app_font_name, 28),
                             text_color=self.text_color,
                             )
        self.title.place(relx=0.5, rely=0.2, anchor="center")

        self.new_button = ctk.CTkButton(self.main_bg,
                                   text="New File",
                                   fg_color=self.button_color,
                                   hover_color=self.hover_color,
                                   border_width=0,
                                   width=100,
                                   height=20,
                                   font=(self.app_font_name, 16),
                                   corner_radius=5,
                                   text_color=self.text_color,
                                   command=self.new_file,
                                   )
        self.new_button.place(relx=0.4, rely=0.5, anchor="center")

        self.open_button = ctk.CTkButton(self.main_bg,
                                    text="Open File",
                                    fg_color=self.button_color,
                                    hover_color=self.hover_color,
                                    border_width=0,
                                    width=100,
                                    height=20,
                                    font=(self.app_font_name, 16),
                                    corner_radius=5,
                                    text_color=self.text_color,
                                    command=self.open_file_dialog)
        self.open_button.place(relx=0.6, rely=0.5, anchor="center")

        self.theme_button = ctk.CTkButton(self.main_bg,
                                          text="Theme",
                                          fg_color=self.button_color,
                                          hover_color=self.hover_color,
                                          border_width=0,
                                          width=50,
                                          height=20,
                                          font=(self.app_font_name, 16),
                                          corner_radius=5,
                                          text_color=self.text_color,
                                          command=self.show_theme_editor)
        self.theme_button.place(relx=0.01, rely=0.99, anchor="sw")

    # function called when user clicks a file or theme editor
    def show_editor(self):
        self.editor_container = ctk.CTkFrame(self.main_frame, bg_color=self.background_color, fg_color=self.background_color, corner_radius=5,)
        self.main_frame.add(self.editor_container, minsize=500)

        self.show_toolbar()

        # editor widgets
        self.note_title_case = ctk.CTkFrame(self.editor_container,
                                            corner_radius=5,
                                            fg_color=self.background_color,
                                            border_width=0,
                                            height=75,
                                            )
        self.note_title_case.pack(side="top", fill="x")

        # get title of note/page, else title = untitled
        if self.current_file:
            title = os.path.splitext(os.path.basename(self.current_file))[0]
        else:
            title = "Untitled"

        self.note_title = ctk.CTkLabel(self.note_title_case,
                                       text=title,
                                       height=75,
                                       width=100,
                                       corner_radius=5,
                                       font=(self.app_font_name, 30),
                                       text_color=self.text_color,
                                       bg_color=self.background_color)
        self.note_title.place(relx=0.5, rely=0.5, anchor="center")

        self.text_bg = ctk.CTkFrame(self.editor_container, corner_radius=5, fg_color=self.background_color)
        self.text_bg.pack(side="top", expand=True, fill="both", padx=5, pady=(5, 0))

        self.notebox = tk.Text(self.text_bg,
                       bg=self.background_color,
                       fg=self.text_color,
                       insertbackground=self.text_color,
                       font=(self.font_name, self.font_size),
                       bd=0,
                       wrap="word",
                       yscrollcommand=True,
                       selectbackground=self.highlight_color,
                       selectforeground=self.highlighted_text_color,
                       highlightthickness=0,
                       relief="flat")
        self.notebox.pack(fill="both", expand=True, padx=50, pady=50)

        # configure text tags
        self.notebox.tag_config("bold")
        self.notebox.tag_config("italic")
        self.notebox.tag_config("bold_italic")

        self.notebox.bind("<Return>", self.handle_enter)
        self.notebox.bind("<Tab>", self.handle_tab)
        self.notebox.bind("<Shift-Tab>", self.handle_shift_tab)
        self.notebox.bind("<KeyPress>", self.on_key_press)

    # function called by show_editor, creates toolbar
    def show_toolbar(self):
        # toolbar frame
        self.toolbar_case = ctk.CTkFrame(self.editor_container,
                                         border_width=0,
                                         fg_color=self.background_color,
                                         corner_radius=5,
                                         width=40,
                                         )
        self.toolbar_case.pack(side="right", fill="y")

        self.toolbar_line = ctk.CTkFrame(self.toolbar_case,
                                         border_width=1,
                                         border_color=self.frame_color,
                                         fg_color=self.background_color,
                                         corner_radius=5,
                                         width=2
                                         )
        self.toolbar_line.place(relx=0.0, rely=0.5, relheight=1.0, anchor="w")

        self.toolbar = ctk.CTkFrame(self.toolbar_case,
                                    fg_color=self.background_color,
                                    border_width=0)
        self.toolbar.place(relx=0.5, rely=0.001, anchor="n")

        self.back_image = ctk.CTkImage(
                                    light_image=Image.open(os.path.join(IMAGES, "Back_Arrow.png")),
                                    dark_image=Image.open(os.path.join(IMAGES, "Back_Arrow.png")),
                                    size=(15, 15)
        )

        self.save_image = ctk.CTkImage(
                                    light_image=Image.open(os.path.join(IMAGES, "Save.png")),
                                    dark_image=Image.open(os.path.join(IMAGES, "Save.png")),
                                    size=(15, 15)
        )

        self.font_image = ctk.CTkImage(
                                    light_image=Image.open(os.path.join(IMAGES, "Font.png")),
                                    dark_image=Image.open(os.path.join(IMAGES, "Font.png")),
                                    size=(15, 15)
        )

        self.bold_image = ctk.CTkImage(
                                    light_image=Image.open(os.path.join(IMAGES, "Bold.png")),
                                    dark_image=Image.open(os.path.join(IMAGES, "Bold.png")),
                                    size=(15, 15)
        )

        self.italics_image = ctk.CTkImage(
                                    light_image=Image.open(os.path.join(IMAGES, "Italics.png")),
                                    dark_image=Image.open(os.path.join(IMAGES, "Italics.png")),
                                    size=(15, 15)
        )

        self.bulleted_image = ctk.CTkImage(
                                    light_image=Image.open(os.path.join(IMAGES, "Bulleted_List.png")),
                                    dark_image=Image.open(os.path.join(IMAGES, "Bulleted_List.png")),
                                    size=(15, 15)
        )

        # toolbar widgets
        self.back_button = ctk.CTkButton(self.toolbar,
                                    text="",
                                    image=self.back_image,
                                    fg_color=self.button_color,
                                    hover_color=self.hover_color,
                                    border_width=1,
                                    border_color=self.frame_color,
                                    width=30,
                                    corner_radius=5,
                                    text_color=self.text_color,
                                    command=self.back_pressed
                                    )
        self.back_button.pack(pady=1)

        self.save_button = ctk.CTkButton(self.toolbar,
                                    text="",
                                    image=self.save_image,
                                    fg_color=self.button_color,
                                    hover_color=self.hover_color,
                                    border_width=1,
                                    border_color=self.frame_color,
                                    width=30,
                                    corner_radius=5,
                                    text_color=self.text_color,
                                    command=self.save_file
                                    )
        self.save_button.pack(pady=1)

        self.bold_button = ctk.CTkButton(self.toolbar,
                                    text="",
                                    image=self.bold_image,
                                    fg_color=self.button_color,
                                    hover_color=self.hover_color,
                                    border_width=1,
                                    border_color=self.frame_color,
                                    width=30,
                                    corner_radius=5,
                                    text_color=self.text_color,
                                    command=self.toggle_bold
                                    )
        self.bold_button.pack(pady=1)

        self.italic_button = ctk.CTkButton(self.toolbar,
                                      text="",
                                      image=self.italics_image,
                                      fg_color=self.button_color,
                                      hover_color=self.hover_color,
                                      border_width=1,
                                      border_color=self.frame_color,
                                      width=30,
                                      corner_radius=5,
                                      text_color=self.text_color,
                                      command=self.toggle_italic
                                      )
        self.italic_button.pack(pady=1)

        self.font_button = ctk.CTkButton(self.toolbar,
                                      text="",
                                      image=self.font_image,
                                      fg_color=self.button_color,
                                      hover_color=self.hover_color,
                                      border_width=1,
                                      border_color=self.frame_color,
                                      width=30,
                                      corner_radius=5,
                                      text_color=self.text_color,
                                      command=self.show_fonts
                                      )
        self.font_button.pack(pady=1)

        self.bullet_button = ctk.CTkButton(self.toolbar,
                                      text="",
                                      image=self.bulleted_image,
                                      fg_color=self.button_color,
                                      hover_color=self.hover_color,
                                      border_width=1,
                                      border_color=self.frame_color,
                                      width=30,
                                      corner_radius=5,
                                      text_color=self.text_color,
                                      command=self.insert_bullet
                                      )
        self.bullet_button.pack(pady=1)

        self.plus_button = ctk.CTkButton(self.toolbar,
                                      text="+",
                                      #image=self.bulleted_image,
                                      fg_color=self.button_color,
                                      hover_color=self.hover_color,
                                      border_width=1,
                                      border_color=self.frame_color,
                                      width=30,
                                      corner_radius=5,
                                      text_color=self.text_color,
                                      command=self.increase_font_size
                                      )
        self.plus_button.pack(pady=1)

        self.minus_button = ctk.CTkButton(self.toolbar,
                                      text="-",
                                      #image=self.bulleted_image,
                                      fg_color=self.button_color,
                                      hover_color=self.hover_color,
                                      border_width=1,
                                      border_color=self.frame_color,
                                      width=30,
                                      corner_radius=5,
                                      text_color=self.text_color,
                                      command=self.decrease_font_size
                                      )
        self.minus_button.pack(pady=1)

    # function called when user presses theme button
    def show_theme_editor(self):
        # clear widgets and call functions to create theme editor
        self.clear_main()
        self.show_editor()
        self.show_bottom_window()
        self.show_theme_widgets()

        self.app.update_idletasks()

        # change the title and add filler text to the notebox
        self.note_title.configure(text="Theme Customization")
        self.notebox.insert(tk.END, "Customize your app theme below...")

    # function called by show_theme_editor or font button, creates bottom scrool window
    def show_bottom_window(self):
        self.bottom_shown = True
        # bottom window widgets
        self.bottom_window_case = ctk.CTkFrame(self.main_frame,
                                                 corner_radius=5,
                                                 fg_color=self.background_color,
                                                 )
        self.main_frame.add(self.bottom_window_case, minsize=200)

        self.bottom_scroll = ctk.CTkScrollableFrame(self.bottom_window_case,
                                                 corner_radius=5,
                                                 border_width=0,
                                                 fg_color=self.background_color,
                                                 scrollbar_fg_color=self.background_color,
                                                 scrollbar_button_color=self.frame_color,
                                                 scrollbar_button_hover_color=self.hover_color,
                                                 )
        self.bottom_scroll._parent_canvas.configure(yscrollincrement=0.5)
        self.bottom_scroll.pack(fill="both", side="left", expand=True, padx=2, pady=2)

    def app_font(self):
        if not self.app_font_customize:
            self.app_font_button.configure(fg_color=self.hover_color)
            self.app_font_customize = True
        else:
            self.app_font_button.configure(fg_color=self.background_color)
            self.app_font_customize = False

    def show_fonts(self):
        if not self.fonts_shown:
            self.fonts_shown = True
            if self.bottom_shown:
                self.clear_bottom()
            self.show_bottom_window()

            font_settings_window = ctk.CTkFrame(
                self.bottom_window_case,
                width=100,
                border_width=1,
                border_color=self.frame_color,
                corner_radius=5,
                fg_color=self.background_color,
            )
            font_settings_window.pack(fill="y", side="right")

            size_label = ctk.CTkLabel(
                font_settings_window,
                text="Size",
                text_color=self.text_color,
                fg_color=self.background_color
            )
            size_label.pack(pady=(10, 0))

            size_var = tk.StringVar(value=str(self.font_size))
            size_spinner = ctk.CTkEntry(
                font_settings_window,
                textvariable=size_var,
                width=60,
                justify="center",
                fg_color=self.background_color,
                text_color=self.text_color,
                border_color=self.frame_color,
            )
            size_spinner.pack(padx=10, pady=5)
            size_spinner.bind("<Return>", lambda e: self.change_font_size(size_var.get()))

            for size in [8, 10, 12, 14, 16, 18, 24, 32, 48, 72]:
                ctk.CTkButton(
                    font_settings_window,
                    text=str(size),
                    width=60,
                    fg_color=self.button_color,
                    hover_color=self.hover_color,
                    text_color=self.text_color,
                    command=lambda s=size: self.change_font_size(s)
                ).pack(padx=10, pady=2)

            self.app_font_button = ctk.CTkButton(
                font_settings_window,
                text="App Font",
                width=60,
                fg_color=self.button_color,
                hover_color=self.hover_color,
                text_color=self.text_color,
                command=lambda: self.app_font()
            )
            self.app_font_button.pack(padx=10, pady=10)

            self.app.update_idletasks()  # IMPORTANT

            fonts = list(tkfont.families())

            #print(f"Found {len(fonts)} fonts")  # debug

            fonts = sorted(set(fonts))  # remove duplicates

            if not fonts:
                ctk.CTkLabel(self.bottom_scroll, text="No fonts found").pack()
                return

            for font_name in fonts:
                btn = ctk.CTkButton(
                    self.bottom_scroll,
                    text=font_name,
                    font=(font_name, 14),  # show actual font style
                    fg_color=self.button_color,
                    hover_color=self.hover_color,
                    text_color=self.text_color,
                    anchor="w",
                    command=lambda f=font_name: self.set_font(f)
                )
                btn.pack(fill="x", padx=5, pady=2)
        else:
            self.fonts_shown = False
            self.clear_bottom()

    # function called by show_theme_editor when user clicks theme button
    def show_theme_widgets(self):
        # disable toolbar buttons for the theme editor
        self.bold_button.configure(command=None)
        self.font_button.configure(command=None)
        self.italic_button.configure(command=None)
        self.save_button.configure(command=None)
        self.bullet_button.configure(command=None)
        self.plus_button.configure(command=None)
        self.minus_button.configure(command=None)

        # widgets attatched to the bottom scroll window
        self.pre_button_frame = ctk.CTkFrame(self.bottom_scroll,
                                         corner_radius=5,
                                         border_width=0,
                                         fg_color=self.background_color,
                                         height=100,
                                         )
        self.pre_button_frame.pack(side="top", fill="x")

        self.custom_button_frame = ctk.CTkFrame(self.bottom_scroll,
                                                 corner_radius=5,
                                                 border_width=0,
                                                 height=700,
                                                 fg_color=self.background_color,
                                                 )
        self.custom_button_frame.pack(side="bottom", fill="both", expand=True)

        self.yellow_button = ctk.CTkButton(self.pre_button_frame,
                                      text="Yellow",
                                      fg_color=self.button_color,
                                      hover_color=self.hover_color,
                                      border_width=0,
                                      corner_radius=5,
                                      font=(self.app_font_name, 18),
                                      text_color=self.text_color,
                                      command=lambda: self.change_theme("yellow")
                                      )
        self.yellow_button.place(relx=0.2, rely=0.5, anchor="center")

        self.purple_button = ctk.CTkButton(self.pre_button_frame,
                                      text="Purple",
                                      fg_color=self.button_color,
                                      hover_color=self.hover_color,
                                      border_width=0,
                                      corner_radius=5,
                                      font=(self.app_font_name, 18),
                                      text_color=self.text_color,
                                      command=lambda: self.change_theme("purple")
                                      )
        self.purple_button.place(relx=0.35, rely=0.5, anchor="center")

        self.red_button = ctk.CTkButton(self.pre_button_frame,
                                      text="Red",
                                      fg_color=self.button_color,
                                      hover_color=self.hover_color,
                                      border_width=0,
                                      corner_radius=5,
                                      font=(self.app_font_name, 18),
                                      text_color=self.text_color,
                                      command=lambda: self.change_theme("red")
                                      )
        self.red_button.place(relx=0.5, rely=0.5, anchor="center")

        self.green_button = ctk.CTkButton(self.pre_button_frame,
                                      text="Green",
                                      fg_color=self.button_color,
                                      hover_color=self.hover_color,
                                      border_width=0,
                                      corner_radius=5,
                                      font=(self.app_font_name, 18),
                                      text_color=self.text_color,
                                      command=lambda: self.change_theme("green")
                                      )
        self.green_button.place(relx=0.65, rely=0.5, anchor="center")

        self.blue_button = ctk.CTkButton(self.pre_button_frame,
                                      text="Blue",
                                      fg_color=self.button_color,
                                      hover_color=self.hover_color,
                                      border_width=0,
                                      corner_radius=5,
                                      font=(self.app_font_name, 18),
                                      text_color=self.text_color,
                                      command=lambda: self.change_theme("blue")
                                      )
        self.blue_button.place(relx=0.8, rely=0.5, anchor="center")

        self.customize_seperator = ctk.CTkLabel(self.custom_button_frame,
                                                text="--- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---",
                                                width=700,
                                                text_color=self.text_color,
                                                )
        self.customize_seperator.place(relx=0.5, rely=0.00, anchor="n")

        self.customize_label = ctk.CTkLabel(self.custom_button_frame,
                                            text="Customize:",
                                            fg_color=self.background_color,
                                            font=(self.app_font_name, 25),
                                            text_color=self.text_color,
                                            )
        self.customize_label.place(relx=0.5, rely=0.1, anchor="n")

        self.background_color_button = ctk.CTkButton(self.custom_button_frame,
                                                     text="",
                                                     fg_color=self.background_color,
                                                     border_width=3,
                                                     border_color=self.frame_color,
                                                     width=50,
                                                     height=25,
                                                     hover_color=self.hover_color,
                                                     command=lambda: self.pick_color("background_color"),
                                                     )
        self.background_color_button.place(relx=0.6, rely=0.3, anchor="center")

        self.background_enter_bar = ctk.CTkEntry(self.custom_button_frame,
                                                 placeholder_text=self.background_color,
                                                 justify="center",
                                                 fg_color=self.background_color,
                                                 state="normal",
                                                 font=(self.app_font_name, 18),
                                                 border_color=self.frame_color,
                                                 placeholder_text_color=self.text_color,
                                                 )
        self.background_enter_bar.place(relx=0.45, rely=0.3, anchor="center")
        self.background_enter_bar.bind("<Return>", lambda e: self.set_color_from_entry("background_color", self.background_enter_bar))

        self.background_color_label = ctk.CTkLabel(self.custom_button_frame,
                                                    text=f"Background Color: ",
                                                    font=(self.app_font_name, 18),
                                                    text_color=self.text_color,
                                                    )
        self.background_color_label.place(relx=0.3, rely=0.3, anchor="center")

        self.hover_color_button = ctk.CTkButton(self.custom_button_frame,
                                                     text="",
                                                     fg_color=self.hover_color,
                                                     border_width=3,
                                                     border_color=self.frame_color,
                                                     width=50,
                                                     height=25,
                                                     hover_color=self.hover_color,
                                                     command=lambda: self.pick_color("hover_color"),
                                                     )
        self.hover_color_button.place(relx=0.6, rely=0.4, anchor="center")

        self.hover_enter_bar = ctk.CTkEntry(self.custom_button_frame,
                                                 placeholder_text=self.hover_color,
                                                 justify="center",
                                                 fg_color=self.background_color,
                                                 state="normal",
                                                 font=(self.app_font_name, 18),
                                                 border_color=self.frame_color,
                                                 placeholder_text_color=self.text_color,
                                                 )
        self.hover_enter_bar.place(relx=0.45, rely=0.4, anchor="center")
        self.hover_enter_bar.bind("<Return>", lambda e: self.set_color_from_entry("hover_color", self.hover_enter_bar))

        self.hover_color_label = ctk.CTkLabel(self.custom_button_frame,
                                                    text=f"Hover Color: ",
                                                    font=(self.app_font_name, 18),
                                                    text_color=self.text_color,
                                                    )
        self.hover_color_label.place(relx=0.3, rely=0.4, anchor="center")

        self.button_color_button = ctk.CTkButton(self.custom_button_frame,
                                                     text="",
                                                     fg_color=self.button_color,
                                                     border_width=3,
                                                     border_color=self.frame_color,
                                                     width=50,
                                                     height=25,
                                                     hover_color=self.hover_color,
                                                     command=lambda: self.pick_color("button_color"),
                                                     )
        self.button_color_button.place(relx=0.6, rely=0.5, anchor="center")

        self.button_enter_bar = ctk.CTkEntry(self.custom_button_frame,
                                                 placeholder_text=self.button_color,
                                                 justify="center",
                                                 fg_color=self.background_color,
                                                 state="normal",
                                                 font=(self.app_font_name, 18),
                                                 border_color=self.frame_color,
                                                 placeholder_text_color=self.text_color,
                                                 )
        self.button_enter_bar.place(relx=0.45, rely=0.5, anchor="center")
        self.button_enter_bar.bind("<Return>", lambda e: self.set_color_from_entry("button_color", self.button_enter_bar))

        self.button_color_label = ctk.CTkLabel(self.custom_button_frame,
                                                    text=f"Button Color: ",
                                                    font=(self.app_font_name, 18),
                                                    text_color=self.text_color,
                                                    )
        self.button_color_label.place(relx=0.3, rely=0.5, anchor="center")

        self.frame_color_button = ctk.CTkButton(self.custom_button_frame,
                                                     text="",
                                                     fg_color=self.frame_color,
                                                     border_width=3,
                                                     border_color=self.frame_color,
                                                     width=50,
                                                     height=25,
                                                     hover_color=self.hover_color,
                                                     command=lambda: self.pick_color("frame_color"),
                                                     )
        self.frame_color_button.place(relx=0.6, rely=0.6, anchor="center")

        self.frame_enter_bar = ctk.CTkEntry(self.custom_button_frame,
                                                 placeholder_text=self.frame_color,
                                                 justify="center",
                                                 fg_color=self.background_color,
                                                 state="normal",
                                                 font=(self.app_font_name, 18),
                                                 border_color=self.frame_color,
                                                 placeholder_text_color=self.text_color,
                                                 )
        self.frame_enter_bar.place(relx=0.45, rely=0.6, anchor="center")
        self.frame_enter_bar.bind("<Return>", lambda e: self.set_color_from_entry("frame_color", self.frame_enter_bar))

        self.frame_color_label = ctk.CTkLabel(self.custom_button_frame,
                                                    text=f"Frame Color: ",
                                                    font=(self.app_font_name, 18),
                                                    text_color=self.text_color,
                                                    )
        self.frame_color_label.place(relx=0.3, rely=0.6, anchor="center")

        self.divider_color_button = ctk.CTkButton(self.custom_button_frame,
                                                     text="",
                                                     fg_color=self.divider_color,
                                                     border_width=3,
                                                     border_color=self.frame_color,
                                                     width=50,
                                                     height=25,
                                                     hover_color=self.hover_color,
                                                     command=lambda: self.pick_color("divider_color"),
                                                     )
        self.divider_color_button.place(relx=0.6, rely=0.7, anchor="center")

        self.divider_enter_bar = ctk.CTkEntry(self.custom_button_frame,
                                                 placeholder_text=self.divider_color,
                                                 justify="center",
                                                 fg_color=self.background_color,
                                                 state="normal",
                                                 font=(self.app_font_name, 18),
                                                 border_color=self.frame_color,
                                                 placeholder_text_color=self.text_color,
                                                 )
        self.divider_enter_bar.place(relx=0.45, rely=0.7, anchor="center")
        self.divider_enter_bar.bind("<Return>", lambda e: self.set_color_from_entry("divider_color", self.divider_enter_bar))

        self.divider_color_label = ctk.CTkLabel(self.custom_button_frame,
                                                    text=f"Divider Color: ",
                                                    font=(self.app_font_name, 18),
                                                    text_color=self.text_color,
                                                    )
        self.divider_color_label.place(relx=0.3, rely=0.7, anchor="center")

        self.highlight_color_button = ctk.CTkButton(self.custom_button_frame,
                                                     text="",
                                                     fg_color=self.highlight_color,
                                                     border_width=3,
                                                     border_color=self.frame_color,
                                                     width=50,
                                                     height=25,
                                                     hover_color=self.hover_color,
                                                     command=lambda: self.pick_color("highlight_color"),
                                                     )
        self.highlight_color_button.place(relx=0.6, rely=0.8, anchor="center")

        self.highlight_enter_bar = ctk.CTkEntry(self.custom_button_frame,
                                                 placeholder_text=self.divider_color,
                                                 justify="center",
                                                 fg_color=self.background_color,
                                                 state="normal",
                                                 font=(self.app_font_name, 18),
                                                 border_color=self.frame_color,
                                                 placeholder_text_color=self.text_color,
                                                 )
        self.highlight_enter_bar.place(relx=0.45, rely=0.8, anchor="center")
        self.highlight_enter_bar.bind("<Return>", lambda e: self.set_color_from_entry("highlight_color", self.highlight_enter_bar))

        self.highlight_color_label = ctk.CTkLabel(self.custom_button_frame,
                                                    text=f"Highlight Color: ",
                                                    font=(self.app_font_name, 18),
                                                    text_color=self.text_color,
                                                    )
        self.highlight_color_label.place(relx=0.3, rely=0.8, anchor="center")

        self.text_highlight_color_button = ctk.CTkButton(self.custom_button_frame,
                                                     text="",
                                                     fg_color=self.highlighted_text_color,
                                                     border_width=3,
                                                     border_color=self.frame_color,
                                                     width=50,
                                                     height=25,
                                                     hover_color=self.hover_color,
                                                     command=lambda: self.pick_color("highlighted_text_color"),
                                                     )
        self.text_highlight_color_button.place(relx=0.6, rely=0.9, anchor="center")

        self.text_highlight_enter_bar = ctk.CTkEntry(self.custom_button_frame,
                                                 placeholder_text=self.divider_color,
                                                 justify="center",
                                                 fg_color=self.background_color,
                                                 state="normal",
                                                 font=(self.app_font_name, 18),
                                                 border_color=self.frame_color,
                                                 placeholder_text_color=self.text_color,
                                                 )
        self.text_highlight_enter_bar.place(relx=0.45, rely=0.9, anchor="center")
        self.text_highlight_enter_bar.bind("<Return>", lambda e: self.set_color_from_entry("highlighted_text_color", self.text_highlight_enter_bar))

        self.text_highlight_color_label = ctk.CTkLabel(self.custom_button_frame,
                                                    text=f"Text Highlight Color: ",
                                                    font=(self.app_font_name, 18),
                                                    text_color=self.text_color,
                                                    )
        self.text_highlight_color_label.place(relx=0.3, rely=0.9, anchor="center")

    # function called when user changes themes.
    def change_theme(self, theme_name):
        # define the color picked by user to be passed through function
        if theme_name == "custom":
            theme = [
                self.background_color,
                self.hover_color,
                self.button_color,
                self.frame_color,
                self.divider_color,
                self.highlight_color,
                self.text_color,
                self.highlighted_text_color
            ]
        else:
            theme = self.themes[theme_name]

        # redefine individual colors
        self.background_color = theme[0]
        self.hover_color = theme[1]
        self.button_color = theme[2]
        self.frame_color = theme[3]
        self.divider_color = theme[4]
        self.highlight_color = theme[5]
        self.text_color = theme[6]
        self.highlighted_text_color = theme[7]

        batch_recolor_fast(IMAGES, self.frame_color)

        # reconfigure widgets to apply theme colors
        self.app.configure(fg_color=self.background_color)
        self.paned.configure(bg=self.divider_color)
        self.sidebar_label.configure(fg_color=self.background_color, text_color=self.text_color)
        self.sidebar.configure(fg_color=self.background_color)
        self.file_frame.configure(scrollbar_fg_color=self.background_color, scrollbar_button_color=self.frame_color, scrollbar_button_hover_color=self.hover_color, fg_color=self.background_color)
        self.main_frame.configure(bg=self.divider_color)
        self.notebox.configure(bg=self.background_color)

        # call functions
        self.save_theme_state()
        self.clear_main()
        self.show_theme_editor()
        self.refresh_file_frame()

    def set_color_from_entry(self, element_name, entry_widget):
        value = entry_widget.get().strip()

        if not value.startswith("#"):
            value = "#" + value

        # basic validation
        if len(value) == 7:
            try:
                self.app.winfo_rgb(value)  # validates color
                self.apply_custom_color(element_name, value)
            except tk.TclError:
                print("Invalid color")

    def pick_color(self, element_name):
        dialog = ColorPicker(self.app, self)
        self.app.wait_window(dialog)

        if dialog.confirmed:   # <-- THIS is the real fix
            self.apply_custom_color(element_name, dialog.color)

    def apply_custom_color(self, element_name, color):
        setattr(self, element_name, color)
        # update UI immediately
        self.change_theme("custom")


# >>>>>>>>>>>>>>>>>>>>>>>>
# UI Helpers
# <<<<<<<<<<<<<<<<<<<<<<<<

    # called alot to clear all widgets in the  main frame
    def clear_main(self):
        try:
            for widget in self.main_frame.winfo_children():
                widget.destroy()
        except Exception as e:
            print(f"\n\nError: clear_main failed to clear main frame.\n{e}\n\n")

    def clear_bottom(self):
        try:
            if hasattr(self, "bottom_window_case") and self.bottom_window_case in self.main_frame.winfo_children():
                self.bottom_window_case.destroy()
            self.bottom_shown = False
            self.fonts_shown = False
        except Exception as e:
            print(f"\n\nError: clear_bottom failed to clear bottom window.\n{e}\n\n")

    # called when saving deleting or loading files or when changing theme
    def refresh_file_frame(self):
        try:
            for widget in self.file_frame.winfo_children():
                widget.destroy()
            files = [f for f in os.listdir(NOTES_DIR)]
            for file in files:
                btn = ctk.CTkButton(
                    self.file_frame,
                    text=os.path.splitext(os.path.basename(file))[0],
                    fg_color=self.background_color,
                    hover_color=self.hover_color,
                    font=(self.app_font_name, 14),
                    text_color=self.text_color,
                    corner_radius=5,
                    command=lambda f=file: self.open_file(os.path.join(NOTES_DIR, f))
                )
                btn.pack(fill="x", pady=2)
        except Exception as e:
            print(f"\n\nError: refresh_file_frame failed to refresh the file list.\n{e}\n\n")


# >>>>>>>>>>>>>>>>>>>>>>>>
# File Logic
# <<<<<<<<<<<<<<<<<<<<<<<<

    # called when user clicks new button
    def new_file(self):
        # clear current file reference, show editor, and empty notebox
        self.current_file = None
        self.clear_main()
        self.show_editor()
        self.notebox.delete("1.0", "end")

    # called when user clicks open button
    def open_file_dialog(self):
        dialog = FileDialog(self.app, self, mode="open", initial_dir=NOTES_DIR)
        self.app.wait_window(dialog)

        if dialog.selected_file:
            self.open_file(dialog.selected_file)

    # called when the user opens a file
    def open_file(self, path):
        try:
            self.current_file = path
            try:
                self.clear_bottom()
            except Exception as e:
                print(f"\n\nError: open_file failed to clear bottom window.\n{e}\n\n")
            self.clear_main()
            self.show_editor()
            self.font_tags.clear()
            self.notebox.configure(font=(self.font_name, self.font_size))
            self._refresh_base_tags()
            if path.endswith(".txt"):
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
                self.notebox.insert("1.0", text)
                return
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.notebox.insert("1.0", data.get("text", ""))
                for tag_info in data.get("tags", []):
                    tag = tag_info["tag"]
                    if tag.startswith("font_"):
                        if tag not in self.notebox.tag_names():
                            spec = tag_info.get("font_spec")
                            if spec:
                                name = spec["font"]
                                size = spec["size"]
                                style = spec["style"]
                                key = f"{name}|{size}|{style}"
                                if style:
                                    self.notebox.tag_config(tag, font=(name, size, style))
                                else:
                                    self.notebox.tag_config(tag, font=(name, size))
                                self.font_tags[key] = tag
                    self.notebox.tag_add(tag, tag_info["start"], tag_info["end"])
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"\n\nError: open_file failed to parse JSON, loading as plain text.\n{e}\n\n")
                with open(path, "r", encoding="utf-8") as f:
                    self.notebox.insert("1.0", f.read())
        except Exception as e:
            print(f"\n\nError: open_file failed to open '{path}'.\n{e}\n\n")

    # called when user saves a file
    def save_file(self):
        try:
            if not self.current_file:
                dialog = FileDialog(self.app, self, mode="save", initial_dir=NOTES_DIR)
                self.app.wait_window(dialog)
                if not dialog.selected_file:
                    return
                self.current_file = dialog.selected_file
            self.save_font_state()
            self.save_theme_state()
            data = {
                "text": self.notebox.get("1.0", "end"),
                "tags": self.get_tag_data()
            }
            with open(self.current_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.refresh_file_frame()
        except Exception as e:
            print(f"\n\nError: save_file failed to save '{self.current_file}'.\n{e}\n\n")


# >>>>>>>>>>>>>>>>>>>>>>>>
# Notebox Logic
# <<<<<<<<<<<<<<<<<<<<<<<<

    # called while typing
    def apply_active_tags(self):
        try:
            index = self.notebox.index("insert-1c")
            bold = self.active_tags["bold"]
            italic = self.active_tags["italic"]
            style = ""
            self.notebox.tag_remove("bold", index, f"{index} +1c")
            self.notebox.tag_remove("italic", index, f"{index} +1c")
            self.notebox.tag_remove("bold_italic", index, f"{index} +1c")
            if bold and italic:
                style = "bold_italic"
                self.notebox.tag_add("bold_italic", index, f"{index} +1c")
            elif bold:
                style = "bold"
                self.notebox.tag_add("bold", index, f"{index} +1c")
            elif italic:
                style = "italic"
                self.notebox.tag_add("italic", index, f"{index} +1c")
            font_tag = self._get_font_tag(self.font_name, self.font_size, style)
            self.notebox.tag_add(font_tag, index, f"{index} +1c")
        except Exception as e:
            print(f"\n\nError: apply_active_tags failed to apply tags while typing.\n{e}\n\n")

    # called when user formats selected text
    def update_tags_on_selection(self):
        try:
            start = self.notebox.index("sel.first")
            end = self.notebox.index("sel.last")
            self._apply_font_to_range(start, end)
        except tk.TclError:
            pass

    def insert_bullet(self):
        try:
            text = self.notebox
            try:
                start = text.index("sel.first linestart")
                end = text.index("sel.last lineend")
            except tk.TclError:
                start = text.index("insert linestart")
                end = text.index("insert lineend")
            line = start
            while True:
                line_end = text.index(f"{line} lineend")
                content = text.get(line, line_end)
                stripped = content.lstrip(" \t")
                indent = content[:len(content) - len(stripped)]
                if stripped.startswith("• "):
                    new = indent + "- " + stripped[2:]
                elif stripped.startswith("- "):
                    new = indent + "* " + stripped[2:]
                elif stripped.startswith("* "):
                    new = indent + stripped[2:]
                else:
                    new = indent + "• " + stripped
                tags_in_line = []
                for tag in ("bold", "italic", "bold_italic"):
                    ranges = text.tag_ranges(tag)
                    for i in range(0, len(ranges), 2):
                        tag_start = ranges[i]
                        tag_end = ranges[i+1]
                        if text.compare(tag_start, "<", line_end) and text.compare(tag_end, ">", line):
                            start_offset = int(text.count(line, tag_start, "chars")[0])
                            end_offset = int(text.count(line, tag_end, "chars")[0])
                            tags_in_line.append((tag, start_offset, end_offset))
                text.delete(line, line_end)
                text.insert(line, new)
                for tag, start_off, end_off in tags_in_line:
                    new_start = f"{line}+{start_off}c"
                    new_end = f"{line}+{end_off}c"
                    text.tag_add(tag, new_start, new_end)
                next_line = text.index(f"{line} +1line")
                if text.compare(next_line, ">", end):
                    break
                line = next_line
        except Exception as e:
            print(f"\n\nError: insert_bullet failed to insert or cycle bullet.\n{e}\n\n")

    def _reapply_font_to_all(self):
        try:
            start = "1.0"
            end = self.notebox.index("end")
            bold_ranges = self._snapshot_tag("bold")
            italic_ranges = self._snapshot_tag("italic")
            bold_italic_ranges = self._snapshot_tag("bold_italic")
            for tag_name in list(self.font_tags.values()):
                self.notebox.tag_remove(tag_name, start, end)
            self.font_tags.clear()
            self._refresh_base_tags()
            plain_tag = self._get_font_tag(self.font_name, self.font_size, "")
            self.notebox.tag_add(plain_tag, start, end)
            bold_tag = self._get_font_tag(self.font_name, self.font_size, "bold")
            for s, e in bold_ranges:
                self.notebox.tag_add("bold", s, e)
                self.notebox.tag_add(bold_tag, s, e)
            italic_tag = self._get_font_tag(self.font_name, self.font_size, "italic")
            for s, e in italic_ranges:
                self.notebox.tag_add("italic", s, e)
                self.notebox.tag_add(italic_tag, s, e)
            bi_tag = self._get_font_tag(self.font_name, self.font_size, "bold_italic")
            for s, e in bold_italic_ranges:
                self.notebox.tag_add("bold_italic", s, e)
                self.notebox.tag_add(bi_tag, s, e)
            for tag in ("bold", "italic", "bold_italic"):
                self.notebox.tag_raise(tag)
        except Exception as e:
            print(f"\n\nError: _reapply_font_to_all failed to reapply fonts.\n{e}\n\n")

    def _snapshot_tag(self, tag):
        try:
            ranges = self.notebox.tag_ranges(tag)
            return [(str(ranges[i]), str(ranges[i+1])) for i in range(0, len(ranges), 2)]
        except Exception as e:
            print(f"\n\nError: _snapshot_tag failed to snapshot tag '{tag}'.\n{e}\n\n")
            return []

    def increase_font_size(self):
        self.change_font_size(self.font_size + 1)

    def decrease_font_size(self):
        if self.font_size > 1:
            self.change_font_size(self.font_size - 1)

    def _get_font_tag(self, font_name, font_size, style=""):
        try:
            key = f"{font_name}|{font_size}|{style}"
            if key not in self.font_tags:
                tag_name = f"font_{len(self.font_tags)}"
                tk_style = style.replace("_", " ")
                if tk_style:
                    self.notebox.tag_config(tag_name, font=(font_name, font_size, tk_style))
                else:
                    self.notebox.tag_config(tag_name, font=(font_name, font_size))
                self.font_tags[key] = tag_name
            return self.font_tags[key]
        except Exception as e:
            print(f"\n\nError: _get_font_tag failed to register font tag.\n{e}\n\n")
            return ""

    def set_font(self, font_name):
        try:
            if self.app_font_customize:
                self.app_font_name = font_name
                self.clear_bottom()
                self.clear_main()
                self.show_welcome()
                self.sidebar_label.configure(font=(self.app_font_name, 16))
                self.refresh_file_frame()
            else:
                self.font_name = font_name
                try:
                    sel_start = self.notebox.index("sel.first")
                    sel_end = self.notebox.index("sel.last")
                    self._apply_font_to_range(sel_start, sel_end)
                except tk.TclError:
                    self._reapply_font_to_all()
        except Exception as e:
            print(f"\n\nError: set_font failed to set font '{font_name}'.\n{e}\n\n")

    def change_font_size(self, size):
        try:
            self.font_size = int(size)
            try:
                sel_start = self.notebox.index("sel.first")
                sel_end = self.notebox.index("sel.last")
                self._apply_font_to_range(sel_start, sel_end)
            except tk.TclError:
                self._reapply_font_to_all()
        except Exception as e:
            print(f"\n\nError: change_font_size failed to change font size to '{size}'.\n{e}\n\n")

    def _apply_font_to_range(self, start, end):
        try:
            print(f"\n--- _apply_font_to_range called ---")
            print(f"Selection: {start} -> {end}")
            all_font_tags = []
            for tag_name in list(self.font_tags.values()):
                ranges = self._snapshot_tag(tag_name)
                if ranges:
                    all_font_tags.append((tag_name, ranges))
            print(f"Font tags and their ranges BEFORE removal: {all_font_tags}")
            bold_ranges = self._clip_ranges(self._snapshot_tag("bold"), start, end)
            italic_ranges = self._clip_ranges(self._snapshot_tag("italic"), start, end)
            bi_ranges = self._clip_ranges(self._snapshot_tag("bold_italic"), start, end)
            bold_outside = self._exclude_ranges(self._snapshot_tag("bold"), start, end)
            italic_outside = self._exclude_ranges(self._snapshot_tag("italic"), start, end)
            bi_outside = self._exclude_ranges(self._snapshot_tag("bold_italic"), start, end)
            for tag_name in list(self.font_tags.values()):
                self.notebox.tag_remove(tag_name, start, end)
            all_font_tags_after = []
            for tag_name in list(self.font_tags.values()):
                ranges = self._snapshot_tag(tag_name)
                if ranges:
                    all_font_tags_after.append((tag_name, ranges))
            print(f"Font tags and their ranges AFTER removal: {all_font_tags_after}")
            for tag in ("bold", "italic", "bold_italic"):
                self.notebox.tag_remove(tag, start, end)
            self._refresh_base_tags()
            plain_tag = self._get_font_tag(self.font_name, self.font_size, "")
            self.notebox.tag_add(plain_tag, start, end)
            bold_tag = self._get_font_tag(self.font_name, self.font_size, "bold")
            for s, e in bold_ranges:
                self.notebox.tag_add("bold", s, e)
                self.notebox.tag_add(bold_tag, s, e)
            italic_tag = self._get_font_tag(self.font_name, self.font_size, "italic")
            for s, e in italic_ranges:
                self.notebox.tag_add("italic", s, e)
                self.notebox.tag_add(italic_tag, s, e)
            bi_tag = self._get_font_tag(self.font_name, self.font_size, "bold_italic")
            for s, e in bi_ranges:
                self.notebox.tag_add("bold_italic", s, e)
                self.notebox.tag_add(bi_tag, s, e)
            for s, e in bold_outside:
                self.notebox.tag_add("bold", s, e)
            for s, e in italic_outside:
                self.notebox.tag_add("italic", s, e)
            for s, e in bi_outside:
                self.notebox.tag_add("bold_italic", s, e)
            for tag in ("bold", "italic", "bold_italic"):
                self.notebox.tag_raise(tag)
        except Exception as e:
            print(f"\n\nError: _apply_font_to_range failed to apply font to range {start}->{end}.\n{e}\n\n")

    def _clip_ranges(self, ranges, start, end):
        try:
            result = []
            for s, e in ranges:
                if self.notebox.compare(e, "<=", start) or self.notebox.compare(s, ">=", end):
                    continue
                cs = s if self.notebox.compare(s, ">", start) else start
                ce = e if self.notebox.compare(e, "<", end) else end
                if self.notebox.compare(cs, "<", ce):
                    result.append((cs, ce))
            return result
        except Exception as e:
            print(f"\n\nError: _clip_ranges failed to clip ranges.\n{e}\n\n")
            return []

    def _exclude_ranges(self, ranges, start, end):
        try:
            result = []
            for s, e in ranges:
                if self.notebox.compare(s, "<", start):
                    ce = e if self.notebox.compare(e, "<", start) else start
                    if self.notebox.compare(s, "<", ce):
                        result.append((s, ce))
                if self.notebox.compare(e, ">", end):
                    cs = s if self.notebox.compare(s, ">", end) else end
                    if self.notebox.compare(cs, "<", e):
                        result.append((cs, e))
            return result
        except Exception as e:
            print(f"\n\nError: _exclude_ranges failed to exclude ranges.\n{e}\n\n")
            return []

    def _refresh_base_tags(self):
        try:
            self.notebox.tag_config("bold", font="")
            self.notebox.tag_config("italic", font="")
            self.notebox.tag_config("bold_italic", font="")
        except Exception as e:
            print(f"\n\nError: _refresh_base_tags failed to refresh base tags.\n{e}\n\n")

    # called when user clicks bold button
    def toggle_bold(self):
        try:
            self.active_tags["bold"] = not self.active_tags["bold"]
            self.update_tags_on_selection()
            self.bold_button.configure(
                fg_color=self.hover_color if self.active_tags["bold"] else self.background_color
            )
        except Exception as e:
            print(f"\n\nError: toggle_bold failed to toggle bold.\n{e}\n\n")

    # called when user clicks italic button
    def toggle_italic(self):
        try:
            self.active_tags["italic"] = not self.active_tags["italic"]
            self.update_tags_on_selection()
            self.italic_button.configure(
                fg_color=self.hover_color if self.active_tags["italic"] else self.background_color
            )
        except Exception as e:
            print(f"\n\nError: toggle_italic failed to toggle italic.\n{e}\n\n")

    def handle_enter(self, event):
        text = self.notebox

        line_start = text.index("insert linestart")
        line_end = text.index("insert lineend")
        line_text = text.get(line_start, line_end)

        # Extract indentation
        indent = ""
        i = 0
        while i < len(line_text) and line_text[i] in (" ", "\t"):
            indent += line_text[i]
            i += 1

        stripped = line_text[len(indent):]

        for bullet in BULLETS:
            if stripped.startswith(bullet):
                content = stripped[len(bullet):]

                # EXIT LIST
                if content.strip() == "":
                    text.delete(line_start, line_end)
                    text.insert(line_start, indent)
                    text.mark_set("insert", line_start + f"+{len(indent)}c")
                    return "break"

                # CONTINUE LIST
                text.insert("insert", f"\n{indent}{bullet}")
                return "break"

        return None

    def handle_tab(self, event):
        text = self.notebox

        try:
            start = text.index("sel.first linestart")
            end = text.index("sel.last lineend")
        except tk.TclError:
            start = text.index("insert linestart")
            end = text.index("insert lineend")

        line = start

        while True:
            text.insert(line, "    ")

            if text.compare(line, ">", end):
                break

            line = text.index(f"{line} +1line")

        return "break"


    def handle_shift_tab(self, event):
        text = self.notebox

        try:
            start = text.index("sel.first linestart")
            end = text.index("sel.last lineend")
        except tk.TclError:
            start = text.index("insert linestart")
            end = text.index("insert lineend")

        line = start

        while True:
            line_end = text.index(f"{line} lineend")
            content = text.get(line, line_end)

            if content.startswith("    "):
                text.delete(line, f"{line}+4c")

            if text.compare(line, ">=", end):
                break

            line = text.index(f"{line} +1line")

        return "break"

    def on_key_press(self, event):
        # Don't apply tags for control/navigation/deletion keys
        skip = {"BackSpace", "Delete", "Left", "Right", "Up", "Down",
                "Home", "End", "Prior", "Next", "Shift_L", "Shift_R",
                "Control_L", "Control_R", "Alt_L", "Alt_R", "Escape",
                "Tab", "Return", "Caps_Lock"}
        if event.keysym in skip:
            return
        self.notebox.after_idle(self.apply_active_tags)


# >>>>>>>>>>>>>>>>>>>>>>>>
# Save State Logic
# <<<<<<<<<<<<<<<<<<<<<<<<

    def back_pressed(self):
        self.save_file()
        self.show_welcome()

    # get all formatting from notebox
    def get_tag_data(self):
        try:
            tag_data = []
            tag_to_spec = {}
            for key, tag_name in self.font_tags.items():
                parts = key.split("|")
                if len(parts) == 3:
                    tag_to_spec[tag_name] = {"font": parts[0], "size": int(parts[1]), "style": parts[2]}
            all_tags = ["bold", "italic", "bold_italic"] + list(self.font_tags.values())
            for tag in all_tags:
                ranges = self.notebox.tag_ranges(tag)
                for i in range(0, len(ranges), 2):
                    entry = {
                        "tag": tag,
                        "start": str(ranges[i]),
                        "end": str(ranges[i+1])
                    }
                    if tag in tag_to_spec:
                        entry["font_spec"] = tag_to_spec[tag]
                    tag_data.append(entry)
            return tag_data
        except Exception as e:
            print(f"\n\nError: get_tag_data failed to collect tag data.\n{e}\n\n")
            return []

    # save toolbar state for button consistency
    def save_font_state(self):
        try:
            font_state = {
                "bold": self.active_tags["bold"],
                "italic": self.active_tags["italic"],
                "bold_italic": self.active_tags["bold_italic"],
                "font_name": self.font_name,
                "font_size": self.font_size,
                "app_font_name": self.app_font_name,
            }
            with open(FONT_FILE, 'w') as f:
                json.dump(font_state, f)
        except Exception as e:
            print(f"\n\nError: save_font_state failed to save font state.\n{e}\n\n")

    # restores toolbar state on app open
    def load_font_state(self):
        try:
            with open(FONT_FILE, 'r') as f:
                font_state = json.load(f)
            self.active_tags["bold"] = False
            self.active_tags["italic"] = False
            self.active_tags["bold_italic"] = False
            self.app_font_name = font_state.get("app_font_name") or "Arial"
            self.font_size = font_state.get("font_size") or 12
            self.font_name = font_state.get("font_name") or "Arial"
        except (FileNotFoundError, json.JSONDecodeError):
            self.active_tags["bold"] = False
            self.active_tags["italic"] = False
            self.active_tags["bold_italic"] = False
            self.app_font_name = "Arial"
            self.font_name = "Arial"
            self.font_size = 12

    # do i really need to comment here?
    def save_theme_state(self):
        try:
            theme_data = {
                "background_color": self.background_color,
                "hover_color": self.hover_color,
                "button_color": self.button_color,
                "frame_color": self.frame_color,
                "divider_color": self.divider_color,
                "highlight_color": self.highlight_color,
                "text_color": self.text_color,
                "highlighted_text_color": self.highlighted_text_color
            }
            with open(THEME_FILE, 'w') as f:
                json.dump(theme_data, f)
        except Exception as e:
            print(f"\n\nError: save_theme_state failed to save theme state.\n{e}\n\n")

    # apply theme state on app open, if error, theme == purple
    def load_theme_state(self):
        try:
            with open(THEME_FILE, 'r') as f:
                theme_data = json.load(f)

            self.background_color = theme_data.get("background_color", self.default[0])
            self.hover_color = theme_data.get("hover_color", self.default[1])
            self.button_color = theme_data.get("button_color", self.default[2])
            self.frame_color = theme_data.get("frame_color", self.default[3])
            self.divider_color = theme_data.get("divider_color", self.default[4])
            self.highlight_color = theme_data.get("highlight_color", self.default[5])
            self.text_color = theme_data.get("text_color", self.default[6])
            self.highlighted_text_color = theme_data.get("highlighted_text_color", self.default[7])

        except (FileNotFoundError, json.JSONDecodeError):
            # If no theme file exists or it's invalid, fall back to default (purple)
            self.background_color = self.default[0]
            self.hover_color = self.default[1]
            self.button_color = self.default[2]
            self.frame_color = self.default[3]
            self.divider_color = self.default[4]
            self.highlight_color = self.default[5]
            self.text_color = self.default[6]
            self.highlighted_text_color = self.default[7]


# >>>>>>>>>>>>>>>>>>>>>>>>
# App Run
# <<<<<<<<<<<<<<<<<<<<<<<<
    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS  # PyInstaller temp folder
        except AttributeError:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def close_app(self):
        try:
            self.save_font_state()
            self.save_theme_state()
            self.app.destroy()
        except Exception as e:
            print(f"\n\nError: close_app failed to close cleanly.\n{e}\n\n")
            self.app.destroy()

    def run(self):
        # Validate font_name now that Tk is running and tkfont.families() works
        available = tkfont.families()
        if self.font_name not in available:
            self.font_name = "Arial"
        if self.app_font_name not in available:
            self.app_font_name = "Arial"

        self.show_welcome()
        self.app.mainloop()


if __name__ == "__main__":
    app = Notes()
    app.run()

