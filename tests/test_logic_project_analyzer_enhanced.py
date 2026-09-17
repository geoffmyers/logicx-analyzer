"""Tests for the binary ProjectData parsing in
scripts/logic_project_analyzer_enhanced.py: the chunk markers documented in
CLAUDE.md's "Key Chunk Types" table, the embedded-JSON preset extractor, the
track/region name heuristics, and the tempo-candidate scan. Every fixture is
a SYNTHETIC `.logicx` bundle built by conftest.py — never a real project.
"""

import json
import struct

import logic_project_analyzer_enhanced as enhanced
from conftest import build_project_data_bytes, write_logicx_bundle


class TestExtractJsonObjects:
    def test_extracts_single_preset(self):
        data = build_project_data_bytes()
        objs = enhanced.extract_json_objects(data)

        assert len(objs) == 1
        assert objs[0]["data"]["Preset"]["Name"] == "Sweet Memories"
        assert objs[0]["data"]["RegionType"] == "Type_AcousticPianoV2"

    def test_no_json_in_data(self):
        assert enhanced.extract_json_objects(b"no json here at all") == []

    def test_multiple_objects(self):
        obj_a = json.dumps({"a": 1}).encode()
        obj_b = json.dumps({"b": 2}).encode()
        # `limit = len(data) - 10`, so pad the tail well past the second
        # object's start or it falls outside the scan window.
        data = b"\x00\x00" + obj_a + b"\x00\x00\x00" + obj_b + b"\x00" * 15

        objs = enhanced.extract_json_objects(data)

        assert [o["data"] for o in objs] == [{"a": 1}, {"b": 2}]

    def test_string_containing_braces_does_not_break_parsing(self):
        # A JSON string value containing literal `{`/`}` must not be counted
        # as a brace by the depth tracker (it's inside `in_string`).
        obj = json.dumps({"note": "{not a nested object}"}).encode()
        objs = enhanced.extract_json_objects(b"junk" + obj + b"junk")

        assert len(objs) == 1
        assert objs[0]["data"]["note"] == "{not a nested object}"

    def test_unbalanced_candidate_does_not_hang_or_crash(self):
        # A `{"` start that never closes within the scan window: the
        # regression this function's docstring describes (quadratic
        # rescanning). This must return quickly and find nothing there.
        data = b'{"' + b"x" * 500 + b"unterminated"
        objs = enhanced.extract_json_objects(data)
        assert objs == []

    def test_many_false_starts_stay_fast(self):
        # Dense `{"` false starts, none of which ever balance: the exact
        # shape that went quadratic before the `i = j` fix. This should
        # complete near-instantly (bounded by wall-clock as a smoke check,
        # not an exact complexity proof).
        import time

        data = (b'{"x' * 20000) + b"tail"
        start = time.monotonic()
        objs = enhanced.extract_json_objects(data)
        elapsed = time.monotonic() - start

        assert objs == []
        assert elapsed < 5.0

    def test_real_preset_still_found_after_a_dense_false_start_region(self):
        # A real, well-formed object appearing after a run of false starts
        # must still be found — the skip-ahead must not eat past it.
        noise = b'{"x' * 50
        real = json.dumps({"ok": True}).encode()
        objs = enhanced.extract_json_objects(noise + real)
        assert [o["data"] for o in objs] == [{"ok": True}]


class TestCountChunkMarkers:
    def test_counts_known_markers(self, synthetic_bundle):
        counts = enhanced.count_chunk_markers(synthetic_bundle)
        # build_project_data_bytes() embeds two 'karT' and one 'gRuA'.
        assert counts["Track"] == 2
        assert counts["AudioRegion"] == 1

    def test_omits_markers_with_zero_count(self, synthetic_bundle):
        counts = enhanced.count_chunk_markers(synthetic_bundle)
        assert "CoreMIDI" not in counts  # b'MroC' never appears in the fixture

    def test_missing_project_data_returns_empty(self, tmp_path):
        bundle = tmp_path / "Empty.logicx"
        bundle.mkdir()
        assert enhanced.count_chunk_markers(bundle) == {}


class TestExtractTempoData:
    def test_finds_tempo_in_accepted_range(self, synthetic_bundle):
        tempos = enhanced.extract_tempo_data(synthetic_bundle)
        assert 120.5 in tempos

    def test_rejects_values_outside_40_240(self, tmp_path):
        bundle = write_logicx_bundle(
            tmp_path,
            name="OutOfRange.logicx",
            project_data=struct.pack(">f", 500.0) + struct.pack(">f", 10.0),
        )
        assert enhanced.extract_tempo_data(bundle) == []

    def test_missing_project_data_returns_empty(self, tmp_path):
        bundle = tmp_path / "Empty.logicx"
        bundle.mkdir()
        assert enhanced.extract_tempo_data(bundle) == []

    def test_caps_at_ten_candidates(self, tmp_path):
        blob = b"".join(struct.pack(">f", 60.0 + i) for i in range(20))
        bundle = write_logicx_bundle(tmp_path, name="Many.logicx", project_data=blob)
        tempos = enhanced.extract_tempo_data(bundle)
        assert len(tempos) == 10


class TestIsValidName:
    def test_rejects_too_short(self):
        assert enhanced.is_valid_name("ab") is False

    def test_rejects_chunk_markers_themselves(self):
        assert enhanced.is_valid_name("karT") is False
        assert enhanced.is_valid_name("gRuA") is False

    def test_rejects_reserved_prefix(self):
        assert enhanced.is_valid_name("reserved123") is False

    def test_accepts_plausible_track_name(self):
        assert enhanced.is_valid_name("Lead Vocal") is True

    def test_rejects_low_alpha_ratio(self):
        assert enhanced.is_valid_name("12345678") is False

    def test_rejects_excessive_special_characters(self):
        assert enhanced.is_valid_name("a!@#$%^&*b") is False

    def test_rejects_no_vowel_short_strings(self):
        assert enhanced.is_valid_name("bcdfghj") is False


class TestExtractTrackNames:
    def test_finds_track_and_region_names(self, synthetic_bundle):
        tracks, regions = enhanced.extract_track_names(synthetic_bundle)
        assert "Lead Vocal" in tracks
        assert "Verse 1 Region" in regions

    def test_finds_generic_audio_n_pattern(self, synthetic_bundle):
        tracks, _ = enhanced.extract_track_names(synthetic_bundle)
        assert "Audio 2" in tracks

    def test_missing_project_data_returns_empty_lists(self, tmp_path):
        bundle = tmp_path / "Empty.logicx"
        bundle.mkdir()
        assert enhanced.extract_track_names(bundle) == ([], [])

    def test_deduplicates(self, tmp_path):
        # Two 'karT' markers, both followed by the same track name. NUL
        # separators keep each marker/name as its own extracted string
        # (extract_strings_from_binary merges adjacent printable runs).
        data = b"karT\x00Lead Vocal\x00karT\x00Lead Vocal\x00"
        bundle = write_logicx_bundle(tmp_path, name="Dup.logicx", project_data=data)
        tracks, _ = enhanced.extract_track_names(bundle)
        assert tracks.count("Lead Vocal") == 1


class TestExtractPluginData:
    def test_extracts_alchemy_reference(self, synthetic_bundle):
        result = enhanced.extract_plugin_data(synthetic_bundle)
        assert any("Alchemy/Libraries" in ref for ref in result["alchemy_references"])

    def test_extracts_preset_from_embedded_json(self, synthetic_bundle):
        result = enhanced.extract_plugin_data(synthetic_bundle)
        assert len(result["presets"]) == 1
        assert result["presets"][0]["name"] == "Sweet Memories"
        assert result["presets"][0]["character"] == "Acoustic Piano - Strummed"

    def test_missing_project_data_returns_empty_structure(self, tmp_path):
        bundle = tmp_path / "Empty.logicx"
        bundle.mkdir()
        result = enhanced.extract_plugin_data(bundle)
        assert result == {"plugins": [], "presets": [], "alchemy_references": []}


class TestParseProjectData:
    def test_integrates_metadata_and_binary_data(self, synthetic_bundle):
        metadata = enhanced.extract_metadata_plist(synthetic_bundle)
        proj_info = enhanced.extract_project_info(synthetic_bundle)

        result = enhanced.parse_project_data(metadata, proj_info, synthetic_bundle)

        assert result["name"] == synthetic_bundle.stem
        assert result["musical"]["key"] == "C"
        assert result["musical"]["mode"] == "major"
        assert result["musical"]["time_signature"] == "4/4"
        assert 120.5 in result["musical"]["tempo_candidates"]
        assert result["technical"]["logic_version"] == "11.1.0"
        assert result["technical"]["tracks"] == 3
        assert "Lead Vocal" in result["track_info"]["track_names"]
        assert result["plugin_data"]["preset_count"] == 1
        assert result["binary_data"]["chunk_counts"]["Track"] == 2
        assert result["binary_data"]["total_chunks"] > 0
        assert result["errors"] == []
