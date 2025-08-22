import yaml, pathlib
from dataclasses import dataclass

@dataclass(frozen=True)
class Invariants:
    max_decks: int
    max_cards: int
    text_rules: list[str]

def load_invariants(path: str = "specs/invariants.yaml") -> Invariants:
    data = yaml.safe_load(pathlib.Path(path).read_text())["inv"]
    return Invariants(
        max_decks = data["INV-READ-1"]["N"],
        max_cards = data["INV-READ-2"]["M"],
        text_rules = [
            f"INV-READ-1: {data['INV-READ-1']['desc'].replace('N', str(data['INV-READ-1']['N']))}",
            f"INV-READ-2: {data['INV-READ-2']['desc'].replace('M', str(data['INV-READ-2']['M']))}",
            "INV-READ-3: " + data["INV-READ-3"]["desc"],
            "INV-READ-4: " + data["INV-READ-4"]["desc"],
        ]
    )
