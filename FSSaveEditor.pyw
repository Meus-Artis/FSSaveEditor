try:
    import tkinter as tk
except ImportError:
    import win32ui
    import win32con
    if win32ui.MessageBox("Click yes to go to the Python download page and reinstall python with tcl/tk", "Tkinter Missing", win32con.MB_YESNO) == win32con.IDYES:
        import webbrowser
        url = "https://python.org/downloads"
        webbrowser.open(url, new=0, autoraise=True)
        exit()
    else:
        exit()
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import re
import os
try:
    import sv_ttk
except ImportError:
    messagebox.showerror("Error: Sun-Valley-ttk-theme missing", f"Attempting to automatically install required module: sv-ttk")
    import sys
    os.system(sys.executable + " -m pip install sv-ttk")
    import sv_ttk
try:
    import darkdetect
except ImportError:
    messagebox.showerror("Error: Darkdetect missing", f"Attempting to automatically install required module: darkdetect")
    import sys
    os.system(sys.executable + " -m pip install darkdetect")
    import darkdetect

with open("config.json", "r") as f:
    config = json.load(f)

try:
    with open("lang.json", "r") as f:
        lang = json.load(f)
except FileNotFoundError:
    lang = {}

class SaveEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Flexible Survival Save Editor")
        try:
            self.root.iconbitmap("favicon.ico")
        except:
            try:
                from PIL import Image, ImageTk
            except ImportError:
                messagebox.showerror("Error: PIL missing", f"Attempting to automatically install required module: PIL")
                import sys
                os.system(sys.executable + " -m pip install PIL")
                from PIL import Image, ImageTk
            ico = Image.open('favicon.ico')
            icon = ImageTk.PhotoImage(ico)
            self.root.iconphoto(True, icon)
        self.root.geometry("780x805")
        self.root.resizable(True, False)
        self.characters = []
        self.header_lines = []
        self.current_character_index = 0
        self.current_character = tk.StringVar()
        self.value_names = []
        self.value_types = {}
        self.first_name_key = None
        self.bool_string_values = {}
        self.button_frame = ttk.Frame(root)
        self.button_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky="s")
        self.dropdown_frame = ttk.Frame(self.button_frame)
        self.dropdown_frame.pack(side="left", padx=(5, 0))
        self.load_button = ttk.Button(self.button_frame, text="Load", command=self.load_save)
        self.load_button.pack(side="left", padx=5)
        self.current_file_label = ttk.Label(self.button_frame, text="No file loaded")
        self.current_file_label.pack(side="left", padx=5)
        self.save_button = ttk.Button(self.button_frame, text="Save", command=self.save_changes)
        self.save_button.pack(side="left", padx=5)
        self.delete_button = ttk.Button(self.button_frame, text="Delete Line", command=self.delete_current_line)
        self.delete_button.pack(side="left", padx=5)
        self.delete_button.pack_forget()
        self.editor_frame = ttk.Frame(root)
        self.editor_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)
        self.value_entries = {}

    def load_save(self):
        file_path = filedialog.askopenfilename(filetypes=[["Encoded/Decoded Save File", "*.glkdata"]])
        if not file_path:
            return
        self.current_file_label.config(text=os.path.basename(file_path))
        file_name = os.path.basename(file_path)
        config_key = file_name.replace(".glkdata", "")
        if config_key not in config:
            messagebox.showerror("Error", f"No configuration found for '{config_key}' in config.json.\nPlease contact Meus Artis if you are trying to load a supported file that isn't blank.")
            return
        self.line_by_line = False
        if isinstance(config[config_key], list) and len(config[config_key]) > 0 and config[config_key][0].get("flag") == "LineByLine":
            self.line_by_line = True
            self.value_names = [entry["name"] for entry in config[config_key][1:]]
            self.value_types = {entry["name"]: entry["type"] for entry in config[config_key][1:]}
        else:
            self.value_names = [entry["name"] for entry in config[config_key]]
            self.value_types = {entry["name"]: entry["type"] for entry in config[config_key]}
        self.first_name_key = self.value_names[0] if not self.line_by_line else None
        self.bool_string_values = {entry["name"]: entry["values"] for entry in config.get("BoolString", [])}
        with open(file_path, "r") as f:
            lines = f.readlines()
            self.header_lines = lines[:2]
            raw_lines = [line.strip() for line in lines[2:]]
            self.is_encoded = all(line.startswith("S") for line in raw_lines if line)
            if self.is_encoded:
                self.characters = [self.decode_glkdata_line(line) for line in raw_lines]
            else:
                self.characters = raw_lines
        if self.characters:
            if self.line_by_line:
                names = [f"Line {i+1}" for i in range(len(self.characters))]
                self.create_dropdown(names)
                self.current_character.set(names[0])
                self.current_character_index = 0
                self.delete_button.pack(side="left", padx=5)
            else:
                names = [self.parse_line(line).get(self.first_name_key, "Unknown") for line in self.characters]
                self.create_dropdown(names)
                if "yourself" in names:
                    self.current_character.set("yourself")
                    self.current_character_index = names.index("yourself")
                else:
                    self.current_character.set(names[0])
                    self.current_character_index = 0
                self.delete_button.pack_forget()
            self.display_character()

    def create_dropdown(self, names):
        for widget in self.dropdown_frame.winfo_children():
            widget.destroy()
        self.dropdown = ttk.Combobox(self.dropdown_frame, width=12, textvariable=self.current_character, state="readonly")
        self.dropdown["values"] = names
        self.dropdown.pack(side="right")
        if not self.line_by_line:
            dropdown_label_text = lang.get(self.first_name_key, self.first_name_key)
            label = ttk.Label(self.dropdown_frame, text=dropdown_label_text)
            label.pack(side="left", padx=(0, 5))
        self.dropdown.bind("<<ComboboxSelected>>", self.on_dropdown_select)

    def on_dropdown_select(self, event=None):
        selected_name = self.current_character.get()
        if self.line_by_line:
            self.current_character_index = int(selected_name.split()[1]) - 1
        else:
            names = [self.parse_line(line).get(self.first_name_key, "Unknown") for line in self.characters]
            self.current_character_index = names.index(selected_name)
        self.display_character()

    def parse_line(self, line):
        pattern = r'"(.*?)";|([^ ]+)'
        parts = [match[0] or match[1] for match in re.findall(pattern, line)]
        parsed_data = {}
        if self.line_by_line:
            for i in range(min(len(self.value_names), len(parts))):
                name = self.value_names[i]
                value = parts[i]
                if self.value_types[name] == "Integer":
                    try:
                        parsed_data[name] = int(value)
                    except ValueError:
                        parsed_data[name] = 0
                elif self.value_types[name] == "Bool":
                    parsed_data[name] = bool(int(value)) if value.isdigit() else False
                elif self.value_types[name] == "BoolString":
                    parsed_data[name] = value
                else:
                    parsed_data[name] = value
        else:
            for i in range(min(len(self.value_names), len(parts))):
                name = self.value_names[i]
                value = parts[i]
                if self.value_types[name] == "Integer":
                    try:
                        parsed_data[name] = int(value)
                    except ValueError:
                        parsed_data[name] = 0
                elif self.value_types[name] == "Bool":
                    parsed_data[name] = bool(int(value)) if value.isdigit() else False
                elif self.value_types[name] == "BoolString":
                    parsed_data[name] = value
                else:
                    parsed_data[name] = value
        return parsed_data

    def delete_current_line(self):
        if not self.characters or len(self.characters) <= 1:
            messagebox.showwarning("Delete Line", "Cannot delete the last line without crashing")
            return
        confirm = messagebox.askyesno("Delete Line", f"Are you sure you want to delete Line {self.current_character_index + 1}?")
        if not confirm:
            return
        del self.characters[self.current_character_index]
        names = [f"Line {i+1}" for i in range(len(self.characters))]
        self.dropdown["values"] = names
        if self.current_character_index >= len(self.characters):
            self.current_character_index = len(self.characters) - 1
        self.current_character.set(names[self.current_character_index])
        self.display_character()

    def display_character(self):
        for widget in self.editor_frame.winfo_children():
            widget.destroy()
        if not self.characters:
            return
        character_data = self.parse_line(self.characters[self.current_character_index])
        vcmd = self.root.register(self.validate_int)
        for idx, name in enumerate(self.value_names):
            row = idx // 3
            col = idx % 3
            display_name = lang.get(name, name)
            label = ttk.Label(self.editor_frame, text=display_name)
            label.grid(row=row, column=col * 2, padx=5, pady=5, sticky="e")
            if not self.line_by_line and name == self.first_name_key:
                var = tk.StringVar(value=character_data.get(name, ""))
                entry = ttk.Entry(self.editor_frame, width=14, textvariable=var, state="readonly")
                entry.grid(row=row, column=col * 2 + 1, padx=0, pady=1, sticky="w")
                self.value_entries[name] = var
                continue
            if self.value_types[name] == "Bool":
                var = tk.BooleanVar(value=character_data.get(name, False))
                entry = ttk.Checkbutton(self.editor_frame, variable=var)
            elif self.value_types[name] == "BoolString":
                var = tk.BooleanVar(value=character_data.get(name) == self.bool_string_values[name][1])
                entry = ttk.Checkbutton(self.editor_frame, variable=var)
            elif self.value_types[name] == "Integer":
                var = tk.StringVar(value=str(character_data.get(name, 0)))
                entry = ttk.Entry(self.editor_frame, width=4, textvariable=var, validate="key", validatecommand=(vcmd, "%P"))
            else:
                var = tk.StringVar(value=character_data.get(name, ""))
                entry = ttk.Entry(self.editor_frame, width=14, textvariable=var)
            entry.grid(row=row, column=col * 2 + 1, padx=0, pady=1, sticky="w")
            self.value_entries[name] = var

    def validate_int(self, value):
        try:
            int(value)
            return True
        except ValueError:
            return value == "" or value == "-"

    def decode_glkdata_line(self, line):
        output = ""
        i = 0
        while i < len(line):
            if line[i] == 'S':
                i += 1
                ascii_codes = ""
                while i < len(line) and line[i] != ';':
                    ascii_codes += line[i]
                    i += 1
                i += 1
                codes = ascii_codes.split(',')
                if codes == ['0']:
                    output += '""; '
                else:
                    if codes and codes[-1] == '0':
                        codes = codes[:-1]
                    decoded = ''.join(chr(int(c)) for c in codes if c.isdigit())
                    output += f'"{decoded}"; '
            else:
                start = i
                while i < len(line) and not line[i].isspace():
                    i += 1
                output += line[start:i] + " "
                while i < len(line) and line[i].isspace():
                    i += 1
        return output.strip()

    def encode_glkdata_line(self, line):
        output = []
        i = 0
        while i < len(line):
            if line[i] == '"':
                i += 1
                start = i
                while i < len(line) and line[i] != '"':
                    i += 1
                text = line[start:i]
                i += 1
                if i < len(line) and line[i] == ';':
                    i += 1
                if text in ("S0;", ""):
                    output.append("S0;")
                else:
                    ascii_str = ",".join(str(ord(c)) for c in text) + ",0"
                    output.append("S" + ascii_str + ";")
            elif not line[i].isspace():
                start = i
                while i < len(line) and not line[i].isspace():
                    i += 1
                output.append(line[start:i])
            else:
                i += 1
        return " ".join(output)

    def save_changes(self):
        if not self.characters:
            return
        values = []
        for name in self.value_names:
            if name == self.first_name_key and not self.line_by_line:
                current_data = self.parse_line(self.characters[self.current_character_index])
                values.append(f'"{current_data.get(name, "")}";')
                continue
            value = self.value_entries[name].get()
            if self.value_types[name] == "Bool":
                values.append("1" if value else "0")
            elif self.value_types[name] == "BoolString":
                values.append(f'"{self.bool_string_values[name][1] if value else self.bool_string_values[name][0]}"')
            elif self.value_types[name] == "Integer":
                values.append(value)
            else:
                values.append(f'"{value}";')
        self.characters[self.current_character_index] = " ".join(values) + " "
        file_path = filedialog.asksaveasfilename(defaultextension=".glkdata", filetypes=[["Encoded Save File", "*.glkdata"]])
        if not file_path:
            return
        modified_characters = [line if line.endswith(" ") else line + " " for line in self.characters]
        if self.is_encoded:
            modified_characters = [self.encode_glkdata_line(line).rstrip() + " " for line in modified_characters]
        with open(file_path, "w") as f:
            f.writelines(self.header_lines)
            f.write("\n".join(modified_characters) + "\n")
        messagebox.showinfo("Save Editor", "Changes saved successfully!")

if __name__ == "__main__":
    root = tk.Tk()
    sv_ttk.set_theme(darkdetect.theme())
    app = SaveEditor(root)
    root.after(100, app.load_save)
    root.mainloop()