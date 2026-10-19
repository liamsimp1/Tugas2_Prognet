import os
import zipfile
import threading
import urllib.request
import tkinter as tk
from tkinter import messagebox, filedialog

class FixedProgressBarDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("File Downloader")
        self.root.geometry("480x620")
        self.root.resizable(False, False)

        self.COLOR_BG = "#FFFFFF"           # Latar belakang putih murni
        self.COLOR_CARD_BG = "#F8FAFC"      # Latar belakang input/kartu
        self.COLOR_TEXT_PRIMARY = "#1E293B" # Teks gelap
        self.COLOR_TEXT_BLUE = "#3B82F6"    # Teks/label biru
        self.COLOR_BORDER = "#CBD5E1"       # Garis tepi tipis
        self.COLOR_BLUE_PRIMARY = "#3B82F6" # Biru utama
        self.COLOR_BLUE_HOVER = "#2563EB"   # Biru tombol saat ditekan
        self.COLOR_BLUE_LIGHT = "#EFF6FF"   # Biru muda untuk tombol sekunder

        self.root.configure(bg=self.COLOR_BG)

        # State Variables
        self.is_downloading = False
        self.cancel_download = False
        self.download_history = []
        self.file_path = ""

        # Inisialisasi Tampilan
        self.setup_ui()

    def create_rounded_rect(self, canvas, x1, y1, x2, y2, radius=10, **kwargs):
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]
        return canvas.create_polygon(points, **kwargs, smooth=True)

    def setup_ui(self):
        # 1. HEADER SECTION
        header_frame = tk.Frame(self.root, bg=self.COLOR_BG)
        header_frame.pack(fill=tk.X, pady=(20, 10))

        lbl_title = tk.Label(
            header_frame,
            text="File Downloader ☁",
            font=("Segoe UI", 16, "bold"),
            fg=self.COLOR_TEXT_BLUE,
            bg=self.COLOR_BG
        )
        lbl_title.pack()

        # Garis Putus-putus Horizontal
        canvas_line = tk.Canvas(self.root, height=10, bg=self.COLOR_BG, highlightthickness=0)
        canvas_line.pack(fill=tk.X, padx=20, pady=(0, 10))
        canvas_line.create_line(0, 5, 480, 5, dash=(4, 4), fill=self.COLOR_BORDER, width=1)

        # Form Container
        form_frame = tk.Frame(self.root, bg=self.COLOR_BG, padx=30)
        form_frame.pack(fill=tk.BOTH, expand=True)

        # 2. FIELD: URL FILE
        lbl_url = tk.Label(form_frame, text="URL File:", font=("Segoe UI", 9, "bold"), fg=self.COLOR_TEXT_BLUE, bg=self.COLOR_BG)
        lbl_url.pack(anchor="w", pady=(0, 4))

        url_canvas = tk.Canvas(form_frame, height=40, bg=self.COLOR_BG, highlightthickness=0)
        url_canvas.pack(fill=tk.X, pady=(0, 14))
        self.create_rounded_rect(url_canvas, 1, 1, 418, 38, radius=10, fill=self.COLOR_CARD_BG, outline=self.COLOR_BORDER, width=1)

        icon_pencil = tk.Label(url_canvas, text="✎", font=("Segoe UI", 12), fg=self.COLOR_TEXT_BLUE, bg=self.COLOR_CARD_BG)
        icon_pencil.place(x=12, y=6)

        self.url_entry = tk.Entry(url_canvas, font=("Segoe UI", 9), bd=0, bg=self.COLOR_CARD_BG, fg=self.COLOR_TEXT_PRIMARY, highlightthickness=0)
        self.url_entry.place(x=40, y=9, width=365, height=22)

        # 3. FIELD: DIREKTORI TUJUAN
        lbl_dir = tk.Label(form_frame, text="Direktori Tujuan:", font=("Segoe UI", 9, "bold"), fg=self.COLOR_TEXT_BLUE, bg=self.COLOR_BG)
        lbl_dir.pack(anchor="w", pady=(0, 4))

        dir_container = tk.Frame(form_frame, bg=self.COLOR_BG)
        dir_container.pack(fill=tk.X, pady=(0, 14))

        dir_canvas = tk.Canvas(dir_container, height=40, width=300, bg=self.COLOR_BG, highlightthickness=0)
        dir_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.create_rounded_rect(dir_canvas, 1, 1, 298, 38, radius=10, fill=self.COLOR_CARD_BG, outline=self.COLOR_BORDER, width=1)

        icon_folder = tk.Label(dir_canvas, text="📁", font=("Segoe UI", 11), fg=self.COLOR_TEXT_BLUE, bg=self.COLOR_CARD_BG)
        icon_folder.place(x=12, y=8)

        self.dir_entry = tk.Entry(dir_canvas, font=("Segoe UI", 9), bd=0, bg=self.COLOR_CARD_BG, fg=self.COLOR_TEXT_PRIMARY, highlightthickness=0)
        self.dir_entry.place(x=40, y=9, width=245, height=22)
        self.dir_entry.insert(0, os.getcwd())

        # Tombol Pilih...
        self.btn_browse_canvas = tk.Canvas(dir_container, height=40, width=105, bg=self.COLOR_BG, highlightthickness=0, cursor="hand2")
        self.btn_browse_canvas.pack(side=tk.RIGHT, padx=(10, 0))
        self.create_rounded_rect(self.btn_browse_canvas, 1, 1, 103, 38, radius=10, fill=self.COLOR_BLUE_LIGHT, outline=self.COLOR_BLUE_PRIMARY, width=1)
        self.btn_browse_canvas.create_text(52, 19, text="Pilih...", font=("Segoe UI", 9, "bold"), fill=self.COLOR_BLUE_PRIMARY)
        self.btn_browse_canvas.bind("<Button-1>", lambda e: self.browse_directory())

        # 4. PROGRESS BAR & TOMBOL BATAL (✕)
        progress_row = tk.Frame(form_frame, bg=self.COLOR_BG)
        progress_row.pack(fill=tk.X, pady=(0, 2))

        # Canvas Progress Bar (Lebar otomatis menyesuaikan sisa ruang)
        self.progress_canvas = tk.Canvas(progress_row, height=24, bg=self.COLOR_BG, highlightthickness=0)
        self.progress_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        # Simbol Silang Batal (✕)
        self.btn_cancel = tk.Label(progress_row, text="✕", font=("Segoe UI", 11, "bold"), fg=self.COLOR_BORDER, bg=self.COLOR_BG, cursor="hand2")
        self.btn_cancel.pack(side=tk.RIGHT)
        self.btn_cancel.bind("<Button-1>", lambda e: self.cancel_download_action())

        # Sub Info Progress Text
        info_row = tk.Frame(form_frame, bg=self.COLOR_BG)
        info_row.pack(fill=tk.X, pady=(2, 14))

        self.lbl_progress_percent = tk.Label(info_row, text="Progress: 0%", font=("Segoe UI", 8, "bold"), fg=self.COLOR_TEXT_BLUE, bg=self.COLOR_BG)
        self.lbl_progress_percent.pack(side=tk.LEFT)

        self.lbl_progress_size = tk.Label(info_row, text="0.0 Mb", font=("Segoe UI", 8, "bold"), fg=self.COLOR_TEXT_BLUE, bg=self.COLOR_BG)
        self.lbl_progress_size.pack(side=tk.RIGHT)

        # 5. TOMBOL UTAMA ("Mulai Mengunduh")
        self.btn_download_canvas = tk.Canvas(form_frame, height=42, bg=self.COLOR_BG, highlightthickness=0, cursor="hand2")
        self.btn_download_canvas.pack(fill=tk.X, pady=(0, 20))
        self.draw_download_button("Mulai Mengunduh")
        self.btn_download_canvas.bind("<Button-1>", lambda e: self.start_download_thread())

        # 6. RIWAYAT UNDUHAN SECTION
        lbl_history_title = tk.Label(form_frame, text="Tiga File Unduhan Terakhir:", font=("Segoe UI", 9, "bold"), fg=self.COLOR_TEXT_BLUE, bg=self.COLOR_BG)
        lbl_history_title.pack(anchor="w", pady=(0, 8))

        self.history_frame = tk.Frame(form_frame, bg=self.COLOR_BG)
        self.history_frame.pack(fill=tk.X)

        self.draw_progress(0)
        self.render_history()

        # FOOTER
        footer_label = tk.Label(self.root, text="©AJCU1", font=("Segoe UI", 8, "bold"), fg=self.COLOR_TEXT_BLUE, bg=self.COLOR_BG)
        footer_label.pack(side=tk.BOTTOM, pady=12)

    # -----------------------------------------------------------------
    # RENDERING VISUAL (PERBAIKAN UKURAN PROGRESS BAR)
    # -----------------------------------------------------------------
    def draw_download_button(self, text):
        """Menggambar tombol utama"""
        self.btn_download_canvas.delete("all")
        self.create_rounded_rect(self.btn_download_canvas, 1, 1, 418, 40, radius=10, fill=self.COLOR_BLUE_PRIMARY, outline=self.COLOR_BLUE_HOVER, width=1)
        self.btn_download_canvas.create_text(210, 20, text=text, font=("Segoe UI", 10, "bold"), fill="#FFFFFF")

    def draw_progress(self, percent):
        """Menggambar progress bar dengan lebar presisi agar tidak menutupi tanda X"""
        self.progress_canvas.delete("all")
        
        # Mendapatkan lebar aktual canvas secara dinamis (fallback ke 380 jika belum di-render)
        width = self.progress_canvas.winfo_width()
        if width <= 1:
            width = 380
            
        height = 22

        # Outer Rounded Track Bar
        self.create_rounded_rect(self.progress_canvas, 1, 1, width - 2, height, radius=10, fill=self.COLOR_CARD_BG, outline=self.COLOR_BORDER, width=1)

        # Inner Blue Progress Fill
        if percent > 0:
            fill_w = max(15, (percent / 100.0) * (width - 4))
            self.create_rounded_rect(self.progress_canvas, 2, 2, fill_w, height - 1, radius=8, fill=self.COLOR_BLUE_PRIMARY, outline="")

    # -----------------------------------------------------------------
    # LOGIKA PENGUNDUHAN
    # -----------------------------------------------------------------
    def browse_directory(self):
        chosen_dir = filedialog.askdirectory()
        if chosen_dir:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, chosen_dir)

    def start_download_thread(self):
        if self.is_downloading:
            return

        url = self.url_entry.get().strip()
        save_dir = self.dir_entry.get().strip()

        if not url:
            messagebox.showwarning("Peringatan", "URL File tidak boleh kosong!")
            return
        if not os.path.isdir(save_dir):
            messagebox.showwarning("Peringatan", "Direktori tujuan tidak valid!")
            return

        self.is_downloading = True
        self.cancel_download = False
        self.draw_download_button("Mengunduh...")
        self.draw_progress(0)
        self.lbl_progress_percent.config(text="Progress: 0%")
        self.lbl_progress_size.config(text="0.0 Mb")

        threading.Thread(target=self.download_file, args=(url, save_dir), daemon=True).start()

    def download_file(self, url, save_dir):
        try:
            filename = url.split("/")[-1].split("?")[0]
            if not filename or "." not in filename:
                filename = "downloaded_file.zip"

            self.file_path = os.path.join(save_dir, filename)

            def reporthook(block_num, block_size, total_size):
                if self.cancel_download:
                    raise Exception("DOWNLOAD_CANCELED")

                downloaded = block_num * block_size
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    percent = min(percent, 100)
                    mb_downloaded = downloaded / (1024 * 1024)
                    self.root.after(0, lambda: self.update_progress_ui(percent, mb_downloaded))

            urllib.request.urlretrieve(url, self.file_path, reporthook=reporthook)
            self.root.after(0, lambda: self.download_completed(filename))

        except Exception as e:
            if str(e) == "DOWNLOAD_CANCELED":
                self.root.after(0, self.download_canceled)
            else:
                self.root.after(0, lambda: self.download_error(str(e)))

    def update_progress_ui(self, percent, mb_downloaded):
        self.draw_progress(percent)
        self.lbl_progress_percent.config(text=f"Progress: {int(percent)}%")
        self.lbl_progress_size.config(text=f"{mb_downloaded:.1f} Mb")

    def cancel_download_action(self):
        if self.is_downloading:
            self.cancel_download = True

    def download_canceled(self):
        self.is_downloading = False
        if os.path.exists(self.file_path):
            try:
                os.remove(self.file_path)
            except:
                pass
        self.draw_download_button("Mulai Mengunduh")
        self.draw_progress(0)
        self.lbl_progress_percent.config(text="Progress: 0%")
        self.lbl_progress_size.config(text="0.0 Mb")
        messagebox.showwarning("Dibatalkan", "Proses mengunduh telah dibatalkan.")

    def download_completed(self, filename):
        self.is_downloading = False
        self.draw_progress(100)
        self.lbl_progress_percent.config(text="Progress: 100%")
        self.draw_download_button("Mulai Mengunduh")

        self.download_history.insert(0, filename)
        if len(self.download_history) > 3:
            self.download_history.pop()

        self.render_history()
        messagebox.showinfo("Informasi", f"File '{filename}' berhasil didownload!")

        if zipfile.is_zipfile(self.file_path):
            resp = messagebox.askyesno("Ekstrak File", f"File '{filename}' berformat ZIP.\nApakah Anda ingin mengekstrak file ini sekarang?")
            if resp:
                self.extract_zip()

    def download_error(self, err):
        self.is_downloading = False
        self.draw_download_button("Mulai Mengunduh")
        messagebox.showerror("Gagal", f"Gagal mengunduh file:\n{err}")

    def extract_zip(self):
        try:
            extract_dir = os.path.splitext(self.file_path)[0]
            os.makedirs(extract_dir, exist_ok=True)

            with zipfile.ZipFile(self.file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            messagebox.showinfo("Sukses", f"File berhasil diekstrak ke:\n{extract_dir}")
        except Exception as e:
            messagebox.showerror("Error Ekstraksi", f"Gagal mengekstrak ZIP:\n{str(e)}")

    def render_history(self):
        """Menampilkan daftar 3 file terakhir"""
        for widget in self.history_frame.winfo_children():
            widget.destroy()

        if not self.download_history:
            return

        for filename in self.download_history:
            item_canvas = tk.Canvas(self.history_frame, height=36, bg=self.COLOR_BG, highlightthickness=0)
            item_canvas.pack(fill=tk.X, pady=3)

            # Latar belakang kartu
            self.create_rounded_rect(item_canvas, 1, 1, 418, 34, radius=8, fill=self.COLOR_CARD_BG, outline=self.COLOR_BORDER, width=1)

            # Icon Dokumen & Nama File
            item_canvas.create_text(25, 17, text=f"📄  {filename}", font=("Segoe UI", 9, "bold"), fill=self.COLOR_TEXT_BLUE, anchor="w")
            
            # Lingkaran Centang Biru
            item_canvas.create_oval(390, 8, 408, 26, fill=self.COLOR_BLUE_PRIMARY, outline="")
            item_canvas.create_text(399, 17, text="✓", font=("Segoe UI", 9, "bold"), fill="#FFFFFF")

if __name__ == "__main__":
    root = tk.Tk()
    app = FixedProgressBarDownloader(root)
    root.mainloop()