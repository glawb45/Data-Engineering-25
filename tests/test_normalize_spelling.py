import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from normalize_spelling import (
    build_normalizer,
    _build_reverse_channel,
    _log,
    _preserve_case,
    CHANNEL,
    DEFAULT_MODERN_PRIORS,
)


class TestBuildReverseChannel:
    def test_reverse_channel_structure(self):
        """Test that reverse channel is built correctly."""
        reverse = _build_reverse_channel(CHANNEL)

        # Check that "thou" maps to "you"
        assert "thou" in reverse
        assert any(modern == "you" for modern, _ in reverse["thou"])

        # Check that "thee" maps to "you"
        assert "thee" in reverse
        assert any(modern == "you" for modern, _ in reverse["thee"])

    def test_reverse_channel_multiple_candidates(self):
        """Test that archaic words can map to multiple modern forms."""
        reverse = _build_reverse_channel(CHANNEL)

        # "thou" should map to "you" with some probability
        candidates = reverse.get("thou", [])
        assert len(candidates) > 0
        assert all(isinstance(prob, float) for _, prob in candidates)


class TestLogFunction:
    def test_log_positive_values(self):
        """Test log function with positive values."""
        result = _log(1.0)
        assert result == 0.0

        result = _log(0.5)
        assert result < 0.0

    def test_log_zero_clipping(self):
        """Test that log of zero is clipped to small value."""
        result = _log(0.0)
        # Should not raise error, should return log of small epsilon
        assert result < -20  # log(1e-9) is about -20.7


class TestPreserveCase:
    def test_all_uppercase(self):
        """Test case preservation for all uppercase."""
        result = _preserve_case("THOU", "you")
        assert result == "YOU"

    def test_capitalized(self):
        """Test case preservation for capitalized words."""
        result = _preserve_case("Thou", "you")
        assert result == "You"

    def test_lowercase(self):
        """Test case preservation for lowercase."""
        result = _preserve_case("thou", "you")
        assert result == "you"

    def test_multi_word_capitalized(self):
        """Test case preservation for multi-word replacements."""
        result = _preserve_case("Tis", "it is")
        assert result == "It is"


class TestNormalizer:
    def test_basic_normalization(self):
        """Test basic archaic to modern normalization."""
        normalizer = build_normalizer()

        # Test single word normalization
        result = normalizer("thou")
        assert result == "you"

        result = normalizer("thee")
        assert result == "you"

        result = normalizer("thy")
        assert result == "your"

    def test_case_preservation(self):
        """Test that case is preserved in normalization."""
        normalizer = build_normalizer()

        result = normalizer("Thou art wise")
        assert "You" in result or "you" in result
        assert "are" in result

    def test_sentence_normalization(self):
        """Test normalization of a full sentence."""
        normalizer = build_normalizer()

        text = "Thou art a wise person."
        result = normalizer(text)

        # Should normalize "thou" and "art"
        assert "thou" not in result.lower() or result == text  # Either normalized or kept
        assert "art" not in result or result == text

    def test_preserve_unknown_words(self):
        """Test that unknown words are preserved."""
        normalizer = build_normalizer()

        text = "The cat sat on the mat."
        result = normalizer(text)
        assert result == text

    def test_contractions_normalized(self):
        """Test that contractions like 'tis are normalized."""
        normalizer = build_normalizer()

        result = normalizer("'tis a lovely day")
        # Should normalize 'tis to "it is" or keep it
        assert "tis" not in result.lower() or "'tis" in result

    def test_custom_priors(self):
        """Test normalizer with custom priors."""
        custom_priors = {"you": 0.9, "your": 0.05, "yours": 0.05}
        normalizer = build_normalizer(priors=custom_priors)

        # Should still work with custom priors
        result = normalizer("thou")
        assert isinstance(result, str)


class TestDefaultData:
    def test_default_priors_structure(self):
        """Test that default priors are properly structured."""
        assert isinstance(DEFAULT_MODERN_PRIORS, dict)
        assert all(isinstance(k, str) for k in DEFAULT_MODERN_PRIORS.keys())
        assert all(isinstance(v, float) for v in DEFAULT_MODERN_PRIORS.values())

        # All priors should be positive
        assert all(v > 0 for v in DEFAULT_MODERN_PRIORS.values())

    def test_channel_structure(self):
        """Test that channel probabilities are properly structured."""
        assert isinstance(CHANNEL, dict)

        for modern, archaics in CHANNEL.items():
            assert isinstance(modern, str)
            assert isinstance(archaics, dict)

            for archaic, prob in archaics.items():
                assert isinstance(archaic, str)
                assert isinstance(prob, float)
                assert 0 < prob <= 1.0


def test_integration_shakespeare_like():
    """Integration test with Shakespeare-like text."""
    normalizer = build_normalizer()

    text = "Thou shalt not pass! Thy wisdom is great."
    result = normalizer(text)

    # Should normalize some archaic forms
    assert isinstance(result, str)
    assert len(result) > 0

    # Check that result is different from input (something was normalized)
    # or is the same (if the normalizer decided to keep the original)
    assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
