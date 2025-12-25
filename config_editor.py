"""
Config Editor Window
Window untuk edit konfigurasi keyword dan video dengan UI yang user-friendly
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import shutil
from pathlib import Path
import re


class ConfigEditorWindow:
    """Window untuk edit konfigurasi"""
    
    def __init__(self, parent, config, on_save_callback=None):
        self.parent = parent
        self.config = config.copy()
        self.on_save_callback = on_save_callback
        self.keywords = list(config.get('comment_keywords', {}).items())
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title("Config Editor - Keyword & Video Management")
        self.window.geometry("900x650")
        self.window.transient(parent)
        
        self.setup_ui()
        self.load_keywords()
    
    def setup_ui(self):
        """Setup UI components"""
        # Main container
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Keyword & Video Configuration", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Toolbar
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(toolbar, text="➕ Add New", command=self.add_keyword, 
                  width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="🗑️ Delete", command=self.delete_keyword, 
                  width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="📁 Import Videos", command=self.import_videos, 
                  width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="💾 Save All", command=self.save_config, 
                  width=15).pack(side=tk.LEFT, padx=5)
        
        # Treeview frame
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview
        columns = ("Keyword/Regex", "Video File", "Response Text")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="tree headings",
                                yscrollcommand=scrollbar.set, selectmode="browse")
        
        self.tree.heading("#0", text="ID")
        self.tree.heading("Keyword/Regex", text="Keyword / Regex Pattern")
        self.tree.heading("Video File", text="Video File")
        self.tree.heading("Response Text", text="Response Text")
        
        self.tree.column("#0", width=50)
        self.tree.column("Keyword/Regex", width=250)
        self.tree.column("Video File", width=250)
        self.tree.column("Response Text", width=300)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tree.yview)
        
        # Bind double-click to edit
        self.tree.bind("<Double-1>", self.edit_keyword)
        
        # Status bar
        self.status_label = ttk.Label(main_frame, text="Ready", relief=tk.SUNKEN)
        self.status_label.pack(fill=tk.X, pady=(10, 0))
    
    def load_keywords(self):
        """Load keywords ke treeview"""
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Load from config
        keywords = self.config.get('comment_keywords', {})
        
        for idx, (keyword, data) in enumerate(keywords.items(), 1):
            video_file = Path(data.get('video_path', '')).name
            response = data.get('response_text', '')
            
            self.tree.insert("", tk.END, text=str(idx), 
                           values=(keyword, video_file, response),
                           tags=(keyword,))
        
        count = len(keywords)
        self.status_label.config(text=f"Loaded {count} keywords")
    
    def add_keyword(self):
        """Add new keyword"""
        dialog = KeywordEditorDialog(self.window, "Add New Keyword")
        
        if dialog.result:
            keyword = dialog.result['keyword']
            
            # Check duplicate
            if keyword in self.config.get('comment_keywords', {}):
                messagebox.showwarning("Duplicate", 
                                     f"Keyword '{keyword}' already exists!")
                return
            
            # Add to config
            if 'comment_keywords' not in self.config:
                self.config['comment_keywords'] = {}
            
            self.config['comment_keywords'][keyword] = {
                'video_path': dialog.result['video_path'],
                'response_text': dialog.result['response_text'],
                'is_regex': dialog.result.get('is_regex', False)
            }
            
            self.load_keywords()
            self.status_label.config(text=f"Added keyword: {keyword}")
    
    def edit_keyword(self, event=None):
        """Edit selected keyword"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a keyword to edit")
            return
        
        item = selection[0]
        keyword = self.tree.item(item)['tags'][0]
        
        # Get current data
        current_data = self.config['comment_keywords'][keyword]
        
        dialog = KeywordEditorDialog(
            self.window, 
            "Edit Keyword",
            initial_data={
                'keyword': keyword,
                'video_path': current_data.get('video_path', ''),
                'response_text': current_data.get('response_text', ''),
                'is_regex': current_data.get('is_regex', False)
            }
        )
        
        if dialog.result:
            new_keyword = dialog.result['keyword']
            
            # If keyword changed, delete old and add new
            if new_keyword != keyword:
                if new_keyword in self.config['comment_keywords']:
                    messagebox.showwarning("Duplicate", 
                                         f"Keyword '{new_keyword}' already exists!")
                    return
                del self.config['comment_keywords'][keyword]
            
            # Update data
            self.config['comment_keywords'][new_keyword] = {
                'video_path': dialog.result['video_path'],
                'response_text': dialog.result['response_text'],
                'is_regex': dialog.result.get('is_regex', False)
            }
            
            self.load_keywords()
            self.status_label.config(text=f"Updated keyword: {new_keyword}")
    
    def delete_keyword(self):
        """Delete selected keyword"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a keyword to delete")
            return
        
        item = selection[0]
        keyword = self.tree.item(item)['tags'][0]
        
        if messagebox.askyesno("Confirm Delete", 
                              f"Delete keyword '{keyword}'?"):
            del self.config['comment_keywords'][keyword]
            self.load_keywords()
            self.status_label.config(text=f"Deleted keyword: {keyword}")
    
    def import_videos(self):
        """Import multiple videos sekaligus"""
        files = filedialog.askopenfilenames(
            title="Select Video Files",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv"),
                ("All files", "*.*")
            ]
        )
        
        if not files:
            return
        
        videos_dir = Path("videos")
        videos_dir.mkdir(exist_ok=True)
        
        imported = 0
        for file_path in files:
            src = Path(file_path)
            
            # Copy to videos folder
            dst = videos_dir / src.name
            
            try:
                if not dst.exists() or messagebox.askyesno(
                    "File Exists", 
                    f"'{src.name}' already exists. Overwrite?"):
                    
                    shutil.copy2(src, dst)
                    imported += 1
                    
                    # Auto-create keyword if not exists
                    # Extract number from filename (e.g., product_1.mp4 -> 1)
                    match = re.search(r'(\d+)', src.stem)
                    if match:
                        num = match.group(1)
                        keyword = f"keranjang {num}"
                        
                        if keyword not in self.config.get('comment_keywords', {}):
                            if 'comment_keywords' not in self.config:
                                self.config['comment_keywords'] = {}
                            
                            self.config['comment_keywords'][keyword] = {
                                'video_path': f"videos/{src.name}",
                                'response_text': f"Terima kasih! Produk {num} akan kami proses 🎉"
                            }
            
            except Exception as e:
                messagebox.showerror("Error", f"Failed to copy {src.name}: {e}")
        
        self.load_keywords()
        self.status_label.config(text=f"Imported {imported} videos")
        messagebox.showinfo("Success", f"Successfully imported {imported} video(s)")
    
    def save_config(self):
        """Save configuration to file"""
        try:
            # Backup current config
            config_path = Path("config.json")
            if config_path.exists():
                backup_path = Path("config.json.backup")
                shutil.copy2(config_path, backup_path)
            
            # Save new config
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            self.status_label.config(text="✓ Configuration saved successfully!")
            messagebox.showinfo("Success", 
                              "Configuration saved successfully!\n\n"
                              "Changes will take effect after:\n"
                              "- Clicking 'Reload Config' in main window, or\n"
                              "- Restarting the application")
            
            # Call callback if provided
            if self.on_save_callback:
                self.on_save_callback(self.config)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration:\n{e}")


class KeywordEditorDialog:
    """Dialog untuk edit/add keyword"""
    
    def __init__(self, parent, title, initial_data=None):
        self.result = None
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("600x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (600 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (400 // 2)
        self.dialog.geometry(f"600x400+{x}+{y}")
        
        self.setup_ui(initial_data or {})
        
        # Wait for dialog to close
        self.dialog.wait_window()
    
    def setup_ui(self, initial_data):
        """Setup dialog UI"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Keyword / Regex
        row = 0
        ttk.Label(main_frame, text="Keyword / Regex Pattern:", 
                 font=("", 10, "bold")).grid(row=row, column=0, sticky=tk.W, pady=(0, 5))
        
        row += 1
        self.keyword_entry = ttk.Entry(main_frame, width=50, font=("", 10))
        self.keyword_entry.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        self.keyword_entry.insert(0, initial_data.get('keyword', ''))
        
        row += 1
        self.is_regex_var = tk.BooleanVar(value=initial_data.get('is_regex', False))
        regex_check = ttk.Checkbutton(main_frame, text="Use as Regex Pattern (advanced)", 
                                     variable=self.is_regex_var,
                                     command=self.toggle_regex_help)
        regex_check.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Regex help
        row += 1
        self.regex_help = tk.Text(main_frame, height=4, width=50, wrap=tk.WORD, 
                                 font=("Consolas", 8), bg="#f0f0f0", fg="#666")
        self.regex_help.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        self.regex_help.insert("1.0", 
            "Regex examples:\n"
            "• (keranjang|krnjg|cart)\\s*1  - Match 'keranjang 1', 'krnjg 1', 'cart 1'\n"
            "• keranjang\\s*[1-5]         - Match 'keranjang 1' through 'keranjang 5'\n"
            "• .*checkout.*               - Match any text containing 'checkout'")
        self.regex_help.config(state=tk.DISABLED)
        self.regex_help.grid_remove()  # Hide initially
        
        # Video file
        row += 1
        ttk.Label(main_frame, text="Video File:", 
                 font=("", 10, "bold")).grid(row=row, column=0, sticky=tk.W, pady=(10, 5))
        
        row += 1
        video_frame = ttk.Frame(main_frame)
        video_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.video_entry = ttk.Entry(video_frame, width=40, font=("", 10))
        self.video_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.video_entry.insert(0, initial_data.get('video_path', ''))
        
        ttk.Button(video_frame, text="Browse...", 
                  command=self.browse_video).pack(side=tk.LEFT)
        ttk.Button(video_frame, text="Upload", 
                  command=self.upload_video).pack(side=tk.LEFT, padx=(5, 0))
        
        # Response text
        row += 1
        ttk.Label(main_frame, text="Response Text (Optional):", 
                 font=("", 10, "bold")).grid(row=row, column=0, sticky=tk.W, pady=(10, 5))
        
        row += 1
        self.response_text = tk.Text(main_frame, height=5, width=50, wrap=tk.WORD, 
                                    font=("", 10))
        self.response_text.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        self.response_text.insert("1.0", initial_data.get('response_text', ''))
        
        # Buttons
        row += 1
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=(20, 0))
        
        ttk.Button(button_frame, text="Save", command=self.save, 
                  width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel, 
                  width=15).pack(side=tk.LEFT, padx=5)
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        
        # Focus on keyword entry
        self.keyword_entry.focus()
        
        # Bind Enter to save
        self.dialog.bind("<Return>", lambda e: self.save())
        self.dialog.bind("<Escape>", lambda e: self.cancel())
    
    def toggle_regex_help(self):
        """Show/hide regex help"""
        if self.is_regex_var.get():
            self.regex_help.grid()
        else:
            self.regex_help.grid_remove()
    
    def browse_video(self):
        """Browse for existing video in videos folder"""
        videos_dir = Path("videos")
        
        if not videos_dir.exists():
            videos_dir.mkdir()
        
        file = filedialog.askopenfilename(
            title="Select Video File",
            initialdir=videos_dir,
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv"),
                ("All files", "*.*")
            ]
        )
        
        if file:
            # Make path relative to project root
            file_path = Path(file)
            try:
                rel_path = file_path.relative_to(Path.cwd())
                self.video_entry.delete(0, tk.END)
                self.video_entry.insert(0, str(rel_path).replace("\\", "/"))
            except ValueError:
                # If not in project dir, use absolute path
                self.video_entry.delete(0, tk.END)
                self.video_entry.insert(0, str(file_path).replace("\\", "/"))
    
    def upload_video(self):
        """Upload new video file"""
        file = filedialog.askopenfilename(
            title="Upload Video File",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv"),
                ("All files", "*.*")
            ]
        )
        
        if not file:
            return
        
        src = Path(file)
        videos_dir = Path("videos")
        videos_dir.mkdir(exist_ok=True)
        
        # Ask for filename
        filename = tk.simpledialog.askstring(
            "Filename",
            "Enter filename (without extension):",
            initialvalue=src.stem,
            parent=self.dialog
        )
        
        if not filename:
            return
        
        # Copy file
        dst = videos_dir / f"{filename}{src.suffix}"
        
        try:
            if dst.exists():
                if not messagebox.askyesno("File Exists", 
                                          f"'{dst.name}' already exists. Overwrite?",
                                          parent=self.dialog):
                    return
            
            shutil.copy2(src, dst)
            
            # Update entry
            self.video_entry.delete(0, tk.END)
            self.video_entry.insert(0, f"videos/{dst.name}")
            
            messagebox.showinfo("Success", 
                              f"Video uploaded successfully!\n{dst.name}",
                              parent=self.dialog)
        
        except Exception as e:
            messagebox.showerror("Error", 
                               f"Failed to upload video:\n{e}",
                               parent=self.dialog)
    
    def save(self):
        """Save and close"""
        keyword = self.keyword_entry.get().strip()
        video_path = self.video_entry.get().strip()
        response = self.response_text.get("1.0", tk.END).strip()
        is_regex = self.is_regex_var.get()
        
        # Validation
        if not keyword:
            messagebox.showwarning("Validation Error", 
                                 "Keyword/Regex cannot be empty!",
                                 parent=self.dialog)
            return
        
        if not video_path:
            messagebox.showwarning("Validation Error", 
                                 "Video file cannot be empty!",
                                 parent=self.dialog)
            return
        
        # Test regex if enabled
        if is_regex:
            try:
                re.compile(keyword)
            except re.error as e:
                messagebox.showerror("Invalid Regex", 
                                   f"Invalid regex pattern:\n{e}",
                                   parent=self.dialog)
                return
        
        self.result = {
            'keyword': keyword,
            'video_path': video_path,
            'response_text': response,
            'is_regex': is_regex
        }
        
        self.dialog.destroy()
    
    def cancel(self):
        """Cancel and close"""
        self.result = None
        self.dialog.destroy()


# For testing
if __name__ == "__main__":
    import tkinter.simpledialog
    
    # Test config
    test_config = {
        "obs_settings": {
            "host": "localhost",
            "port": 4455
        },
        "comment_keywords": {
            "keranjang 1": {
                "video_path": "videos/product_1.mp4",
                "response_text": "Terima kasih!"
            },
            "keranjang 2": {
                "video_path": "videos/product_2.mp4",
                "response_text": "Siap diproses!"
            }
        }
    }
    
    root = tk.Tk()
    root.withdraw()
    
    editor = ConfigEditorWindow(root, test_config)
    
    root.mainloop()
