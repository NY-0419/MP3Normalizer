import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
from tkinterdnd2 import DND_FILES
from tkinter import font as tkfont
import threading
import os
import sys
import time
from pathlib import Path
from audio_processor import AudioProcessor, ProcessingCancelled
from settings import load_settings, save_settings
from logger import setup_logger

class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, settings, callback):
        super().__init__(parent)
        self.title("詳細設定")
        self.geometry("420x700")
        self.resizable(False, False)
        self.settings = settings
        self.callback = callback

        # モーダルウィンドウ化
        self.transient(parent)
        self.grab_set()

        # 右上の「×」ボタンで閉じたときも確実にモーダルを解除する
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.create_widgets()

    def on_close(self):
        # 右上の「×」ボタンで閉じたときも確実にモーダルを解除する
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()


    def create_widgets(self):
        settings_frame = ctk.CTkScrollableFrame(self)
        settings_frame.pack(fill="both", expand=True, padx=10, pady=(10, 0))

        lbl_prev = ctk.CTkLabel(settings_frame, text="プレビュー再生秒数:")
        lbl_prev.pack(anchor="w", padx=20, pady=(20, 5))
        self.combo_duration = ctk.CTkComboBox(settings_frame, values=["5秒", "10秒", "15秒", "30秒"], state="readonly")
        self.combo_duration.pack(fill="x", padx=20, pady=5)
        current_dur = f"{self.settings.get('preview_duration', 10)}秒"
        self.combo_duration.set(current_dur if current_dur in ["5秒", "10秒", "15秒", "30秒"] else "10秒")

        lbl_mode = ctk.CTkLabel(settings_frame, text="ノーマライズ後の保存方法:")
        lbl_mode.pack(anchor="w", padx=20, pady=(15, 5))
        self.combo_mode = ctk.CTkComboBox(settings_frame, values=["別名で保存 (_norm)", "ファイル名を変更しない"], state="readonly")
        self.combo_mode.pack(fill="x", padx=20, pady=5)
        current_mode = self.settings.get('save_mode', 'copy')
        self.combo_mode.set("ファイル名を変更しない" if current_mode == "replace" else "別名で保存 (_norm)")

        lbl_format = ctk.CTkLabel(settings_frame, text="出力形式:")
        lbl_format.pack(anchor="w", padx=20, pady=(15, 5))
        self.combo_format = ctk.CTkComboBox(
            settings_frame,
            values=["入力形式に合わせる", "MP3", "M4A (AAC)", "M4A (ALAC)", "WAV", "FLAC"],
            state="readonly"
        )
        self.combo_format.pack(fill="x", padx=20, pady=5)
        current_format = self.settings.get("output_format", "same").lower()
        format_labels = {
            "same": "入力形式に合わせる",
            "mp3": "MP3",
            "m4a": "M4A (AAC)",
            "m4a_alac": "M4A (ALAC)",
            "wav": "WAV",
            "flac": "FLAC"
        }
        self.combo_format.set(format_labels.get(current_format, "入力形式に合わせる"))

        lbl_font_size = ctk.CTkLabel(settings_frame, text="ファイル一覧のフォントサイズ (pt):")
        lbl_font_size.pack(anchor="w", padx=20, pady=(15, 5))
        self.combo_font_size = ctk.CTkComboBox(
            settings_frame,
            values=[str(size) for size in range(5, 26, 5)],
            state="readonly"
        )
        self.combo_font_size.pack(fill="x", padx=20, pady=5)
        current_font_size = str(self.settings.get("file_list_font_size", 10))
        self.combo_font_size.set(current_font_size if current_font_size in self.combo_font_size.cget("values") else "10")

        lbl_audio_bitrate = ctk.CTkLabel(settings_frame, text="MP3 / M4Aビットレート (kbps):")
        lbl_audio_bitrate.pack(anchor="w", padx=20, pady=(15, 5))
        self.combo_audio_bitrate = ctk.CTkComboBox(
            settings_frame,
            values=["128", "192", "256", "320"],
            state="readonly"
        )
        self.combo_audio_bitrate.pack(fill="x", padx=20, pady=5)
        bitrate = self.settings.get("audio_bitrate")
        if bitrate is None:
            bitrate = self.settings.get("mp3_bitrate", self.settings.get("m4a_bitrate", 320))
        self.combo_audio_bitrate.set(str(bitrate) if str(bitrate) in self.combo_audio_bitrate.cget("values") else "320")

        lbl_flac_compression = ctk.CTkLabel(settings_frame, text="FLAC圧縮レベル (0-8):")
        lbl_flac_compression.pack(anchor="w", padx=20, pady=(15, 5))
        self.combo_flac_compression = ctk.CTkComboBox(settings_frame, values=[str(level) for level in range(9)], state="readonly")
        self.combo_flac_compression.pack(fill="x", padx=20, pady=5)
        self.combo_flac_compression.set(str(self.settings.get("flac_compression", 5)))

        lbl_theme = ctk.CTkLabel(settings_frame, text="外観テーマ (ダーク/ライト):")
        lbl_theme.pack(anchor="w", padx=20, pady=(15, 5))
        self.combo_appearance = ctk.CTkComboBox(settings_frame, values=["System", "Dark", "Light"], state="readonly")
        self.combo_appearance.pack(fill="x", padx=20, pady=5)
        self.combo_appearance.set(self.settings.get('appearance_mode', 'System'))

        btn_save = ctk.CTkButton(self, text="設定を保存", command=self.save_and_close, fg_color="#28a745", hover_color="#218838")
        btn_save.pack(fill="x", padx=20, pady=(10, 15))

    def save_and_close(self):
        dur_str = self.combo_duration.get().replace("秒", "")
        self.settings["preview_duration"] = int(dur_str)

        mode_str = self.combo_mode.get()
        self.settings["save_mode"] = "replace" if mode_str == "ファイル名を変更しない" else "copy"
        selected_format = self.combo_format.get()
        format_values = {
            "入力形式に合わせる": "same",
            "MP3": "mp3",
            "M4A (AAC)": "m4a",
            "M4A (ALAC)": "m4a_alac",
            "WAV": "wav",
            "FLAC": "flac"
        }
        self.settings["output_format"] = format_values[selected_format]
        self.settings["file_list_font_size"] = int(self.combo_font_size.get())
        self.settings["audio_bitrate"] = int(self.combo_audio_bitrate.get())
        self.settings.pop("mp3_bitrate", None)
        self.settings.pop("m4a_bitrate", None)
        self.settings["flac_compression"] = int(self.combo_flac_compression.get())

        self.settings["appearance_mode"] = self.combo_appearance.get()

        save_settings(self.settings)
        self.callback()
        self.on_close()


class MP3NormalizerApp:
    def __init__(self, root):
        self.root = root
        self.set_window_icon()
        self.root.title("音声一括ノーマライザー")
        self.root.geometry("850x710")

        self.logger = setup_logger()
        self.settings = load_settings()
        self.last_appearance_mode = self.settings.get("appearance_mode", "System")
        
        ctk.set_appearance_mode(self.settings.get("appearance_mode", "System"))
        ctk.set_default_color_theme("blue")

        self.audio_processor = AudioProcessor()
        self.file_list = []
        self.processing_thread = None
        self.closing = False

        self.create_widgets()
        self.load_ui_settings()
        self.root.protocol("WM_DELETE_WINDOW", self.close_application)

    def set_window_icon(self):
        icon_candidates = [
            Path(__file__).resolve().parent / "image.ico",
            Path(getattr(sys, "_MEIPASS", "")) / "image.ico",
            Path(sys.executable).resolve().parent / "image.ico",
            Path(sys.executable).resolve().parent / "_internal" / "image.ico",
        ]
        for icon_path in icon_candidates:
            if icon_path.exists():
                try:
                    self.root.iconbitmap(default=str(icon_path))
                except Exception:
                    pass
                break

    def create_widgets(self):
        top_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        top_frame.pack(fill="x", padx=15, pady=10)

        self.btn_add = ctk.CTkButton(top_frame, text="ファイル追加", command=self.add_files, width=120)
        self.btn_add.pack(side="left", padx=5)

        self.btn_remove = ctk.CTkButton(top_frame, text="選択解除", command=self.remove_file, fg_color="gray", hover_color=("gray50", "gray30"), width=100)
        self.btn_remove.pack(side="left", padx=5)

        self.btn_clear = ctk.CTkButton(top_frame, text="一覧クリア", command=self.clear_files, fg_color="#d9534f", hover_color="#c9302c", width=100)
        self.btn_clear.pack(side="left", padx=5)

        self.btn_settings = ctk.CTkButton(top_frame, text="⚙ 詳細設定", command=self.open_settings_dialog, fg_color="#6c757d", hover_color="#5a6268", width=100)
        self.btn_settings.pack(side="right", padx=5)

        center_frame = ctk.CTkFrame(self.root)
        center_frame.pack(fill="both", expand=True, padx=15, pady=5)

        import tkinter as ttk_mod
        
        preview_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
        preview_frame.pack(fill="x", padx=5, pady=5)

        dur = self.settings.get("preview_duration", 10)
        self.btn_preview = ctk.CTkButton(preview_frame, text=f"▶ 選択曲を{dur}秒プレビュー再生", command=self.start_preview, fg_color="#28a745", hover_color="#218838", width=220)
        self.btn_preview.pack(side="left", padx=5)

        self.btn_stop = ctk.CTkButton(preview_frame, text="■ 停止", command=self.stop_preview, fg_color="#6c757d", hover_color="#5a6268", width=80)
        self.btn_stop.pack(side="left", padx=5)

        self.btn_measure = ctk.CTkButton(
            preview_frame,
            text="音量を測定",
            command=self.measure_selected_file,
            fg_color="#6c757d",
            hover_color="#5a6268",
            width=100
        )
        self.btn_measure.pack(side="left", padx=5)

        self.lbl_measurement = ctk.CTkLabel(
            preview_frame,
            text="ラウドネス: -- LUFS / ピーク: -- dBTP",
            text_color="gray"
        )
        self.lbl_measurement.pack(side="left", padx=10)

        self.lbl_file_count = ctk.CTkLabel(
            preview_frame,
            text="待機中: 0件",
            text_color="gray"
        )
        self.lbl_file_count.pack(side="right", padx=10)

        tree_container = ttk_mod.Frame(center_frame)
        tree_container.pack(fill="both", expand=True, padx=5, pady=5)

        columns = ("filename", "size", "status", "path")
        tree_style = ttk.Style(self.root)
        font_size = self.get_file_list_font_size()
        self.tree_font = tkfont.Font(family="Yu Gothic UI", size=font_size)
        self.tree_heading_font = tkfont.Font(family="Yu Gothic UI", size=font_size, weight="bold")
        tree_style.configure(
            "Audio.Treeview",
            font=self.tree_font,
            rowheight=self.get_file_list_row_height(font_size)
        )
        tree_style.configure(
            "Audio.Treeview.Heading",
            font=self.tree_heading_font
        )
        self.tree = ttk.Treeview(
            tree_container,
            columns=columns,
            show="headings",
            selectmode="extended",
            height=12,
            style="Audio.Treeview"
        )
        self.range_selection_anchor = None
        self.tree.bind("<ButtonPress-1>", self.start_range_selection, add="+")
        self.tree.bind("<B1-Motion>", self.update_range_selection, add="+")
        self.tree.heading("filename", text="ファイル名")
        self.tree.heading("size", text="サイズ")
        self.tree.heading("status", text="処理状態")
        self.tree.heading("path", text="フルパス")

        self.tree.column("filename", width=220)
        self.tree.column("size", width=90, anchor="e")
        self.tree.column("status", width=110, anchor="center")
        self.tree.column("path", width=360)

        scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.drop_target_register(DND_FILES)
        self.tree.dnd_bind("<<Drop>>", self.handle_file_drop)

        bottom_frame = ctk.CTkFrame(self.root, corner_radius=10)
        bottom_frame.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(bottom_frame, text="目標ラウドネス (LUFS):").grid(row=0, column=0, sticky="w", padx=10, pady=8)
        self.spin_loudness = ctk.CTkEntry(bottom_frame, width=100)
        self.spin_loudness.grid(row=0, column=1, sticky="w", padx=10, pady=8)

        ctk.CTkLabel(bottom_frame, text="目標トゥルーピーク (dBTP):").grid(row=0, column=2, sticky="w", padx=10, pady=8)
        self.spin_peak = ctk.CTkEntry(bottom_frame, width=100)
        self.spin_peak.grid(row=0, column=3, sticky="w", padx=10, pady=8)

        ctk.CTkLabel(bottom_frame, text="出力先フォルダ:").grid(row=1, column=0, sticky="w", padx=10, pady=8)
        self.entry_output = ctk.CTkEntry(bottom_frame, width=380)
        self.entry_output.grid(row=1, column=1, columnspan=2, sticky="ew", padx=10, pady=8)
        
        self.btn_browse = ctk.CTkButton(bottom_frame, text="参照...", command=self.browse_output, width=90)
        self.btn_browse.grid(row=1, column=3, sticky="w", padx=10, pady=8)

        self.progress = ctk.CTkProgressBar(bottom_frame, orientation="horizontal")
        self.progress.set(0)
        self.progress.grid(row=2, column=0, columnspan=3, sticky="ew", padx=10, pady=(15, 5))

        self.btn_start = ctk.CTkButton(bottom_frame, text="一括処理開始", command=self.start_processing, fg_color="#007bff", hover_color="#0056b3", width=120)
        self.btn_start.grid(row=2, column=3, sticky="ew", padx=10, pady=(15, 5))

        self.btn_cancel = ctk.CTkButton(bottom_frame, text="処理キャンセル", command=self.cancel_processing, state="disabled", fg_color="#d9534f", hover_color="#c9302c", width=120)
        self.btn_cancel.grid(row=3, column=3, sticky="ew", padx=10, pady=(0, 5))

        self.lbl_status_detail = ctk.CTkLabel(bottom_frame, text="待機中...", text_color="gray")
        self.lbl_status_detail.grid(row=4, column=0, columnspan=4, sticky="w", padx=10, pady=(0, 10))

    def load_ui_settings(self):
        self.spin_loudness.insert(0, str(self.settings.get("target_loudness", -14.0)))
        self.spin_peak.insert(0, str(self.settings.get("target_true_peak", -1.0)))
        out_dir = self.settings.get("output_dir", "")
        if out_dir:
            self.entry_output.insert(0, out_dir)

    def open_settings_dialog(self):
        SettingsDialog(self.root, self.settings, self.on_settings_updated)

    def on_settings_updated(self):
        appearance_mode = self.settings.get("appearance_mode", "System")
        if appearance_mode != self.last_appearance_mode:
            ctk.set_appearance_mode(appearance_mode)
            self.last_appearance_mode = appearance_mode
        self.restore_file_list_view()
        self.apply_file_list_font()
        dur = self.settings.get("preview_duration", 10)
        self.btn_preview.configure(text=f"▶ 選択曲を{dur}秒プレビュー再生")

    def get_file_list_font_size(self):
        try:
            return max(5, min(30, int(self.settings.get("file_list_font_size", 10))))
        except (TypeError, ValueError):
            return 10

    def get_file_list_row_height(self, font_size):
        return max(22, font_size + 14)

    def apply_file_list_font(self):
        font_size = self.get_file_list_font_size()
        self.tree_font.configure(size=font_size)
        self.tree_heading_font.configure(size=font_size)
        ttk.Style(self.root).configure(
            "Audio.Treeview",
            font=self.tree_font,
            rowheight=self.get_file_list_row_height(font_size)
        )

    def restore_file_list_view(self):
        if len(self.tree.get_children()) == len(self.file_list):
            self.update_file_count()
            return

        for item_id in self.tree.get_children():
            self.tree.delete(item_id)
        for item in self.file_list:
            self.tree.insert(
                "",
                "end",
                values=(item["filename"], item["size"], item.get("status", "待機中"), item["path"])
            )
        self.update_file_count()

    def update_file_count(self):
        waiting_count = sum(
            1 for item in self.file_list
            if item.get("status", "待機中") == "待機中"
        )
        self.lbl_file_count.configure(text=f"待機中: {waiting_count}件")

    def save_ui_settings(self):
        try:
            self.settings["target_loudness"] = float(self.spin_loudness.get())
            self.settings["target_true_peak"] = float(self.spin_peak.get())
            self.settings["output_dir"] = self.entry_output.get()
            save_settings(self.settings)
        except ValueError:
            pass

    def add_files(self):
        files = filedialog.askopenfilenames(
            title="音声ファイルを選択",
            filetypes=[
                ("Audio Files", "*.mp3 *.m4a *.wav *.flac"),
                ("MP3 Files", "*.mp3"),
                ("M4A Files", "*.m4a"),
                ("WAV Files", "*.wav"),
                ("FLAC Files", "*.flac"),
                ("All Files", "*.*")
            ]
        )
        self.add_audio_files(files)

    def handle_file_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        self.add_audio_files(files)

    def add_audio_files(self, files):
        supported_extensions = {".mp3", ".m4a", ".wav", ".flac"}
        rejected_files = []
        for f in files:
            try:
                is_invalid_file = (
                    os.path.splitext(f)[1].lower() not in supported_extensions
                    or os.path.getsize(f) == 0
                )
            except OSError:
                is_invalid_file = True
            if is_invalid_file:
                rejected_files.append(os.path.basename(f))
                continue
            if not any(item['path'] == f for item in self.file_list):
                try:
                    size_bytes = os.path.getsize(f)
                    size_str = f"{size_bytes / (1024*1024):.2f} MB"
                except Exception:
                    size_str = "不明"
                
                item = {
                    "path": f,
                    "filename": os.path.basename(f),
                    "size": size_str,
                    "status": "待機中"
                }
                self.file_list.append(item)
                self.tree.insert("", "end", values=(item["filename"], item["size"], item["status"], item["path"]))
        self.update_file_count()
        if rejected_files:
            messagebox.showwarning(
                "追加できないファイル",
                f"音声形式でないか空のため、{len(rejected_files)}件を追加しませんでした。"
            )

    def start_range_selection(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            self.range_selection_anchor = None
            return

        self.range_selection_anchor = item_id
        if event.state & 0x0004:
            self.tree.selection_add(item_id)
        else:
            self.tree.selection_set(item_id)

    def update_range_selection(self, event):
        if not self.range_selection_anchor:
            return

        current_item = self.tree.identify_row(event.y)
        if not current_item:
            return

        item_ids = self.tree.get_children("")
        try:
            start_index = item_ids.index(self.range_selection_anchor)
            end_index = item_ids.index(current_item)
        except ValueError:
            return

        if start_index > end_index:
            start_index, end_index = end_index, start_index
        selected_items = item_ids[start_index:end_index + 1]
        if event.state & 0x0004:
            self.tree.selection_add(selected_items)
        else:
            self.tree.selection_set(selected_items)

    def remove_file(self):
        selected = self.tree.selection()
        for sel in selected:
            values = self.tree.item(sel, "values")
            path_to_remove = values[3]
            self.file_list = [item for item in self.file_list if item["path"] != path_to_remove]
            self.tree.delete(sel)
        self.update_file_count()

    def clear_files(self):
        self.stop_preview()
        self.file_list.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.update_file_count()

    def browse_output(self):
        dir_path = filedialog.askdirectory(title="出力先フォルダを選択")
        if dir_path:
            self.entry_output.delete(0, 'end')
            self.entry_output.insert(0, dir_path)

    def start_preview(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("警告", "プレビュー再生するファイルを1つ選択してください。")
            return

        values = self.tree.item(selected[0], "values")
        input_path = values[3]

        try:
            target_i = float(self.spin_loudness.get())
            target_tp = float(self.spin_peak.get())
        except ValueError:
            target_i, target_tp = -14.0, -1.0

        dur = self.settings.get("preview_duration", 10)
        
        try:
            # ストリーミング再生開始（一時ファイルを一切作らない）
            self.audio_processor.start_stream_preview(input_path, duration=dur, target_i=target_i, target_tp=target_tp)
        except Exception as e:
            messagebox.showerror("エラー", f"プレビュー再生に失敗しました:\n{str(e)}")

    def stop_preview(self):
        # ストリーミング即時停止
        self.audio_processor.stop_stream_preview()

    def measure_selected_file(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("警告", "ラウドネスを測定するファイルを選択してください。")
            return

        input_paths = [
            self.tree.item(item_id, "values")[3]
            for item_id in selected
        ]
        try:
            target_i = float(self.spin_loudness.get())
            target_tp = float(self.spin_peak.get())
        except ValueError:
            target_i, target_tp = -14.0, -1.0

        self.btn_measure.configure(state="disabled", text="測定中...")
        self.lbl_measurement.configure(text="ラウドネス: 測定中...")

        threading.Thread(
            target=self.measure_file_thread,
            args=(input_paths, target_i, target_tp),
            daemon=True
        ).start()

    def measure_file_thread(self, input_paths, target_i, target_tp):
        try:
            measurements = []
            for input_path in input_paths:
                measured = self.audio_processor.ffmpeg_manager.analyze_loudness(
                    input_path,
                    target_i=target_i,
                    target_tp=target_tp
                )
                if not measured:
                    raise RuntimeError(
                        f"ラウドネス測定結果を取得できませんでした:\n{input_path}"
                    )
                measurements.append((
                    float(measured["input_i"]),
                    float(measured["input_tp"])
                ))

            loudness = sum(item[0] for item in measurements) / len(measurements)
            true_peak = sum(item[1] for item in measurements) / len(measurements)
            self.root.after(
                0,
                lambda: self.show_measurement_result(
                    loudness,
                    true_peak,
                    len(measurements)
                )
            )
        except (KeyError, TypeError, ValueError) as error:
            self.root.after(0, lambda: self.show_measurement_error(str(error)))
        except Exception as error:
            self.logger.error(f"Failed to measure selected loudness: {error}")
            self.root.after(0, lambda: self.show_measurement_error(str(error)))

    def show_measurement_result(self, loudness, true_peak, count):
        if self.closing:
            return
        prefix = "平均 " if count > 1 else ""
        self.lbl_measurement.configure(
            text=f"{prefix}ラウドネス: {loudness:.2f} LUFS / ピーク: {true_peak:.2f} dBTP"
        )
        self.btn_measure.configure(state="normal", text="音量を測定")

    def show_measurement_error(self, error_message):
        if self.closing:
            return
        self.lbl_measurement.configure(text="ラウドネス: 測定失敗")
        self.btn_measure.configure(state="normal", text="音量を測定")
        messagebox.showerror("測定エラー", f"ラウドネス測定に失敗しました:\n{error_message}")

    def start_processing(self):
        if not self.file_list:
            messagebox.showwarning("警告", "処理するファイルが選択されていません。")
            return

        save_mode = self.settings.get("save_mode", "copy")
        output_format = self.settings.get("output_format", "same")
        audio_bitrate = self.settings.get("audio_bitrate", 320)
        flac_compression = self.settings.get("flac_compression", 5)
        out_dir = self.entry_output.get()

        if not out_dir or not os.path.isdir(out_dir):
            messagebox.showwarning("警告", "有効な出力先フォルダを指定してください。")
            return

        if save_mode == "replace":
            output_dir = os.path.normcase(os.path.abspath(out_dir))
            source_dirs = {
                os.path.normcase(os.path.abspath(os.path.dirname(item["path"])))
                for item in self.file_list
            }
            if output_dir in source_dirs:
                confirmed = messagebox.askyesno(
                    "上書きの確認",
                    "入力元と出力先が同じフォルダです。\n"
                    "元のファイルが上書きされる可能性があります。\n"
                    "続行しますか？"
                )
                if not confirmed:
                    return

        if not self.audio_processor.ffmpeg_manager.check_ffmpeg():
            messagebox.showerror("エラー", "FFmpegが見つからないか、実行パスが通っていません。")
            return

        self.save_ui_settings()
        self.stop_preview()
        self.audio_processor.processing_cancel_event.clear()
        self.toggle_controls(state="disabled")
        try:
            target_i = float(self.spin_loudness.get())
            target_tp = float(self.spin_peak.get())
        except ValueError:
            target_i, target_tp = -14.0, -1.0

        self.processing_thread = threading.Thread(
            target=self.process_thread,
            args=(out_dir, save_mode, output_format, target_i, target_tp, audio_bitrate, flac_compression),
            daemon=True
        )
        self.processing_thread.start()

    def close_application(self):
        if self.closing:
            return

        self.closing = True
        self.audio_processor.cancel_processing()
        self.audio_processor.stop_stream_preview()
        self.toggle_controls(state="disabled")
        self.root.after(50, self.finish_close_application)

    def finish_close_application(self):
        if self.processing_thread and self.processing_thread.is_alive():
            self.root.after(50, self.finish_close_application)
            return
        self.root.destroy()

    def cancel_processing(self):
        self.audio_processor.cancel_processing()
        self.lbl_status_detail.configure(text="キャンセル処理中...")

    def process_thread(self, out_dir, save_mode, output_format, target_i, target_tp, audio_bitrate, flac_compression):
        total = len(self.file_list)
        success_count = 0
        fail_count = 0
        error_logs = []  # エラー詳細を蓄積するリスト

        start_time = time.time()

        cancelled = False
        for i, item in enumerate(self.file_list):
            self.update_tree_status(item["path"], "処理中...")
            try:
                self.audio_processor.process_file(
                    item["path"],
                    out_dir,
                    target_i=target_i,
                    target_tp=target_tp,
                    save_mode=save_mode,
                    output_format=output_format,
                    audio_bitrate=audio_bitrate,
                    flac_compression=flac_compression
                )
                self.update_tree_status(item["path"], "完了")
                success_count += 1
            except ProcessingCancelled:
                self.update_tree_status(item["path"], "キャンセル")
                cancelled = True
                break
            except Exception as e:
                import traceback
                tb_str = traceback.format_exc()
                error_msg = f"■ ファイル: {os.path.basename(item['path'])}\nパス: {item['path']}\nエラー: {str(e)}\n\n【詳細トレースバック】\n{tb_str}\n" + "-"*50
                error_logs.append(error_msg)
                
                self.logger.error(f"Failed to process {item['path']}: {e}")
                self.update_tree_status(item["path"], "失敗")
                fail_count += 1

            completed = i + 1
            elapsed = time.time() - start_time
            avg_time = elapsed / completed
            remaining_files = total - completed
            rem_seconds = int(avg_time * remaining_files)

            if rem_seconds >= 60:
                rem_str = f"約 {rem_seconds // 60}分 {rem_seconds % 60}秒"
            else:
                rem_str = f"約 {rem_seconds}秒"

            status_text = f"進捗: {completed}/{total}件完了 (成功: {success_count}, 失敗: {fail_count}) | 残り時間: {rem_str if remaining_files > 0 else 'まもなく完了'}"
            
            prog_val = completed / total
            self.root.after(0, lambda txt=status_text, p=prog_val: [
                self.progress.set(p),
                self.lbl_status_detail.configure(text=txt)
            ])

        self.root.after(0, lambda: self.toggle_controls(state="normal"))
        if cancelled:
            self.root.after(0, lambda: self.lbl_status_detail.configure(
                text=f"処理をキャンセルしました (成功: {success_count}件, 失敗: {fail_count}件)"
            ))
            return

        self.root.after(0, lambda: self.lbl_status_detail.configure(
            text=f"処理完了 (成功: {success_count}件, 失敗: {fail_count}件)"
        ))
        
        # 処理完了後のポップアップ表示
        if fail_count > 0:
            self.root.after(0, lambda: self.show_error_log_dialog(
                "処理完了（一部失敗）", 
                error_logs
            ))
        else:
            self.root.after(0, lambda: messagebox.showinfo(
                "処理完了",
                f"一括処理が完了しました。\n成功: {success_count}件\n失敗: {fail_count}件"
            ))

    def toggle_controls(self, state):
        self.btn_start.configure(state=state)
        self.btn_add.configure(state=state)
        self.btn_remove.configure(state=state)
        self.btn_clear.configure(state=state)
        self.btn_preview.configure(state=state)
        self.btn_measure.configure(state=state)
        self.btn_settings.configure(state=state)
        self.btn_cancel.configure(state="normal" if state == "disabled" else "disabled")

    def update_tree_status(self, path, status):
        for item in self.file_list:
            if item["path"] == path:
                item["status"] = status
                break

        self.root.after(0, self._update_tree_status_view, path, status)

    def _update_tree_status_view(self, path, status):
        for child in self.tree.get_children():
            values = self.tree.item(child, "values")
            if values[3] == path:
                self.tree.item(child, values=(values[0], values[1], status, values[3]))
                break
        self.update_file_count()

    def show_error_log_dialog(self, title, error_messages):
        """スクロール可能なテキストボックスで長文エラーを表示するダイアログ"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(title)
        dialog.geometry("650, 450")
        dialog.transient(self.root)
        dialog.grab_set()

        # ウィンドウを中央付近に配置
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 650) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 450) // 2
        dialog.geometry(f"+{x}+{y}")

        lbl_title = ctk.CTkLabel(dialog, text="⚠️ 処理中に以下のエラーが発生しました", font=("", 14, "bold"), text_color="#ff6b6b")
        lbl_title.pack(padx=20, pady=(20, 10), anchor="w")

        # スクロール可能なテキストボックス (CustomTkinter標準)
        textbox = ctk.CTkTextbox(dialog, width=610, height=310, font=("Consolas", 12))
        textbox.pack(padx=20, pady=5, fill="both", expand=True)
        
        # エラーログを挿入して読み取り専用にする
        full_text = "\n".join(error_messages)
        textbox.insert("1.0", full_text)
        textbox.configure(state="disabled")

        btn_close = ctk.CTkButton(dialog, text="閉じる", width=120, command=dialog.destroy)
        btn_close.pack(padx=20, pady=(10, 20))
