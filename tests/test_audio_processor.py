import os
import subprocess
import tempfile
import unittest

from audio_processor import AudioProcessor, ProcessingCancelled


class AudioProcessorTests(unittest.TestCase):
    def create_test_wav(self, directory, duration="1"):
        source = os.path.join(directory, "input.wav")
        processor = AudioProcessor()
        subprocess.run(
            [
                processor.ffmpeg_manager.ffmpeg_path,
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                f"sine=frequency=440:duration={duration}",
                "-c:a",
                "pcm_s16le",
                "-y",
                source,
            ],
            check=True,
        )
        return source

    def test_bundled_ffmpeg_is_available(self):
        self.assertTrue(AudioProcessor().ffmpeg_manager.check_ffmpeg())

    def test_supported_output_formats(self):
        processor = AudioProcessor()
        with tempfile.TemporaryDirectory() as directory:
            source = self.create_test_wav(directory)
            for output_format in ("mp3", "m4a", "m4a_alac", "wav", "flac"):
                output = processor.process_file(
                    source,
                    directory,
                    output_format=output_format,
                )
                self.assertTrue(os.path.exists(output))
                expected_extension = ".m4a" if output_format == "m4a_alac" else f".{output_format}"
                self.assertEqual(os.path.splitext(output)[1], expected_extension)

            same_output = processor.process_file(source, directory, output_format="same")
            self.assertEqual(os.path.splitext(same_output)[1], ".wav")

    def test_cancelled_processing_stops_before_start(self):
        processor = AudioProcessor()
        processor.processing_cancel_event.set()
        with tempfile.TemporaryDirectory() as directory:
            source = self.create_test_wav(directory)
            with self.assertRaises(ProcessingCancelled):
                processor.process_file(source, directory)

    def test_no_rename_mode_uses_original_filename_in_output_directory(self):
        processor = AudioProcessor()
        with tempfile.TemporaryDirectory() as source_directory, tempfile.TemporaryDirectory() as output_directory:
            source = self.create_test_wav(source_directory)
            output = processor.process_file(
                source,
                output_directory,
                save_mode="replace",
                output_format="mp3",
            )
            self.assertEqual(os.path.basename(output), "input.mp3")
            self.assertTrue(os.path.exists(output))

    def test_short_tone_with_infinite_loudness_measurement(self):
        processor = AudioProcessor()
        with tempfile.TemporaryDirectory() as directory:
            source = self.create_test_wav(directory, duration="0.2")
            output = processor.process_file(source, directory)
            self.assertTrue(os.path.exists(output))

    def test_invalid_two_pass_measurement_falls_back_to_one_pass(self):
        self.assertFalse(AudioProcessor._can_use_two_pass_measurements({
            "input_i": 0.48,
            "input_tp": 10.17,
            "input_lra": 2.4,
            "input_thresh": -9.65,
            "target_offset": -0.31,
        }))


if __name__ == "__main__":
    unittest.main()
