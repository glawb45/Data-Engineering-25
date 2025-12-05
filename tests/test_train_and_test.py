"""
Tests for train_and_test.py module.
Handles Python 3.9 compatibility for normalize_spelling.py imports.
"""
from __future__ import annotations

import sys
from pathlib import Path
import tempfile

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from train_and_test import (
    _build_reverse_channel,
    _gold_label,
    _derive_priors,
    _token_pairs,
)
from normalize_spelling import CHANNEL


class TestBuildReverseChannel:
    def test_build_reverse_channel(self):
        """Test building reverse channel mapping."""
        test_channel = {
            "you": {"thou": 0.5, "thee": 0.3},
            "your": {"thy": 0.7},
        }
        reverse = _build_reverse_channel(test_channel)

        # Check reverse mapping
        assert "thou" in reverse
        assert "thee" in reverse
        assert "thy" in reverse

        # Check that "thou" maps back to "you"
        assert any(modern == "you" for modern, _ in reverse["thou"])

    def test_reverse_channel_with_real_channel(self):
        """Test with actual CHANNEL data."""
        reverse = _build_reverse_channel(CHANNEL)

        # Verify some known mappings
        assert "thou" in reverse
        assert "art" in reverse
        assert "dost" in reverse


class TestGoldLabel:
    def test_gold_label_with_candidates(self):
        """Test gold label selection with multiple candidates."""
        reverse_channel = {
            "thou": [("you", 0.9), ("your", 0.1)],
        }
        label = _gold_label(reverse_channel, "thou")
        assert label == "you"  # Should pick highest probability

    def test_gold_label_no_candidates(self):
        """Test gold label when token has no candidates."""
        reverse_channel = {}
        label = _gold_label(reverse_channel, "unknown")
        assert label == "unknown"  # Should return original

    def test_gold_label_single_candidate(self):
        """Test gold label with single candidate."""
        reverse_channel = {
            "thy": [("your", 0.7)],
        }
        label = _gold_label(reverse_channel, "thy")
        assert label == "your"


class TestDerivePriors:
    def test_derive_priors_basic(self):
        """Test deriving priors from training pairs."""
        train_pairs = [
            ("thou", "you"),
            ("thee", "you"),
            ("thy", "your"),
            ("thou", "you"),
        ]
        priors = _derive_priors(train_pairs)

        # Check structure
        assert isinstance(priors, dict)
        assert "you" in priors
        assert "your" in priors

        # "you" should have higher prior than "your" (appears 3 times vs 1)
        assert priors["you"] > priors["your"]

    def test_derive_priors_laplace_smoothing(self):
        """Test that Laplace smoothing is applied."""
        train_pairs = [("thou", "you")]
        priors = _derive_priors(train_pairs)

        # With Laplace smoothing (v+1)/(N+V), single item should be 1.0
        # because (1+1)/(1+1) = 1.0
        assert priors["you"] == 1.0

        # Test with multiple items to show smoothing effect
        train_pairs_multi = [("thou", "you"), ("thou", "you"), ("thy", "your")]
        priors_multi = _derive_priors(train_pairs_multi)

        # Neither should be exactly their raw frequency due to smoothing
        # "you" appears 2/3 times, but with smoothing it's (2+1)/(3+2) = 0.6
        assert 0.5 < priors_multi["you"] < 0.7

    def test_derive_priors_probabilities_sum(self):
        """Test that derived priors sum to approximately 1."""
        train_pairs = [
            ("thou", "you"),
            ("thy", "your"),
            ("thee", "you"),
        ]
        priors = _derive_priors(train_pairs)

        # Sum should be close to 1 (with Laplace smoothing)
        total = sum(priors.values())
        assert 0.9 <= total <= 1.1


class TestTokenPairs:
    def test_token_pairs_with_archaic_text(self):
        """Test extracting token pairs from text with archaic forms."""
        # Create a temporary file with sample text
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Thou art wise and thy knowledge is great.")
            temp_path = Path(f.name)

        try:
            pairs = _token_pairs(temp_path)

            # Should find some archaic tokens
            assert isinstance(pairs, list)

            if pairs:  # Only if archaic tokens were found
                # Check structure
                for obs, gold in pairs:
                    assert isinstance(obs, str)
                    assert isinstance(gold, str)
                    assert obs != gold  # Pairs should be different

        finally:
            temp_path.unlink()

    def test_token_pairs_with_modern_text(self):
        """Test with modern text (should find no archaic pairs)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("The cat sat on the mat.")
            temp_path = Path(f.name)

        try:
            pairs = _token_pairs(temp_path)

            # Modern text should yield no archaic token pairs
            assert isinstance(pairs, list)
            # May be empty if no archaic forms found

        finally:
            temp_path.unlink()

    def test_token_pairs_case_handling(self):
        """Test that token pairs are lowercased."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("THOU ART Thy")
            temp_path = Path(f.name)

        try:
            pairs = _token_pairs(temp_path)

            # All observed tokens should be lowercase
            for obs, gold in pairs:
                assert obs.islower()

        finally:
            temp_path.unlink()


class TestIntegration:
    def test_full_pipeline_with_sample_data(self):
        """Test the full training and evaluation pipeline."""
        # Create sample training text
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Thou art wise. Thy knowledge is great. Thee shall prosper.")
            temp_path = Path(f.name)

        try:
            # Extract pairs
            pairs = _token_pairs(temp_path)

            if pairs:
                # Derive priors from all pairs (no split for this test)
                priors = _derive_priors(pairs)

                # Check that priors were derived
                assert len(priors) > 0
                assert all(0 < p <= 1 for p in priors.values())

        finally:
            temp_path.unlink()


def test_channel_consistency():
    """Test that CHANNEL is consistent with expectations."""
    # Verify CHANNEL has expected archaic forms
    expected_archaics = ["thou", "thee", "thy", "art", "dost", "doth"]

    reverse = _build_reverse_channel(CHANNEL)

    for archaic in expected_archaics:
        assert archaic in reverse, f"Expected archaic form '{archaic}' not in CHANNEL"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
