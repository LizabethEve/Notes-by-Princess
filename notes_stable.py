import os
import json
import sys
import customtkinter as ctk
import tkinter as tk
from PIL import Image
from tkinter import filedialog
from Images.recolor import batch_recolor_fast

# constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NOTES_DIR = os.path.join(BASE_DIR, "notes")
THEME_FILE = os.path.join(BASE_DIR, "theme_state.json")
FONT_FILE = os.path.join(BASE_DIR, "font_state.json")
IMAGES = os.path.join(BASE_DIR, "Images")
APP_IMAGE = None
os.makedirs(NOTES_DIR, exist_ok=True)

BULLETS = ("• ", "- ", "* ")



# >>>>>>>>>>>>>>>>>>>>>>>>
# Initialization
# <<<<<<<<<<<<<<<<<<<<<<<<

class Notes():
    def __init__(self):
        # define ctk
        self.app = ctk.CTk()
        self.app.title("Notes")
        self.app.geometry("1920x1080")
        if sys.platform == "win32":
            APP_IMAGE = app.iconbitmap("App.ico")
        elif sys.platform == "darwin":
            #APP_TO_RUN = "notes.app/Contents/MacOS/notes"
            pass
        else:
            APP_IMAGE = os.path.join(BASE_DIR, "App.png")
            self.app_image = tk.PhotoImage(file=APP_IMAGE)
            self.app.iconphoto(True, self.app_image)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # define variables and all that other good stuff
        self.current_file = None
        self.active_tags = {"bold": False, "italic": False}
        self.themes = {
            "purple": ["#38323b", "#9a6bd6", "#38323b", "#efdefa", "#9a6bd6", "#cab0db", "#efdefa", "#38323b"],
            "yellow": ["#3b3b32", "#d6d56b", "#3b3b32", "#faf9de", "#d6d56b", "#dbd9b0", "#faf9de", "#3b3b32"],
            "red": ["#3b3232", "#d66b6b", "#3b3232", "#fadede", "#d66b6b", "#dbb0b0", "#fadede", "#3b3232"],
            "green": ["#343b32", "#70d66b", "#343b32", "#dffade", "#70d66b", "#b2dbb0", "#dffade", "#343b32"],
            "blue": ["#32323b", "#6b7cd7", "#32323b", "#dedffa", "#6b7cd7", "#b0b2db", "#dedffa", "#32323b"],
            "custom": ["#", "#", "#", "#", "#", "#", "#", "#"],
            }
        self.default = self.themes["purple"]
        self.background_color = self.default[0]
        self.hover_color = self.default[1]
        self.button_color = self.default[2]
        self.frame_color = self.default[3]
        self.divider_color = self.default[4]
        self.highlight_color = self.default[5]
        self.text_color = self.default[6]
        self.highlighted_text_color = self.default[7]


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
                                        font=("Arial", 16),
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

        # create the main frame inside paned and refresh file window
        self.main_frame = ctk.CTkFrame(self.paned, fg_color=self.background_color, corner_radius=5)
        self.paned.add(self.main_frame, minsize=300)
        self.refresh_file_frame()


# >>>>>>>>>>>>>>>>>>>>>>>>
# UI
# <<<<<<<<<<<<<<<<<<<<<<<<

    # function called on app open or on main screen
    def show_welcome(self):
        # clear all widgets attatched to the main frame
        self.clear_main()

        # welcome screen widgets
        self.title = ctk.CTkLabel(self.main_frame,
                             text="Notes by Princess",
                             font=("Arial", 28),
                             text_color=self.text_color,
                             )
        self.title.place(relx=0.5, rely=0.2, anchor="center")

        self.new_button = ctk.CTkButton(self.main_frame,
                                   text="New File",
                                   fg_color=self.background_color,
                                   hover_color=self.hover_color,
                                   border_width=0,
                                   width=100,
                                   height=20,
                                   corner_radius=5,
                                   text_color=self.text_color,
                                   command=self.new_file,
                                   )
        self.new_button.place(relx=0.4, rely=0.5, anchor="center")

        self.open_button = ctk.CTkButton(self.main_frame,
                                    text="Open File",
                                    fg_color=self.background_color,
                                    hover_color=self.hover_color,
                                    border_width=0,
                                    width=100,
                                    height=20,
                                    corner_radius=5,
                                    text_color=self.text_color,
                                    command=self.open_file_dialog)
        self.open_button.place(relx=0.6, rely=0.5, anchor="center")

        self.theme_button = ctk.CTkButton(self.main_frame,
                                          text="Theme",
                                          fg_color=self.background_color,
                                          hover_color=self.hover_color,
                                          border_width=0,
                                          width=50,
                                          height=20,
                                          corner_radius=5,
                                          text_color=self.text_color,
                                          command=self.show_theme_editor)
        self.theme_button.place(relx=0.01, rely=0.99, anchor="sw")

    # function called when user clicks a file or theme editor
    def show_editor(self):
        # clear widgets and create toolbar
        self.show_toolbar()

        # editor widgets
        self.note_title_case = ctk.CTkFrame(self.main_frame,
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
                                       font=("Arial", 30),
                                       text_color=self.text_color,
                                       bg_color=self.background_color)
        self.note_title.place(relx=0.5, rely=0.5, anchor="center")

        self.editor_container = ctk.CTkFrame(self.main_frame, fg_color=self.background_color)
        self.editor_container.pack(fill="both", expand=True)

        self.text_bg = ctk.CTkFrame(self.editor_container, corner_radius=5, fg_color=self.background_color)
        self.text_bg.pack(side="top", fill="both", expand=True, padx=5, pady=(5, 0))

        self.notebox = tk.Text(self.text_bg,
                       bg=self.background_color,
                       fg=self.text_color,
                       insertbackground=self.text_color,
                       font=("Arial", 12),
                       bd=0,
                       wrap="word",
                       yscrollcommand=True,
                       selectbackground=self.highlight_color,
                       selectforeground=self.highlighted_text_color,
                       highlightthickness=0,
                       relief="flat")
        self.notebox.pack(fill="both", expand=True, padx=25, pady=25)

        # configure text tags
        self.notebox.tag_config("bold", font=("Arial", 12, "bold"))
        self.notebox.tag_config("italic", font=("Arial", 12, "italic"))
        self.notebox.tag_config("bold_italic", font=("Arial", 12, "bold italic"))

        self.notebox.bind("<Return>", self.handle_enter)

        # binds user key release to apply text tags, so the effect takes place the second the character is released while typing, still having issues with not recording one character while another is pressed down (only one at once)
        self.notebox.bind("<KeyPress>", lambda e: self.notebox.after_idle(self.apply_active_tags))

    # function called by show_editor, creates toolbar
    def show_toolbar(self):
        # toolbar frame
        self.toolbar_case = ctk.CTkFrame(self.main_frame,
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
        self.toolbar.place(relx=0.5, rely=0.0, anchor="n")

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
                                    fg_color=self.background_color,
                                    hover_color=self.hover_color,
                                    border_width=1,
                                    border_color=self.frame_color,
                                    width=30,
                                    corner_radius=5,
                                    text_color=self.text_color,
                                    command=self.show_welcome
                                    )
        self.back_button.pack(pady=1)

        self.save_button = ctk.CTkButton(self.toolbar,
                                    text="",
                                    image=self.save_image,
                                    fg_color=self.background_color,
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
                                    fg_color=self.background_color,
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
                                      fg_color=self.background_color,
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
                                      fg_color=self.background_color,
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
                                      fg_color=self.background_color,
                                      hover_color=self.hover_color,
                                      border_width=1,
                                      border_color=self.frame_color,
                                      width=30,
                                      corner_radius=5,
                                      text_color=self.text_color,
                                      command=self.insert_bullet
                                      )
        self.bullet_button.pack(pady=1)

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
        # bottome window widgets
        self.bottom_window_case = ctk.CTkFrame(self.editor_container,
                                                 corner_radius=5,
                                                 fg_color=self.background_color,
                                                 )
        self.bottom_window_case.pack(side="bottom", fill="x", pady=5)
        self.bottom_window_case.configure(height=200)

        self.bottom_window_line = ctk.CTkFrame(self.bottom_window_case,
                                       corner_radius=5,
                                       border_width=1,
                                       border_color=self.frame_color,
                                       fg_color=self.background_color,
                                       height=2,
                                       )
        self.bottom_window_line.pack(side="top", fill="x", pady=1)

        self.bottom_scroll = ctk.CTkScrollableFrame(self.bottom_window_case,
                                                 corner_radius=5,
                                                 border_width=0,
                                                 fg_color=self.background_color,
                                                 scrollbar_fg_color=self.background_color,
                                                 scrollbar_button_color=self.frame_color,
                                                 scrollbar_button_hover_color=self.hover_color,
                                                 )
        self.bottom_scroll.pack(fill="both", expand=True, padx=2, pady=2)

    # function called by show_theme_editor when user clicks theme button
    def show_theme_widgets(self):
        # disable toolbar buttons for the theme editor
        self.font_button.configure(command=None)
        self.bold_button.configure(command=None)
        self.italic_button.configure(command=None)
        self.save_button.configure(command=None)
        self.bullet_button.configure(command=None)

        # widgets attatched to the bottom scroll window
        self.pre_button_frame = ctk.CTkFrame(self.bottom_scroll,
                                         corner_radius=5,
                                         border_width=0,
                                         height=200,
                                         fg_color=self.background_color
                                         )
        self.pre_button_frame.pack(side="top", fill="x")

        self.custom_button_frame = ctk.CTkFrame(self.bottom_scroll,
                                                 corner_radius=5,
                                                 border_width=0,
                                                 fg_color=self.background_color,
                                                 )
        self.custom_button_frame.pack(side="bottom", fill="both", expand=True)

        self.yellow_button = ctk.CTkButton(self.pre_button_frame,
                                      text="Yellow",
                                      fg_color=self.background_color,
                                      hover_color=self.hover_color,
                                      border_width=0,
                                      corner_radius=5,
                                      width=100,
                                      text_color=self.text_color,
                                      command=lambda: self.change_theme("yellow")
                                      )
        self.yellow_button.place(relx=0.2, rely=0.5, anchor="center")

        self.purple_button = ctk.CTkButton(self.pre_button_frame,
                                      text="Purple",
                                      fg_color=self.background_color,
                                      hover_color=self.hover_color,
                                      border_width=0,
                                      corner_radius=5,
                                      width=100,
                                      text_color=self.text_color,
                                      command=lambda: self.change_theme("purple")
                                      )
        self.purple_button.place(relx=0.35, rely=0.5, anchor="center")

        self.red_button = ctk.CTkButton(self.pre_button_frame,
                                      text="Red",
                                      fg_color=self.background_color,
                                      hover_color=self.hover_color,
                                      border_width=0,
                                      corner_radius=5,
                                      width=100,
                                      text_color=self.text_color,
                                      command=lambda: self.change_theme("red")
                                      )
        self.red_button.place(relx=0.5, rely=0.5, anchor="center")

        self.green_button = ctk.CTkButton(self.pre_button_frame,
                                      text="Green",
                                      fg_color=self.background_color,
                                      hover_color=self.hover_color,
                                      border_width=0,
                                      corner_radius=5,
                                      width=100,
                                      text_color=self.text_color,
                                      command=lambda: self.change_theme("green")
                                      )
        self.green_button.place(relx=0.65, rely=0.5, anchor="center")

        self.blue_button = ctk.CTkButton(self.pre_button_frame,
                                      text="Blue",
                                      fg_color=self.background_color,
                                      hover_color=self.hover_color,
                                      border_width=0,
                                      corner_radius=5,
                                      width=100,
                                      text_color=self.text_color,
                                      command=lambda: self.change_theme("blue")
                                      )
        self.blue_button.place(relx=0.8, rely=0.5, anchor="center")

        self.customize_seperator = ctk.CTkLabel(self.custom_button_frame,
                                                text="--- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---",
                                                width=500,
                                                text_color=self.frame_color,
                                                )
        self.customize_seperator.pack(side="top", pady=5)

        self.customize_label = ctk.CTkLabel(self.custom_button_frame,
                                            text="Customize:",
                                            fg_color=self.background_color,
                                            font=("Arial", 25),
                                            height=100,
                                            text_color=self.text_color,
                                            )
        self.customize_label.pack(side="top", pady=5)

        self.background_color_button = ctk.CTkButton(self.custom_button_frame,
                                                     text="",
                                                     fg_color=self.background_color,
                                                     border_width=3,
                                                     border_color=self.frame_color,
                                                     width=50,
                                                     height=25,
                                                     hover_color=self.hover_color,
                                                     )
        self.background_color_button.pack(side="right", padx=350, pady=0)

        self.background_enter_bar = ctk.CTkEntry(self.custom_button_frame,
                                                 placeholder_text=self.background_color,
                                                 fg_color=self.background_color,
                                                 state="normal",
                                                 border_color=self.frame_color,
                                                 placeholder_text_color=self.text_color,
                                                 )
        self.background_enter_bar.pack(side="right", padx=0)

        self.background_color_label = ctk.CTkLabel(self.custom_button_frame,
                                                    text=f"Background Color: ",
                                                    font=("Arial", 18),
                                                    text_color=self.text_color,
                                                    )
        self.background_color_label.pack(side="right",  padx=0, pady=0)

    # function called when user clicks font button
    def show_fonts(self):
        self.clear_main()
        self.open_file(self.current_file)
        self.show_bottom_window()

    # function called when user changes themes.
    def change_theme(self, theme_name):
        # define the color picked by user to be passed through function
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
        #self.app.configure(bg=self.background_color)
        self.sidebar_label.configure(fg_color=self.background_color, text_color=self.text_color)
        self.sidebar.configure(fg_color=self.background_color)
        self.file_frame.configure(scrollbar_fg_color=self.background_color, scrollbar_button_color=self.frame_color, scrollbar_button_hover_color=self.hover_color, fg_color=self.background_color)
        self.main_frame.configure(fg_color=self.background_color)
        #self.file_frame.configure(fg_color=self.background_color)
        self.notebox.configure(bg=self.background_color)

        # call functions
        self.save_theme_state()
        self.clear_main()
        self.show_theme_editor()
        self.refresh_file_frame()


# >>>>>>>>>>>>>>>>>>>>>>>>
# UI Helpers
# <<<<<<<<<<<<<<<<<<<<<<<<

    # called alot to clear all widgets in the  main frame
    def clear_main(self):
        # get all children of main_frame
        for widget in self.main_frame.winfo_children():
            # destroy children >:(
            widget.destroy()

    # called when saving deleting or loading files or when changing theme
    def refresh_file_frame(self):
        # get all children of file_frame
        for widget in self.file_frame.winfo_children():
            # destroy children >:(
            widget.destroy()

        # get all files in notes directory
        files = [f for f in os.listdir(NOTES_DIR) if f.endswith(".json")]

        # for every file, create a buton in file_frame
        for file in files:
            btn = ctk.CTkButton(
                self.file_frame,
                text=os.path.splitext(os.path.basename(file))[0],
                fg_color=self.background_color,
                hover_color=self.hover_color,
                text_color=self.text_color,
                corner_radius=5,
                command=lambda f=file: self.open_file(os.path.join(NOTES_DIR, f))
            )
            btn.pack(fill="x", pady=2)


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
        # filter files in directory to only show json
        filepath = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        # pass selected file to open_file
        if filepath:
            self.open_file(filepath)

    # called when the user opens a file
    def open_file(self, path):
        # store filepath and show editor
        self.current_file = path
        self.clear_main()
        self.show_editor()

        # check if is text file
        if path.endswith(".txt"):
            # open it
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            self.notebox.insert("1.0", text)
            return

        try:
            # open and read json data
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # add json data to notebox
            self.notebox.insert("1.0", data.get("text", ""))

            # check for and apply tags
            for tag_info in data.get("tags", []):
                self.notebox.tag_add(tag_info["tag"], tag_info["start"], tag_info["end"])

        # file corrupt or does not exist
        except (json.JSONDecodeError, FileNotFoundError):
            with open(path, "r", encoding="utf-8") as f:
                self.notebox.insert("1.0", f.read())

    # called when user saves a file
    def save_file(self):
        # is file's first save?
        if not self.current_file:
            # open save dialogue
            filepath = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON Files", "*.json")],
                initialdir=NOTES_DIR
            )
            # save to current file if preexisting
            if not filepath:
                return
            self.current_file = filepath

        # define save data
        data = {
            "text": self.notebox.get("1.0", "end"),
            "tags": self.get_tag_data()
        }

        # save data to json file
        with open(self.current_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        self.refresh_file_frame()


# >>>>>>>>>>>>>>>>>>>>>>>>
# Notebox Logic
# <<<<<<<<<<<<<<<<<<<<<<<<

    # called while typing
    def apply_active_tags(self):
        # position cursor after last character
        index = self.notebox.index("insert-1c")

        # define tags
        bold = self.active_tags["bold"]
        italic = self.active_tags["italic"]

        # remove any tags to add new ones
        self.notebox.tag_remove("bold", index, f"{index} +1c")
        self.notebox.tag_remove("italic", index, f"{index} +1c")
        self.notebox.tag_remove("bold_italic", index, f"{index} +1c")

        # add new correct tags
        if bold and italic:
            self.notebox.tag_add("bold_italic", index, f"{index} +1c")
        elif bold:
            self.notebox.tag_add("bold", index, f"{index} +1c")
        elif italic:
            self.notebox.tag_add("italic", index, f"{index} +1c")

    # called when user formats selected text
    def update_tags_on_selection(self):
        try:
            # define users selection (begginging to end)
            start = self.notebox.index("sel.first")
            end = self.notebox.index("sel.last")

            # remove old tags to add new ones
            self.notebox.tag_remove("bold", start, end)
            self.notebox.tag_remove("italic", start, end)
            self.notebox.tag_remove("bold_italic", start, end)

            # define tags
            bold = self.active_tags["bold"]
            italic = self.active_tags["italic"]

            # add new correct tags
            if bold and italic:
                self.notebox.tag_add("bold_italic", start, end)
            elif bold:
                self.notebox.tag_add("bold", start, end)
            elif italic:
                self.notebox.tag_add("italic", start, end)

        # error handeling in case this somehow fails
        except tk.TclError:
            pass

    def insert_bullet(self):
        try:
            # If text is selected → apply bullets to all selected lines
            start = self.notebox.index("sel.first linestart")
            end = self.notebox.index("sel.last lineend")

            line = start
            while self.notebox.compare(line, "<=", end):
                line_end = self.notebox.index(f"{line} lineend")
                text = self.notebox.get(line, line_end)

                if text.startswith("• "):
                    # Remove bullet
                    self.notebox.delete(line, f"{line} +2c")
                    self.notebox.insert(line, "- ")
                elif text.startswith(BULLETS[1]):
                    self.notebox.delete(line, f"{line} +2c")
                    self.notebox.insert(line, "* ")
                elif text.startswith(BULLETS[2]):
                    self.notebox.delete(line, f"{line} +2c")
                else:
                    self.notebox.insert(line, "• ")

                line = self.notebox.index(f"{line} +1line")

        except tk.TclError:
            # No selection → toggle bullet on current line
            line = self.notebox.index("insert linestart")
            line_end = self.notebox.index(f"{line} lineend")
            text = self.notebox.get(line, line_end)

            if text.startswith("• "):
                # Remove bullet
                self.notebox.delete(line, f"{line} +2c")
                self.notebox.insert("insert", "- ")
            elif text.startswith(BULLETS[1]):
                self.notebox.delete(line, f"{line} +2c")
                self.notebox.insert("insert", "* ")
            elif text.startswith(BULLETS[2]):
                self.notebox.delete(line, f"{line} +2c")
            else:
                self.notebox.insert("insert", "• ")

    # called when user clicks bold button
    def toggle_bold(self):
        #toggle bold True/False
        self.active_tags["bold"] = not self.active_tags["bold"]
        self.update_tags_on_selection()

        # update bold button
        self.bold_button.configure(
            fg_color=self.hover_color if self.active_tags["bold"] else self.background_color
        )

    # called when user clicks italic button
    def toggle_italic(self):
        # toggle italic True/False
        self.active_tags["italic"] = not self.active_tags["italic"]
        self.update_tags_on_selection()

        # update italic button
        self.italic_button.configure(
            fg_color=self.hover_color if self.active_tags["italic"] else self.background_color
        )

    def handle_enter(self, event):
        current_line = self.notebox.get("insert linestart", "insert lineend")

        if current_line.strip().startswith(BULLETS):
            if current_line.strip().startswith("- "):
                self.notebox.insert("insert", "\n- ")
            elif current_line.strip().startswith("* "):
                self.notebox.insert("insert", "\n* ")
            elif current_line.strip().startswith("• "):
                self.notebox.insert("insert", "\n• ")
            return "break"  # prevent default newline


# >>>>>>>>>>>>>>>>>>>>>>>>
# Save State Logic
# <<<<<<<<<<<<<<<<<<<<<<<<

    # get all formatting from notebox
    def get_tag_data(self):
        # empty list
        tag_data = []
        # store format data
        for tag in ["bold", "italic", "bold_italic"]:
            ranges = self.notebox.tag_ranges(tag)
            for i in range(0, len(ranges), 2):
                tag_data.append({
                    "tag": tag,
                    "start": str(ranges[i]),
                    "end": str(ranges[i+1])
                    })
        return tag_data

    # save toolbar state for button consistency
    def save_font_state(self):
        font_state = {
            "bold": self.active_tags["bold"],
            "italic": self.active_tags["italic"]
            }
        with open(FONT_FILE, 'w') as f:
            json.dump(font_state, f)

    # restores toolbar state on app open
    def load_font_state(self):
        try:
            with open(FONT_FILE, 'r') as f:
                font_state = json.load(f)
            self.active_tags["bold"] = font_state.get("bold", False)
            self.active_tags["italic"] = font_state.get("italic", False)
        except (FileNotFoundError, json.JSONDecodeError):
            # If the file is not found or corrupted, reset the font states to default (False)
            self.active_tags["bold"] = False
            self.active_tags["italic"] = False

    # do i really need to comment here?
    def save_theme_state(self):
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
        # save theme_data
        with open(THEME_FILE, 'w') as f:
            json.dump(theme_data, f)

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
    def resource_path(relative_path):
        try:
            base_path = sys._MEIPASS  # PyInstaller temp folder
        except AttributeError:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def close_app(self):
        self.save_font_state()
        self.save_theme_state()
        self.app.destroy()

    def run(self):
        self.show_welcome()
        self.app.mainloop()


if __name__ == "__main__":
    app = Notes()
    app.run()

