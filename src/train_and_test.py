import argparse
import random
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

from normalize_spelling import CHANNEL, WORD_PATTERN, build_normalizer


def _build_reverse_channel(channel: Dict[str, Dict[str, float]]):
    reverse = {}
    for modern, archaics in channel.items():
        for archaic, prob in archaics.items():
            reverse.setdefault(archaic, []).append((modern, prob))
    return reverse


def _gold_label(reverse_channel, token: str) -> str:
    candidates = reverse_channel.get(token, [])
    if not candidates:
        return token
    return max(candidates, key=lambda x: x[1])[0]


def _derive_priors(train_pairs: List[Tuple[str, str]]) -> Dict[str, float]:
    counts = Counter(modern for _, modern in train_pairs)
    total = sum(counts.values())
    # Laplace smoothing
    vocab = len(counts)
    return {k: (v + 1) / (total + vocab) for k, v in counts.items()}


def _token_pairs(path: Path) -> List[Tuple[str, str]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    reverse_channel = _build_reverse_channel(CHANNEL)
    pairs = []
    for match in WORD_PATTERN.finditer(text):
        obs = match.group(0).lower()
        gold = _gold_label(reverse_channel, obs)
        if gold != obs:  # include only archaic forms we model
            pairs.append((obs, gold))
    return pairs


def main():
    parser = argparse.ArgumentParser(
        description="Derive priors from training data and evaluate normalizer accuracy."
    )
    parser.add_argument("--input", required=True, help="Path to source text.")
    parser.add_argument(
        "--split",
        type=float,
        default=0.8,
        help="Train split fraction (default: 0.8).",
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for reproducible split."
    )
    args = parser.parse_args()

    source = Path(args.input)
    pairs = _token_pairs(source)
    if not pairs:
        print("No archaic tokens found for evaluation.")
        return

    random.Random(args.seed).shuffle(pairs)
    cut = int(len(pairs) * args.split)
    train, test = pairs[:cut], pairs[cut:]

    priors = _derive_priors(train)
    normalizer = build_normalizer(priors=priors, channel=CHANNEL)

    # Evaluate
    correct = 0
    for obs, gold in test:
        pred = normalizer(obs)
        if pred.lower() == gold:
            correct += 1
    accuracy = correct / max(len(test), 1)

    print(f"Derived priors from {len(train)} training tokens; testing on {len(test)} tokens.")
    print(f"Accuracy: {accuracy:.3f}")
    # Show a few examples
    for obs, gold in test[:10]:
        pred = normalizer(obs)
        print(f"{obs} -> {pred} (gold: {gold})")


if __name__ == "__main__":
    main()
