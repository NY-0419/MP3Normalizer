import subprocess
import os
import json
import math
import threading
import shutil
import sys
from pathlib import Path
import numpy as np
import sounddevice as sd

class ProcessingCancelled(Exception):
    """ユーザー操作で音声処理がキャンセルされたことを示す例外。"""

    pass

class FFmpegManager:
    """同梱版またはPATH上のFFmpegを検出して実行する管理クラス。"""

    def __init__(self, ffmpeg_path=None):
        self.ffmpeg_path = self._resolve_ffmpeg_path(ffmpeg_path)

    @staticmethod
    def _resolve_ffmpeg_path(ffmpeg_path):
        if ffmpeg_path:
            explicit_path = Path(ffmpeg_path)
            if explicit_path.exists():
                return str(explicit_path)

        executable_name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
        # 配布版では展開先を先に探し、開発時はソースフォルダを探す。
        search_roots = [Path(__file__).resolve().parent]
        if getattr(sys, "frozen", False):
            search_roots.insert(0, Path(sys.executable).resolve().parent)
            search_roots.insert(0, Path(getattr(sys, "_MEIPASS", sys.executable)))

        for root in search_roots:
            bundled_path = root / "ffmpeg" / "bin" / executable_name
            if bundled_path.exists():
                return str(bundled_path)

        return shutil.which(executable_name) or executable_name

    def check_ffmpeg(self):
        try:
            subprocess.run([self.ffmpeg_path, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def analyze_loudness(self, input_file, target_i=-14.0, target_tp=-1.0, target_lra=11.0, cancel_event=None):
        """
        一括処理用の正確なラウドネス測定（2パスの1パス目）
        """
        cmd = [
            self.ffmpeg_path,
            "-nostdin",
            "-i", input_file,
            "-af", f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}:print_format=json",
            "-f", "null",
            "-"
        ]
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            startupinfo=startupinfo,
            encoding="utf-8",
            errors="ignore"
        )
        try:
            while True:
                try:
                    _, stderr = process.communicate(timeout=0.2)
                    break
                except subprocess.TimeoutExpired:
                    if cancel_event and cancel_event.is_set():
                        process.terminate()
                        process.communicate()
                        raise ProcessingCancelled()
        finally:
            if process.poll() is None:
                process.terminate()

        if process.returncode != 0:
            return None

        try:
            json_start = stderr.rfind("{")
            json_end = stderr.rfind("}") + 1
            if json_start != -1 and json_end != -1:
                return json.loads(stderr[json_start:json_end])
        except Exception:
            pass
        return None


class AudioProcessor:
    """ラウドネス解析、変換、プレビューを担当する音声処理クラス。"""

    def __init__(self, ffmpeg_path="ffmpeg"):
        self.ffmpeg_manager = FFmpegManager(ffmpeg_path)
        self.stream_process = None
        self.audio_stream = None
        self.preview_lock = threading.Lock()
        self.preview_stop_event = None
        self.processing_lock = threading.Lock()
        self.processing_process = None
        self.processing_cancel_event = threading.Event()

    def cancel_processing(self):
        self.processing_cancel_event.set()
        with self.processing_lock:
            process = self.processing_process
        if process and process.poll() is None:
            try:
                process.terminate()
            except OSError:
                pass

    @staticmethod
    def _sanitize_measurements(measured):
        defaults = {
            "input_i": -24.0,
            "input_tp": -2.0,
            "input_lra": 7.0,
            "input_thresh": -70.0,
            "target_offset": 0.0,
        }
        sanitized = dict(measured)
        for key, default in defaults.items():
            try:
                value = float(sanitized.get(key, default))
                sanitized[key] = value if math.isfinite(value) else default
            except (TypeError, ValueError):
                sanitized[key] = default
        return sanitized

    @staticmethod
    def _can_use_two_pass_measurements(measured):
        return (
            -99.0 <= measured["input_i"] <= 0.0
            and math.isfinite(measured["input_tp"])
            and math.isfinite(measured["input_lra"])
            and math.isfinite(measured["input_thresh"])
            and math.isfinite(measured["target_offset"])
        )

    def process_file(self, input_path, output_dir, target_i=-14.0, target_tp=-1.0, target_lra=11.0, save_mode="copy", output_format="same", mp3_bitrate=320, m4a_bitrate=256, flac_compression=5, audio_bitrate=None):
        """
        一括処理用：測定データを用いた高精度な2パス・ラウドネス正規化
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"入力ファイルが見つかりません: {input_path}")
        if self.processing_cancel_event.is_set():
            raise ProcessingCancelled()
        if save_mode not in {"copy", "replace"}:
            raise ValueError(f"未対応の保存方法です: {save_mode}")
        if output_format not in {"same", "mp3", "m4a", "m4a_alac", "wav", "flac"}:
            raise ValueError(f"未対応の出力形式です: {output_format}")
        if not output_dir:
            raise ValueError("出力先フォルダが必要です")
        if not os.path.isdir(output_dir):
            raise NotADirectoryError(f"出力先フォルダが見つかりません: {output_dir}")

        measured = self.ffmpeg_manager.analyze_loudness(
            input_path,
            target_i=target_i,
            target_tp=target_tp,
            target_lra=target_lra,
            cancel_event=self.processing_cancel_event
        )
        if not measured:
            raise RuntimeError("音声のラウドネス測定に失敗しました。")
        measured = self._sanitize_measurements(measured)
        if self.processing_cancel_event.is_set():
            raise ProcessingCancelled()

        if self._can_use_two_pass_measurements(measured):
            af_filter = (
                f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}:"
                f"measured_I={measured['input_i']}:"
                f"measured_TP={measured['input_tp']}:"
                f"measured_LRA={measured['input_lra']}:"
                f"measured_thresh={measured['input_thresh']}:"
                f"offset={measured['target_offset']}:linear=true:print_format=json"
            )
        else:
            # FFmpeg rejects measured_I above 0 LUFS; use dynamic normalization
            # for unusually loud or otherwise unusable measurement results.
            af_filter = f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}"

        base_name = os.path.basename(input_path)
        name, ext = os.path.splitext(base_name)
        if output_format == "same":
            output_format = ext.lower().lstrip(".")
        if output_format not in {"mp3", "m4a", "m4a_alac", "wav", "flac"}:
            raise ValueError(f"入力形式に対応する出力形式ではありません: {ext}")
        if audio_bitrate is not None:
            if audio_bitrate not in {128, 192, 256, 320}:
                raise ValueError("ビットレートの設定値が不正です")
            mp3_bitrate = audio_bitrate
            m4a_bitrate = audio_bitrate
        if mp3_bitrate not in {128, 192, 256, 320} or m4a_bitrate not in {96, 128, 192, 256, 320} or flac_compression not in set(range(9)):
            raise ValueError("出力品質の設定値が不正です")

        output_extension = "m4a" if output_format == "m4a_alac" else output_format
        target_dir = output_dir
        if save_mode == "replace":
            output_filename = f"{name}.{output_extension}"
        else:
            output_filename = f"{name}_norm.{output_extension}"
        output_path = os.path.join(target_dir, output_filename)
        if save_mode == "copy":
            counter = 1
            while os.path.exists(output_path):
                output_filename = f"{name}_norm_{counter}.{output_extension}"
                output_path = os.path.join(target_dir, output_filename)
                counter += 1
        temp_output = os.path.splitext(output_path)[0] + f".tmp.{output_extension}"

        cmd = [
            self.ffmpeg_manager.ffmpeg_path,
            "-nostdin",
            "-i", input_path,
            "-map", "0:a:0",
            "-map_metadata", "0",
            "-af", f"{af_filter},asetnsamples=n=4096:p=0" if output_format == "flac" else af_filter,
        ]

        if output_format in {"mp3", "m4a", "m4a_alac", "flac"}:
            cmd.extend([
                "-map", "0:v:0?",
                "-c:v", "png" if output_format == "flac" else "mjpeg",
                "-q:v", "2",
                "-disposition:v:0", "attached_pic",
                "-metadata:s:v:0", "title=Album cover",
                "-metadata:s:v:0", "comment=Cover (front)"
            ])

        if output_format == "mp3":
            cmd.extend([
                "-c:a", "libmp3lame",
                "-b:a", f"{mp3_bitrate}k",
                "-f", "mp3",
                "-id3v2_version", "3",
                "-write_id3v1", "1"
            ])
        elif output_format == "m4a":
            cmd.extend(["-c:a", "aac", "-b:a", f"{m4a_bitrate}k", "-movflags", "+faststart", "-f", "ipod"])
        elif output_format == "m4a_alac":
            cmd.extend(["-c:a", "alac", "-movflags", "+faststart", "-f", "ipod"])
        elif output_format == "flac":
            cmd.extend(["-c:a", "flac", "-sample_fmt", "s16", "-compression_level", str(flac_compression), "-f", "flac"])
        else:
            cmd.extend(["-c:a", "pcm_s16le", "-f", "wav"])

        cmd.extend(["-y", temp_output])

        if self.processing_cancel_event.is_set():
            raise ProcessingCancelled()

        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=startupinfo,
            encoding="utf-8",
            errors="ignore"
        )
        with self.processing_lock:
            self.processing_process = process

        try:
            while True:
                try:
                    stdout, stderr = process.communicate(timeout=0.2)
                    break
                except subprocess.TimeoutExpired:
                    if self.processing_cancel_event.is_set():
                        process.terminate()
            result = subprocess.CompletedProcess(cmd, process.returncode, stdout, stderr)
        finally:
            with self.processing_lock:
                if self.processing_process is process:
                    self.processing_process = None

        if self.processing_cancel_event.is_set():
            if os.path.exists(temp_output):
                os.remove(temp_output)
            raise ProcessingCancelled()
        if result.returncode != 0:
            if os.path.exists(temp_output):
                os.remove(temp_output)
            raise RuntimeError(f"FFmpegの処理に失敗しました: {result.stderr}")

        try:
            os.replace(temp_output, output_path)
        except OSError:
            if os.path.exists(temp_output):
                os.remove(temp_output)
            raise
        return output_path

    def start_stream_preview(self, input_path, duration=10, target_i=-14.0, target_tp=-1.0, target_lra=11.0):
        """
        プレビュー用：事前スキャンなしのシングルパス（ダイナミック）でメモリ上へ即座にストリーミング再生
        """
        self.stop_stream_preview()

        # プレビューは待機時間を無くすためシングルパスフィルターを使用
        af_filter = f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}"

        cmd = [
            self.ffmpeg_manager.ffmpeg_path,
            "-nostdin",
            "-i", input_path,
            "-ss", "0",
            "-t", str(duration),
            "-map", "0:a:0",
            "-af", af_filter,
            "-f", "s16le",
            "-acodec", "pcm_s16le",
            "-ac", "2",
            "-ar", "44100",
            "-"
        ]

        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, startupinfo=startupinfo)
        stop_event = threading.Event()
        self.stream_process = process
        self.preview_stop_event = stop_event

        def stream_worker():
            sample_rate = 44100
            channels = 2
            bytes_per_sample = 2
            chunk_size = 4096 * channels * bytes_per_sample
            audio_stream = None

            try:
                audio_stream = sd.OutputStream(samplerate=sample_rate, channels=channels, dtype='int16')
                self.audio_stream = audio_stream
                audio_stream.start()

                while not stop_event.is_set() and process.poll() is None:
                    data = process.stdout.read(chunk_size)
                    if not data:
                        break
                    
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    if len(audio_data) > 0:
                        # ステレオ再生用にNumPy配列をシェイプ変換
                        frames = len(audio_data) // channels
                        audio_data = audio_data[:frames * channels].reshape(-1, channels)
                        audio_stream.write(audio_data)
            except Exception as e:
                print(f"Stream error: {e}")
            finally:
                if audio_stream:
                    try:
                        audio_stream.stop()
                        audio_stream.close()
                    except Exception:
                        pass
                try:
                    process.stdout.close()
                    process.wait(timeout=1)
                except Exception:
                    pass
                with self.preview_lock:
                    if self.stream_process is process:
                        self.stream_process = None
                    if self.preview_stop_event is stop_event:
                        self.preview_stop_event = None
                    if self.audio_stream is audio_stream:
                        self.audio_stream = None

        threading.Thread(target=stream_worker, daemon=True).start()

    def stop_stream_preview(self):
        """
        再生中のストリームおよびFFmpegプロセスを安全に停止・破棄する
        """
        with self.preview_lock:
            process = self.stream_process
            stop_event = self.preview_stop_event
            self.stream_process = None
            self.preview_stop_event = None

        if stop_event:
            stop_event.set()

        if process:
            try:
                process.terminate()
                process.wait(timeout=1)
            except Exception:
                pass
