import unittest

from settings import validate_settings


class SettingsValidationTests(unittest.TestCase):
    def test_invalid_values_are_replaced_with_defaults(self):
        settings = validate_settings({
            "target_loudness": "invalid",
            "target_true_peak": 99,
            "preview_duration": 999,
            "output_format": "ogg",
            "file_list_font_size": 30,
        })

        self.assertEqual(settings["target_loudness"], -14.0)
        self.assertEqual(settings["target_true_peak"], -1.0)
        self.assertEqual(settings["preview_duration"], 10)
        self.assertEqual(settings["output_format"], "same")
        self.assertEqual(settings["file_list_font_size"], 10)

    def test_valid_values_are_preserved(self):
        settings = validate_settings({
            "target_loudness": -18,
            "target_true_peak": -2,
            "preview_duration": 30,
            "output_format": "m4a",
            "file_list_font_size": 25,
        })

        self.assertEqual(settings["target_loudness"], -18.0)
        self.assertEqual(settings["target_true_peak"], -2.0)
        self.assertEqual(settings["preview_duration"], 30)
        self.assertEqual(settings["output_format"], "m4a")
        self.assertEqual(settings["file_list_font_size"], 25)

    def test_same_input_format_is_preserved(self):
        settings = validate_settings({"output_format": "same"})
        self.assertEqual(settings["output_format"], "same")

    def test_alac_output_format_is_preserved(self):
        settings = validate_settings({"output_format": "m4a_alac"})
        self.assertEqual(settings["output_format"], "m4a_alac")

    def test_audio_bitrate_is_shared_between_mp3_and_m4a(self):
        settings = validate_settings({"audio_bitrate": 256})
        self.assertEqual(settings["audio_bitrate"], 256)

    def test_legacy_bitrate_settings_are_migrated(self):
        settings = validate_settings({"mp3_bitrate": 192, "m4a_bitrate": 256})
        self.assertEqual(settings["audio_bitrate"], 192)


if __name__ == "__main__":
    unittest.main()
