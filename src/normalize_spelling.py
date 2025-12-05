import argparse
import math
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

# Noisy-channel ingredients:
# - Prior over modern forms (P(modern))
# - Channel probabilities (P(archaic | modern))
DEFAULT_MODERN_PRIORS: Dict[str, float] = {
    "you": 0.12,
    "your": 0.06,
    "yours": 0.02,
    "are": 0.08,
    "have": 0.07,
    "had": 0.05,
    "do": 0.08,
    "does": 0.05,
    "shall": 0.02,
    "will": 0.08,
    "were": 0.06,
    "would": 0.05,
    "could": 0.05,
    "should": 0.05,
    "may": 0.04,
    "can": 0.04,
    "it is": 0.05,
    "it was": 0.05,
    "it will": 0.03,
    "it were": 0.02,
    "over": 0.01,
    "even": 0.02,
    "ever": 0.02,
    "never": 0.02,
    "often": 0.02,
    "yes": 0.02,
    "no": 0.02,
    "please": 0.01,
    "I think": 0.01,
    "why": 0.02,
    "from where": 0.01,
    "from here": 0.01,
    "here": 0.02,
    "there": 0.02,
    "where": 0.02,
    "soon": 0.01,
    "before": 0.02,
    "anything": 0.01,
    "nothing": 0.01,
    "that": 0.03,
    "over there": 0.01,
    "sir": 0.01,
}

CHANNEL: Dict[str, Dict[str, float]] = {
    "you": {"thou": 0.45, "thee": 0.35, "ye": 0.2},
    "your": {"thy": 0.7},
    "yours": {"thine": 0.8},
    "are": {"art": 0.9},
    "have": {"hast": 0.9},
    "had": {"hadst": 0.9},
    "do": {"dost": 0.9},
    "does": {"doth": 0.9},
    "shall": {"shalt": 0.95},
    "will": {"wilt": 0.9},
    "were": {"wert": 0.9},
    "would": {"wouldst": 0.9},
    "could": {"couldst": 0.9},
    "should": {"shouldst": 0.9},
    "may": {"mayst": 0.9},
    "can": {"canst": 0.9},
    "it is": {"tis": 0.95},
    "it was": {"twas": 0.95},
    "it will": {"twill": 0.9},
    "it were": {"twere": 0.9},
    "over": {"o'er": 0.9},
    "even": {"e'en": 0.9},
    "ever": {"e'er": 0.9},
    "never": {"ne'er": 0.9},
    "often": {"oft": 0.8},
    "yes": {"aye": 0.9},
    "no": {"nay": 0.9},
    "please": {"prithee": 0.9},
    "I think": {"methinks": 0.9},
    "why": {"wherefore": 0.7},
    "from where": {"whence": 0.7},
    "from here": {"hence": 0.7},
    "here": {"hither": 0.7},
    "there": {"thither": 0.7},
    "where": {"whither": 0.7},
    "soon": {"anon": 0.7},
    "before": {"ere": 0.7},
    "anything": {"aught": 0.7},
    "nothing": {"naught": 0.7},
    "that": {"yon": 0.6},
    "over there": {"yonder": 0.7},
    "sir": {"sirrah": 0.8},
}

WORD_PATTERN = re.compile(r"\b[\w']+\b")


def _build_reverse_channel(
    channel: Dict[str, Dict[str, float]],
) -> Dict[str, List[Tuple[str, float]]]:
    reverse: Dict[str, List[Tuple[str, float]]] = {}
    for modern, archaics in channel.items():
        for archaic, prob in archaics.items():
            reverse.setdefault(archaic, []).append((modern, prob))
    return reverse


def _log(x: float) -> float:
    return math.log(max(x, 1e-9))


def _preserve_case(src: str, replacement: str) -> str:
    if src.isupper():
        return replacement.upper()
    if src[0].isupper():
        # Capitalize the first character of the replacement only.
        return replacement[0].upper() + replacement[1:]
    return replacement


def build_normalizer(
    priors: Optional[Dict[str, float]] = None,
    channel: Dict[str, Dict[str, float]] = CHANNEL,
):
    reverse_channel = _build_reverse_channel(CHANNEL)
    model_priors = priors or DEFAULT_MODERN_PRIORS
    log_priors = {k: _log(v) for k, v in model_priors.items()}
    fallback_prior = _log(1e-6)

    def score(candidates: Iterable[Tuple[str, float]], observed: str) -> str:
        best = observed
        best_score = fallback_prior

        # Always allow the identity candidate with a weak channel likelihood
        identity_log = fallback_prior + _log(1e-3)
        best_score = identity_log
        best = observed

        for modern, emission_prob in candidates:
            prior_log = log_priors.get(modern, fallback_prior)
            total = prior_log + _log(emission_prob)
            if total > best_score:
                best_score = total
                best = modern
        return best

    def normalize(text: str) -> str:
        def replacer(match: re.Match[str]) -> str:
            word = match.group(0)
            lower = word.lower()
            candidates = reverse_channel.get(lower, [])
            modern = score(candidates, lower)
            return _preserve_case(word, modern)

        return WORD_PATTERN.sub(replacer, text)

    return normalize


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Normalize common Early Modern English spellings while preserving the "
            "original layout and punctuation."
        )
    )
    parser.add_argument("--input", required=True, help="Path to the source text file.")
    parser.add_argument(
        "--output",
        required=False,
        help="Where to write normalized text (defaults to <input>.normalized.txt).",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = (
        Path(args.output)
        if args.output
        else input_path.with_suffix(input_path.suffix + ".normalized.txt")
    )

    normalizer = build_normalizer()
    original = input_path.read_text(encoding="utf-8", errors="ignore")
    normalized = normalizer(original)
    output_path.write_text(normalized, encoding="utf-8")

    print(f"Normalized text written to {output_path}")


if __name__ == "__main__":
    main()
