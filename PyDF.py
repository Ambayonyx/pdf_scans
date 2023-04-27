import tkinter as tk
import tkinter.filedialog
from dataclasses import dataclass
from tkinter import RIGHT, LEFT, X

from PIL import ImageTk

from merge_single_sidescanned_files import merge_single_sides_canned_files

background_color = "#3d6466"
foreground_color = "white"
foreground_color_active = "black"
background_color_button_inactive = "#28393a"
background_color_button_active = "#badee2"
dialog_width = 600
dialog_height = 400


@dataclass
class App:
    front_path: tk.StringVar
    back_path: tk.StringVar
    output_path: tk.StringVar
    reversed: tk.BooleanVar


def create_file_browse_widget(parent: tk.Frame, title: str, value_var) -> tk.Frame:
    def browse_file(_title: str, _value_var):
        filename = tkinter.filedialog.askopenfilename(filetypes=(
            ("PDF files", "*.pdf"),
            ("All files", "*.*")
        ), title=_title)
        if filename:
            _value_var.set(filename)

    browse_frame = tk.Frame(parent, bg=background_color)

    label = tk.Label(browse_frame,
                     text=title,
                     bg=background_color,
                     fg=foreground_color,
                     font=("TkMenuFont", 10)
                     )
    label.pack(side=LEFT, padx=5)

    btn = tk.Button(
        browse_frame,
        text="...",
        font=("TkMenuFont", 10),
        bg=background_color_button_inactive,
        fg=foreground_color,
        cursor="hand2",
        activebackground=background_color_button_active,
        activeforeground=foreground_color_active,
        command=lambda: browse_file(title, value_var)
    )

    btn.pack(pady=5, side=RIGHT, padx=5)

    text = tk.Entry(browse_frame,
                    textvariable=value_var,
                    bg=background_color,
                    fg=foreground_color,
                    font=("TkMenuFont", 10)
                    )

    text.pack(fill=X, expand=True, padx=5)

    return browse_frame


def create_checkbox_widget(parent: tk.Frame, title: str, value_var) -> tk.Frame:
    checkbox_frame = tk.Frame(parent, bg=background_color)
    checkbox_frame.pack(padx=5)

    btn = tk.Checkbutton(
        checkbox_frame,
        text=title,
        variable=value_var,
        bg=background_color,
        fg=foreground_color,
        activebackground=background_color,
        activeforeground=foreground_color,
        selectcolor=background_color
    )

    btn.pack(pady=5, side=RIGHT, padx=5)
    return checkbox_frame


def merge(app: App):
    try:
        merge_single_sides_canned_files(front_pdf=app.front_path.get(),
                                        back_pdf=app.back_path.get(),
                                        merged_pdf=app.output_path.get(),
                                        back_scanned_reverse=app.reversed.get())
        tk.messagebox.showinfo(title="Run result", message="Done")
    except (FileNotFoundError, PermissionError) as e:
        tk.messagebox.showerror(title="Run result",
                                message=f'Required file does not exist or is not readable: {e.filename}')


def load_frame(frame: tk.Frame, app: App):
    frame.pack_propagate(False)

    logo_img = ImageTk.PhotoImage(file="assets/pdf_logo.png")
    logo_widget = tk.Label(frame, image=logo_img, bg=background_color)
    logo_widget.image = logo_img
    logo_widget.pack(padx=5, pady=5)
    selection_frame = tk.Frame(frame, bg=background_color)
    selection_frame.pack_propagate(True)

    front_frame = create_file_browse_widget(selection_frame, title="Front", value_var=app.front_path)
    front_frame.pack(fill=X, padx=5)

    back_frame = create_file_browse_widget(selection_frame, title="Back", value_var=app.back_path)
    back_frame.pack(fill=X, padx=5)

    output_frame = create_file_browse_widget(selection_frame, title="Output", value_var=app.output_path)
    output_frame.pack(fill=X, padx=5)

    checkbox = create_checkbox_widget(selection_frame, title="Reversed back", value_var=app.reversed)
    checkbox.pack(pady=5, padx=5)
    selection_frame.pack(fill=X)

    btn = tk.Button(
        frame,
        text="Run",
        font=("TkMenuFont", 10),
        bg=background_color_button_inactive,
        fg=foreground_color,
        cursor="hand2",
        activebackground=background_color_button_active,
        activeforeground=foreground_color_active,
        command=lambda: merge(app)
    )
    btn.pack(pady=5, padx=5)


def main():
    root = tk.Tk()
    root.title("PyPDF")
    app = App(front_path=tk.StringVar(),
              back_path=tk.StringVar(),
              output_path=tk.StringVar(),
              reversed=tk.BooleanVar())
    app.front_path.set(".")
    app.back_path.set(".")
    app.output_path.set(".")
    app.reversed.set(False)

    # root.eval("tk::PlaceWindow . center")
    x = (root.winfo_screenwidth() - dialog_width) // 2
    y = (root.winfo_screenheight() - dialog_height) // 2
    root.geometry(f'{dialog_width}x{dialog_height}+{x}+{y}')

    frame1 = tk.Frame(root, width=dialog_width, height=dialog_height, bg=background_color)
    frame1.grid(row=0, column=0)
    load_frame(frame1, app)

    # run app
    root.mainloop()


if __name__ == "__main__":
    main()
