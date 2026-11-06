import json
import math
import os
from pathlib import Path

def get_app_data_dir():
    app_data = os.environ.get("APPDATA")
    base_dir = Path(app_data) if app_data else Path.home() / "AppData" / "Roaming"
    app_dir = base_dir / "MP3Normalizer"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


SETTINGS_FILE = get_app_data_dir() / "settings.json"
LEGACY_SETTINGS_FILE = Path(__file__).resolve().parent / "settings.json"

DEFAULT_SETTINGS = {
    "target_loudness": -14.0,
    "target_true_peak": -1.0,
    "output_dir": "",
    "preview_duration": 10,         # プレビュー秒数（デフォルト10秒）
    "appearance_mode": "System",    # "System", "Dark", "Light"
    "color_theme": "blue",          # "blue", "green", "dark-blue"
    "save_mode": "copy",             # "copy" (別名保存) または "replace" (ファイル名変更なし)
    "output_format": "same",          # "same", "mp3", "m4a", "m4a_alac", "wav", "flac"
    "file_list_font_size": 10,         # ファイル一覧のフォントサイズ（pt）
    "audio_bitrate": 320,
    "flac_compression": 5
}

def validate_settings(settings):
    if not isinstance(settings, dict):
        return DEFAULT_SETTINGS.copy()

    validated = DEFAULT_SETTINGS.copy()

    try:
        loudness = float(settings.get("target_loudness", validated["target_loudness"]))
        if math.isfinite(loudness) and -60.0 <= loudness <= 0.0:
            validated["target_loudness"] = loudness
    except (TypeError, ValueError):
        pass

    try:
        true_peak = float(settings.get("target_true_peak", validated["target_true_peak"]))
        if math.isfinite(true_peak) and -20.0 <= true_peak <= 0.0:
            validated["target_true_peak"] = true_peak
    except (TypeError, ValueError):
        pass

    preview_duration = settings.get("preview_duration", validated["preview_duration"])
    if preview_duration in {5, 10, 15, 30}:
        validated["preview_duration"] = preview_duration

    if settings.get("appearance_mode") in {"System", "Dark", "Light"}:
        validated["appearance_mode"] = settings["appearance_mode"]
    if settings.get("save_mode") in {"copy", "replace"}:
        validated["save_mode"] = settings["save_mode"]
    if settings.get("output_format") in {"same", "mp3", "m4a", "m4a_alac", "wav", "flac"}:
        validated["output_format"] = settings["output_format"]
    if settings.get("file_list_font_size") in {5, 10, 15, 20, 25}:
        validated["file_list_font_size"] = settings["file_list_font_size"]
    audio_bitrate = settings.get("audio_bitrate")
    if audio_bitrate not in {128, 192, 256, 320}:
        audio_bitrate = settings.get("mp3_bitrate", settings.get("m4a_bitrate"))
    if audio_bitrate in {128, 192, 256, 320}:
        validated["audio_bitrate"] = audio_bitrate
    if settings.get("flac_compression") in set(range(9)):
        validated["flac_compression"] = settings["flac_compression"]

    if isinstance(settings.get("output_dir"), str):
        validated["output_dir"] = settings["output_dir"]
    return validated

def load_settings():
    settings_file = SETTINGS_FILE if SETTINGS_FILE.exists() else LEGACY_SETTINGS_FILE
    if settings_file.exists():
        try:
            with settings_file.open("r", encoding="utf-8") as f:
                raw_settings = json.load(f)
                settings = validate_settings(raw_settings)
                if settings_file == LEGACY_SETTINGS_FILE or settings != raw_settings:
                    save_settings(settings)
                return settings
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    try:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with SETTINGS_FILE.open("w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
    except Exception:
        pass
