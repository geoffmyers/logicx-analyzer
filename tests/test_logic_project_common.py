"""Tests for scripts/logic_project_common.py, the module shared by
logic_project_analyzer.py, logic_project_analyzer_enhanced.py and
extract_track_names.py."""

import plistlib

import logic_project_common as common


class TestFormatKeySignature:
    def test_combines_key_and_mode(self):
        assert common.format_key_signature("F#", "minor") == "F# minor"

    def test_unknown_key(self):
        assert common.format_key_signature("Unknown", "major") == "Unknown"

    def test_unknown_mode(self):
        assert common.format_key_signature("C", "Unknown") == "Unknown"


class TestFormatTimeSignature:
    def test_formats_fraction(self):
        assert common.format_time_signature(4, 4) == "4/4"
        assert common.format_time_signature(7, 8) == "7/8"

    def test_zero_numerator_is_unknown(self):
        assert common.format_time_signature(0, 4) == "Unknown"

    def test_zero_denominator_is_unknown(self):
        assert common.format_time_signature(4, 0) == "Unknown"


class TestScanDirectory:
    def test_finds_logicx_dirs_only(self, tmp_path):
        (tmp_path / "Song A.logicx").mkdir()
        (tmp_path / "Song B.logicx").mkdir()
        (tmp_path / "not_a_project.txt").write_text("x")
        (tmp_path / "also.logicx.txt").write_text("x")  # not a real .logicx dir

        found = common.scan_directory(tmp_path)

        assert [p.name for p in found] == ["Song A.logicx", "Song B.logicx"]

    def test_ignores_logicx_that_is_a_file(self, tmp_path):
        (tmp_path / "NotADir.logicx").write_text("x")
        assert common.scan_directory(tmp_path) == []

    def test_sorted_by_name(self, tmp_path):
        for name in ("Zeta.logicx", "Alpha.logicx", "Mu.logicx"):
            (tmp_path / name).mkdir()
        found = common.scan_directory(tmp_path)
        assert [p.name for p in found] == ["Alpha.logicx", "Mu.logicx", "Zeta.logicx"]

    def test_empty_directory(self, tmp_path):
        assert common.scan_directory(tmp_path) == []


class TestExtractMetadataPlist:
    def test_reads_valid_plist(self, synthetic_bundle):
        metadata = common.extract_metadata_plist(synthetic_bundle)
        assert metadata is not None
        assert metadata["SongKey"] == "C"
        assert metadata["NumberOfTracks"] == 3

    def test_missing_file_returns_none(self, tmp_path):
        bundle = tmp_path / "Empty.logicx"
        bundle.mkdir()
        assert common.extract_metadata_plist(bundle) is None

    def test_malformed_plist_returns_none(self, tmp_path, capsys):
        bundle = tmp_path / "Broken.logicx"
        (bundle / "Alternatives" / "000").mkdir(parents=True)
        (bundle / common.METADATA_PATH).write_bytes(b"not a plist")

        assert common.extract_metadata_plist(bundle) is None
        # Malformed-but-present is InvalidFileException, never printed even
        # with verbose_errors=True (matches logic_project_analyzer.py).
        assert common.extract_metadata_plist(bundle, verbose_errors=True) is None
        assert capsys.readouterr().out == ""

    def test_verbose_errors_prints_on_other_exceptions(self, tmp_path, capsys):
        # A plist path that is a directory, not a file, raises IsADirectoryError
        # (not FileNotFoundError or InvalidFileException) on open().
        bundle = tmp_path / "Weird.logicx"
        (bundle / common.METADATA_PATH).mkdir(parents=True)

        assert common.extract_metadata_plist(bundle, verbose_errors=True) is None
        assert "Error reading" in capsys.readouterr().out

    def test_silent_by_default_on_other_exceptions(self, tmp_path, capsys):
        bundle = tmp_path / "Weird.logicx"
        (bundle / common.METADATA_PATH).mkdir(parents=True)

        assert common.extract_metadata_plist(bundle) is None
        assert capsys.readouterr().out == ""


class TestExtractProjectInfo:
    def test_reads_valid_plist(self, synthetic_bundle):
        info = common.extract_project_info(synthetic_bundle)
        assert info == {"LastSavedFrom": "11.1.0"}

    def test_missing_file_returns_none(self, tmp_path):
        bundle = tmp_path / "Empty.logicx"
        bundle.mkdir()
        assert common.extract_project_info(bundle) is None


class TestExtractStringsFromBinary:
    def test_extracts_ascii_runs(self, tmp_path):
        f = tmp_path / "blob.bin"
        f.write_bytes(b"\x00\x01Hello World\x02\x03Foo\x00Bar")
        strings = common.extract_strings_from_binary(f, min_length=4)
        assert "Hello World" in strings

    def test_respects_min_length(self, tmp_path):
        f = tmp_path / "blob.bin"
        f.write_bytes(b"\x00ab\x00abcd\x00")
        strings = common.extract_strings_from_binary(f, min_length=4)
        assert "ab" not in strings
        assert "abcd" in strings

    def test_missing_file_returns_empty_list(self, tmp_path):
        assert common.extract_strings_from_binary(tmp_path / "nope.bin") == []

    def test_verbose_errors_prints_on_failure(self, tmp_path, capsys):
        common.extract_strings_from_binary(tmp_path / "nope.bin", verbose_errors=True)
        assert "Error reading" in capsys.readouterr().out

    def test_silent_by_default_on_failure(self, tmp_path, capsys):
        common.extract_strings_from_binary(tmp_path / "nope.bin")
        assert capsys.readouterr().out == ""


class TestExtractCommonMetadataFields:
    def test_pulls_documented_fields(self):
        fields = common.extract_common_metadata_fields(
            {
                "BeatsPerMinute": 128,
                "SongKey": "D",
                "SongGenderKey": "minor",
                "SongSignatureNumerator": 3,
                "SongSignatureDenominator": 4,
                "NumberOfTracks": 5,
                "AudioFiles": ["a.wav", "b.wav"],
                "AlchemyFiles": ["c.alp"],
            }
        )
        assert fields["bpm"] == 128.0
        assert fields["key"] == "D"
        assert fields["mode"] == "minor"
        assert fields["time_sig_num"] == 3
        assert fields["time_sig_denom"] == 4
        assert fields["tracks"] == 5
        assert fields["audio_files"] == ["a.wav", "b.wav"]
        assert fields["alchemy_files"] == ["c.alp"]
        assert fields["total_samples"] == 3  # 2 audio + 1 alchemy
        assert fields["errors"] == []

    def test_invalid_bpm_type_is_flagged(self):
        fields = common.extract_common_metadata_fields({"BeatsPerMinute": "fast"})
        assert fields["bpm"] == 0
        assert "Invalid BPM format" in fields["errors"]

    def test_defaults_for_empty_metadata(self):
        fields = common.extract_common_metadata_fields({})
        assert fields["bpm"] == 0
        assert fields["key"] == "Unknown"
        assert fields["mode"] == "Unknown"
        assert fields["tracks"] == 0
        assert fields["audio_files"] == []
        assert fields["total_samples"] == 0
