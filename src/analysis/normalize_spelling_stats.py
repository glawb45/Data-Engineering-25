"""
Statistical Analysis for normalize_spelling.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to path BEFORE importing
src_path = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(src_path))

# Patch the normalize_spelling module to work with Python 3.9
normalize_spelling_path = src_path / "normalize_spelling.py"
if normalize_spelling_path.exists():
    content = normalize_spelling_path.read_text()

    if "from __future__ import annotations" not in content:
        import importlib.util

        patched_content = "from __future__ import annotations\n" + content

        spec = importlib.util.spec_from_loader("normalize_spelling", loader=None)
        module = importlib.util.module_from_spec(spec)

        exec(patched_content, module.__dict__)
        sys.modules["normalize_spelling"] = module

        print("Successfully patched normalize_spelling for Python 3.9 compatibility\n")

from collections import Counter
from typing import Dict, List, Any
import json
import time
import re

from normalize_spelling import (
    DEFAULT_MODERN_PRIORS,
    CHANNEL,
    _build_reverse_channel,
    build_normalizer,
)


class NormalizerStatisticalAnalysis:
    """Statistical analysis beyond basic unit tests."""

    def __init__(self):
        self.normalizer = build_normalizer()
        self.reverse_channel = _build_reverse_channel(CHANNEL)
        self.results = {}

    def analyze_prior_distribution_detailed(self) -> Dict[str, Any]:
        """Deep analysis of prior distribution."""
        print("\n" + "=" * 80)
        print("PRIOR DISTRIBUTION - DETAILED ANALYSIS")
        print("=" * 80)

        priors_list = list(DEFAULT_MODERN_PRIORS.items())
        sorted_priors = sorted(priors_list, key=lambda x: x[1], reverse=True)

        total_mass = sum(DEFAULT_MODERN_PRIORS.values())
        mean_prior = total_mass / len(DEFAULT_MODERN_PRIORS)
        variance = sum((p - mean_prior) ** 2 for _, p in priors_list) / len(priors_list)
        std_dev = variance**0.5

        import math

        entropy = -sum(p * math.log(p) for p in DEFAULT_MODERN_PRIORS.values())

        top_5_mass = sum(p for _, p in sorted_priors[:5])
        top_10_mass = sum(p for _, p in sorted_priors[:10])

        prob_ranges = {
            "high (>0.08)": sum(1 for _, p in priors_list if p > 0.08),
            "medium (0.04-0.08)": sum(1 for _, p in priors_list if 0.04 <= p <= 0.08),
            "low (<0.04)": sum(1 for _, p in priors_list if p < 0.04),
        }

        stats = {
            "total_words": len(DEFAULT_MODERN_PRIORS),
            "total_mass": total_mass,
            "mean": mean_prior,
            "std_dev": std_dev,
            "variance": variance,
            "entropy": entropy,
            "top_5_mass": top_5_mass,
            "top_10_mass": top_10_mass,
            "concentration_ratio": top_10_mass / total_mass,
            "probability_ranges": prob_ranges,
            "top_10_words": dict(sorted_priors[:10]),
        }

        print(f"Total Words: {stats['total_words']}")
        print(f"Total Mass: {stats['total_mass']:.4f}")
        print(f"Mean Prior: {stats['mean']:.4f}")
        print(f"Std Dev: {stats['std_dev']:.4f}")
        print(f"Entropy: {stats['entropy']:.4f} nats")
        print(
            f"Top 10 Mass: {stats['top_10_mass']:.4f} ({stats['top_10_mass']/total_mass:.1%})"
        )

        print("\nTop 10 Most Likely Words:")
        for i, (word, prob) in enumerate(sorted_priors[:10], 1):
            print(f"  {i:2d}. '{word}': {prob:.4f}")

        return stats

    def analyze_channel_structure_detailed(self) -> Dict[str, Any]:
        """Deep analysis of channel probabilities."""
        print("\n" + "=" * 80)
        print("CHANNEL STRUCTURE - DETAILED ANALYSIS")
        print("=" * 80)

        total_modern = len(CHANNEL)
        total_archaic = sum(len(archaics) for archaics in CHANNEL.values())

        archaics_per_modern = [len(archaics) for archaics in CHANNEL.values()]
        avg_archaics = sum(archaics_per_modern) / len(archaics_per_modern)

        multi_archaic_words = {
            modern: archaics
            for modern, archaics in CHANNEL.items()
            if len(archaics) > 1
        }

        all_channel_probs = [
            prob for archaics in CHANNEL.values() for prob in archaics.values()
        ]
        avg_channel_prob = sum(all_channel_probs) / len(all_channel_probs)
        high_conf_count = sum(1 for p in all_channel_probs if p > 0.9)

        stats = {
            "total_modern_words": total_modern,
            "total_archaic_forms": total_archaic,
            "avg_archaics_per_modern": avg_archaics,
            "words_with_multiple_archaics": len(multi_archaic_words),
            "avg_channel_probability": avg_channel_prob,
            "high_confidence_channels": high_conf_count,
            "high_confidence_ratio": high_conf_count / len(all_channel_probs),
        }

        print(f"Modern Words: {stats['total_modern_words']}")
        print(f"Archaic Forms: {stats['total_archaic_forms']}")
        print(f"Avg Archaic Forms per Modern: {stats['avg_archaics_per_modern']:.2f}")
        print(f"Avg Channel Probability: {stats['avg_channel_probability']:.4f}")
        print(f"High Confidence (>0.9): {stats['high_confidence_ratio']:.1%}")

        return stats

    def analyze_normalization_patterns(self, num_samples: int = 100) -> Dict[str, Any]:
        """Analyze actual normalization behavior with proper word extraction."""
        print("\n" + "=" * 80)
        print("NORMALIZATION PATTERNS - BEHAVIORAL ANALYSIS")
        print("=" * 80)

        sample_texts = self._generate_sample_texts(num_samples)

        word_changes = Counter()
        texts_modified = 0
        total_words = 0
        total_changes = 0
        processing_times = []

        # Use regex pattern from normalize_spelling to match words properly
        WORD_PATTERN = re.compile(r"\b[\w']+\b")

        for text in sample_texts:
            start = time.perf_counter()
            normalized = self.normalizer(text)
            elapsed = time.perf_counter() - start
            processing_times.append(elapsed)

            if text != normalized:
                texts_modified += 1

            # Extract words using the same pattern as the normalizer
            orig_words = WORD_PATTERN.findall(text)
            norm_words = WORD_PATTERN.findall(normalized)

            total_words += len(orig_words)

            # Only compare if same number of words (should be with this normalizer)
            if len(orig_words) == len(norm_words):
                for orig, norm in zip(orig_words, norm_words):
                    if orig.lower() != norm.lower():
                        total_changes += 1
                        # Use string key for JSON compatibility
                        key = f"{orig.lower()} → {norm.lower()}"
                        word_changes[key] += 1

        avg_time = sum(processing_times) / len(processing_times)
        total_chars = sum(len(t) for t in sample_texts)
        throughput = (
            total_chars / sum(processing_times) if sum(processing_times) > 0 else 0
        )

        # Convert Counter to dict with proper format for JSON
        top_transformations = {}
        for key, count in word_changes.most_common(20):
            top_transformations[key] = count

        stats = {
            "texts_analyzed": num_samples,
            "texts_modified": texts_modified,
            "modification_rate": texts_modified / num_samples,
            "total_words_processed": total_words,
            "total_word_changes": total_changes,
            "word_change_rate": total_changes / total_words if total_words > 0 else 0,
            "top_20_transformations": top_transformations,
            "avg_processing_time_ms": avg_time * 1000,
            "throughput_chars_per_sec": throughput,
        }

        print(
            f"Texts Modified: {stats['texts_modified']}/{num_samples} ({stats['modification_rate']:.1%})"
        )
        print(f"Total Words: {stats['total_words_processed']}")
        print(f"Words Changed: {stats['total_word_changes']}")
        print(f"Word Change Rate: {stats['word_change_rate']:.2%}")
        print(f"Throughput: {stats['throughput_chars_per_sec']:,.0f} chars/sec")

        print("\nTop 10 Transformations:")
        for i, (transformation, count) in enumerate(
            list(top_transformations.items())[:10], 1
        ):
            print(f"  {i:2d}. {transformation}: {count} times")

        return stats

    def analyze_idempotence(self) -> Dict[str, Any]:
        """Test idempotence property."""
        print("\n" + "=" * 80)
        print("IDEMPOTENCE ANALYSIS")
        print("=" * 80)

        test_cases = [
            "Thou art wise.",
            "'Tis a fine day.",
            "The cat sat on the mat.",
            "Methinks thou dost protest.",
        ]

        idempotent_count = 0

        for text in test_cases:
            once = self.normalizer(text)
            twice = self.normalizer(once)

            if once == twice:
                idempotent_count += 1

        stats = {
            "total_tested": len(test_cases),
            "idempotent": idempotent_count,
            "idempotence_rate": idempotent_count / len(test_cases),
        }

        print(
            f"Idempotent: {idempotent_count}/{len(test_cases)} ({stats['idempotence_rate']:.1%})"
        )

        return stats

    def analyze_coverage_gaps(self) -> Dict[str, Any]:
        """Analyze coverage gaps."""
        print("\n" + "=" * 80)
        print("COVERAGE ANALYSIS")
        print("=" * 80)

        # High prior words without archaic forms
        high_prior_words = [w for w, p in DEFAULT_MODERN_PRIORS.items() if p > 0.05]

        coverage_gaps = []
        for word in high_prior_words:
            if word not in CHANNEL:
                coverage_gaps.append(word)

        stats = {
            "high_prior_words": len(high_prior_words),
            "coverage_gaps": len(coverage_gaps),
            "gap_examples": coverage_gaps[:5],
        }

        print(f"High Prior Words (>0.05): {len(high_prior_words)}")
        print(f"Coverage Gaps: {len(coverage_gaps)}")
        if coverage_gaps:
            print(f"Examples: {', '.join(coverage_gaps[:5])}")

        return stats

    def _generate_sample_texts(self, count: int) -> List[str]:
        """Generate sample texts."""
        base_texts = [
            "Thou art a wise person.",
            "Thee and thy friends are welcome.",
            "'Tis a beautiful day, is it not?",
            "Methinks thou dost protest too much.",
            "Whither art thou going?",
            "I shall go hence anon.",
            "Hast thou seen the way thither?",
            "Ne'er have I seen such beauty ere this day.",
            "Wherefore dost thou weep?",
            "Prithee, tell me what troubles thee.",
            "Thou shalt not pass!",
            "Thy sword is mighty indeed.",
            "Thine eyes are like the stars.",
            "Dost thou know the way?",
            "Hither came a stranger yester eve.",
            "'Twas a dark and stormy night.",
            "O'er the hills and far away.",
            "E'en the bravest knight may falter.",
            "Aye, 'tis true what they say.",
            "Nay, I shall not go.",
        ]
        multiplier = (count // len(base_texts)) + 1
        return (base_texts * multiplier)[:count]

    def generate_comprehensive_report(self):
        """Generate comprehensive report."""
        print("\n╔" + "═" * 78 + "╗")
        print("║" + " " * 15 + "STATISTICAL ANALYSIS REPORT" + " " * 36 + "║")
        print("╚" + "═" * 78 + "╝")

        self.results["priors"] = self.analyze_prior_distribution_detailed()
        self.results["channel"] = self.analyze_channel_structure_detailed()
        self.results["patterns"] = self.analyze_normalization_patterns(100)
        self.results["idempotence"] = self.analyze_idempotence()
        self.results["coverage"] = self.analyze_coverage_gaps()

        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("\nAnalysis Complete!")
        print("\nKey Findings:")
        print(f"  • Prior entropy: {self.results['priors']['entropy']:.2f} nats")
        print(f"  • Archaic forms: {self.results['channel']['total_archaic_forms']}")
        print(
            f"  • High confidence channels: {self.results['channel']['high_confidence_ratio']:.1%}"
        )
        print(
            f"  • Modification rate: {self.results['patterns']['modification_rate']:.1%}"
        )
        print(
            f"  • Word change rate: {self.results['patterns']['word_change_rate']:.2%}"
        )
        print(f"  • Idempotence: {self.results['idempotence']['idempotence_rate']:.1%}")
        print(
            f"  • Throughput: {self.results['patterns']['throughput_chars_per_sec']:,.0f} chars/sec"
        )

        # Save to JSON (all keys are now JSON-compatible)
        output_path = Path(__file__).parent / "normalization_stats.json"
        try:
            with open(output_path, "w") as f:
                json.dump(self.results, f, indent=2, default=str)
            print("\n Saved to: normalization_stats.json")
        except Exception as e:
            print(f"\n⚠ Could not save JSON: {e}")
            # Try saving as text instead
            with open(output_path, "w") as f:
                f.write("STATISTICAL ANALYSIS RESULTS\n")
                f.write("=" * 80 + "\n\n")
                for section, data in self.results.items():
                    f.write(f"\n{section.upper()}\n")
                    f.write("-" * 80 + "\n")
                    f.write(str(data) + "\n")
            print("Saved to: normalization_stats.txt instead")

        print()


if __name__ == "__main__":
    analyzer = NormalizerStatisticalAnalysis()
    analyzer.generate_comprehensive_report()
