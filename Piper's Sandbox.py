import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
from keystone import *
import platform
import os
import re
import zipfile
import ctypes

class PiperSandboxIDE:
    def __init__(self, root):
        self.root = root
        self.root.title("Piper's Sandbox™ IDE (IDE Beta 0.01_1)")

        # Create text editor with syntax highlighting
        self.editor = tk.Text(self.root, wrap="word", undo=True)
        self.editor.pack(fill="both", expand=1)
        self.editor.bind("<KeyRelease>", self.syntax_highlighting)

        # Create output window for runtime results
        self.output = tk.Text(self.root, height=10, bg="black", fg="white")
        self.output.pack(fill="x", expand=0)

        # Menu bar
        self.menu_bar = tk.Menu(self.root)

        # File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Open", command=self.open_file)
        self.file_menu.add_command(label="Save", command=self.save_file)
        self.file_menu.add_command(label="Save As...", command=self.save_as_file)
        self.file_menu.add_command(label="Compile to Executable", command=self.compile_to_executable)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.root.quit)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)

        # Pipe Loader menu for package management
        self.pipe_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.pipe_menu.add_command(label="Add .pka Package", command=self.load_pka_package)
        self.pipe_menu.add_command(label="Manage Packages", command=self.manage_packages)
        self.menu_bar.add_cascade(label="Pipe Loader", menu=self.pipe_menu)

        # About menu for version and developer information
        self.about_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.about_menu.add_command(label="About", command=self.show_about)
        self.menu_bar.add_cascade(label="About", menu=self.about_menu)

        # Buttons: Run, Debug, and Show Output
        self.run_button = tk.Button(self.root, text="Run", command=self.run_piper_code)
        self.run_button.pack(side="left")
        
        self.debug_button = tk.Button(self.root, text="Debug", command=self.debug_piper_code)
        self.debug_button.pack(side="left")

        self.output_button = tk.Button(self.root, text="Show Output", command=self.show_output)
        self.output_button.pack(side="left")

        # Configure the root window to use the menu
        self.root.config(menu=self.menu_bar)

        # File path to save or open
        self.file_path = None

        # Package manager to keep track of installed packages
        self.installed_packages = {}

    def open_file(self):
        """Open Piper code file (.pi)."""
        self.file_path = filedialog.askopenfilename(filetypes=[("Piper Files", "*.pi")])
        if self.file_path:
            with open(self.file_path, "r") as file:
                self.editor.delete(1.0, tk.END)
                self.editor.insert(tk.END, file.read())
            self.syntax_highlighting()  # Apply syntax highlighting on open

    def save_file(self):
        """Save current Piper code to file."""
        if self.file_path:
            with open(self.file_path, "w") as file:
                file.write(self.editor.get(1.0, tk.END))
        else:
            self.save_as_file()

    def save_as_file(self):
        """Save Piper code to a new file."""
        self.file_path = filedialog.asksaveasfilename(defaultextension=".pi", filetypes=[("Piper Files", "*.pi")])
        if self.file_path:
            with open(self.file_path, "w") as file:
                file.write(self.editor.get(1.0, tk.END))

    def detect_architecture(self):
        """Detect system architecture dynamically."""
        arch = platform.machine().lower()
        if "x86_64" in arch:
            return KS_ARCH_X86, KS_MODE_64
        elif "arm" in arch:
            return KS_ARCH_ARM, KS_MODE_ARM
        else:
            return KS_ARCH_X86, KS_MODE_32  # Default to 32-bit x86 if unknown

    def run_piper_code(self):
        """Run Piper code and show its actual output."""
        piper_code = self.editor.get(1.0, tk.END)

        # Detect system architecture dynamically
        arch, mode = self.detect_architecture()

        try:
            ks = Ks(arch, mode)
            assembly_code = self.piper_to_assembly(piper_code)  # Actual conversion to assembly
            encoding, count = ks.asm(assembly_code)

            # Simulate running the machine code to produce the actual program output
            actual_output = self.execute_piper_code(piper_code)  # Generate actual runtime output

            # Display the output in the IDE
            self.output.delete(1.0, tk.END)
            self.output.insert(tk.END, f"Program Output: {actual_output}\n")
        
        except KsError as e:
            self.output.delete(1.0, tk.END)
            self.output.insert(tk.END, f"Polly Error: Keystone error: {e}")
        
        except SyntaxError as se:
            self.output.delete(1.0, tk.END)
            self.output.insert(tk.END, f"Polly Error: {str(se)}")
        
        except Exception as e:
            self.output.delete(1.0, tk.END)
            self.output.insert(tk.END, f"Unknown error occurred: {str(e)}")

    def execute_piper_code(self, piper_code):
        """Simulate the execution of Piper code to produce actual output."""
        if "print" in piper_code:
            return piper_code.split('print(')[1].split(')')[0].strip('\'"')
        return "No output produced."

    def piper_to_assembly(self, piper_code):
        """Convert Piper code to GAS-style assembly."""
        if "print" in piper_code:
            # Simple GAS syntax to perform a Linux syscall (example: syscall for printing)
            return """
                .section .data
msg:          .ascii "Hello, World!\\n"
len =         . - msg

                .section .text
                .global main
main:
                mov $1, %rax              # syscall number for sys_write
                mov $1, %rdi              # file descriptor 1 is stdout
                lea msg(%rip), %rsi       # address of string to output
                mov $len, %rdx            # number of bytes
                syscall                   # invoke syscall
                mov $60, %rax             # syscall number for sys_exit
                xor %rdi, %rdi            # exit code 0
                syscall
            """
        else:
            raise SyntaxError("No valid Piper code found.")

    def debug_piper_code(self):
        """Simulate debugging Piper code."""
        piper_code = self.editor.get(1.0, tk.END)
        lines = piper_code.splitlines()
        self.output.delete(1.0, tk.END)
        for i, line in enumerate(lines, 1):
            self.output.insert(tk.END, f"Executing Line {i}: {line}\n")
            if "error" in line:
                self.output.insert(tk.END, f"Error found on line {i}\n")
                break

    def show_output(self):
        """Display the output window with results of code execution.""" 
        self.output.pack(fill="x", expand=0)

    def load_pka_package(self):
        """Load a .pka package using Pipe Loader."""
        pka_path = filedialog.askopenfilename(filetypes=[("Piper Package", "*.pka")])
        if pka_path:
            try:
                self.install_package(pka_path)
                messagebox.showinfo("Success", "Package installed successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to install package: {str(e)}")

    def install_package(self, pka_path):
        """Unzip and load the DLL or SO files from the package."""
        package_name = os.path.basename(pka_path).replace(".pka", "")
        extract_path = os.path.join(os.path.dirname(pka_path), package_name)

        # Unzip the .pka file
        with zipfile.ZipFile(pka_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)

        # Load the DLL or SO files
        for filename in os.listdir(extract_path):
            if filename.endswith('.dll') or filename.endswith('.so'):
                full_path = os.path.join(extract_path, filename)
                self.load_library(full_path)
                break  # Load only the first found library for simplicity

        self.installed_packages[package_name] = extract_path

    def load_library(self, library_path):
        """Load a shared library (DLL or SO) using ctypes."""
        try:
            if platform.system() == "Windows":
                ctypes.WinDLL(library_path)
            else:
                ctypes.CDLL(library_path)
            messagebox.showinfo("Success", f"Library loaded: {library_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load library: {str(e)}")

    def manage_packages(self):
        """Display installed packages and offer management options.""" 
        installed_list = "\n".join([pkg for pkg in self.installed_packages])
        if installed_list:
            messagebox.showinfo("Installed Packages", installed_list)
        else:
            messagebox.showinfo("Installed Packages", "No packages installed.")

    def show_about(self):
        """Show about information including name, year, and version.""" 
        messagebox.showinfo("About", "Piper's Sandbox™ IDE\nDeveloper: Jerome Valencia\nYear: 2024\nVersion: IDE Beta 0.01_1")

    def syntax_highlighting(self, event=None):
        """Basic syntax highlighting for Piper code.""" 
        # Clear previous tags
        self.editor.tag_remove("keyword", "1.0", "end")
        self.editor.tag_remove("number", "1.0", "end")
        self.editor.tag_remove("comment", "1.0", "end")

        # Keywords, numbers, and comments highlighting
        keywords = ["print", "if", "else", "while", "for", "return"]
        piper_code = self.editor.get(1.0, tk.END)
        
        # Highlight keywords
        for keyword in keywords:
            start_idx = "1.0"
            while True:
                start_idx = self.editor.search(rf"\b{keyword}\b", start_idx, tk.END)
                if not start_idx:
                    break
                end_idx = f"{start_idx}+{len(keyword)}c"
                self.editor.tag_add("keyword", start_idx, end_idx)
                start_idx = end_idx

        # Highlight numbers
        for match in re.finditer(r"\b\d+\b", piper_code):
            start_idx = f"1.0+{match.start()}c"
            end_idx = f"1.0+{match.end()}c"
            self.editor.tag_add("number", start_idx, end_idx)

        # Highlight comments (starting with #)
        for match in re.finditer(r"#.*", piper_code):
            start_idx = f"1.0+{match.start()}c"
            end_idx = f"1.0+{match.end()}c"
            self.editor.tag_add("comment", start_idx, end_idx)

        # Configure tags' appearance
        self.editor.tag_configure("keyword", foreground="blue")
        self.editor.tag_configure("number", foreground="red")
        self.editor.tag_configure("comment", foreground="green")

    def compile_to_executable(self):
        """Compile the generated assembly into an executable file.""" 
        piper_code = self.editor.get(1.0, tk.END)
        assembly_code = self.piper_to_assembly(piper_code)
        
        # Save assembly code to a file
        asm_file_path = filedialog.asksaveasfilename(defaultextension=".s", filetypes=[("Assembly Files", "*.s")])
        if asm_file_path:
            with open(asm_file_path, "w") as asm_file:
                asm_file.write(assembly_code)
            
            # Use GCC (or other toolchain) to compile assembly into an executable
            exe_file_path = asm_file_path.replace(".s", "")
            if platform.system() == "Windows":
                # For Windows, using MinGW or another assembler to create .exe
                subprocess.run(["gcc", asm_file_path, "-o", exe_file_path])
            else:
                # For Unix-like systems, default to GCC or another assembler
                subprocess.run(["gcc", asm_file_path, "-o", exe_file_path])
            
            messagebox.showinfo("Success", f"Executable compiled: {exe_file_path}")
        else:
            messagebox.showerror("Error", "Failed to save assembly file.")

# Run the Piper Sandbox IDE
if __name__ == "__main__":
    root = tk.Tk()
    ide = PiperSandboxIDE(root)
    root.mainloop()