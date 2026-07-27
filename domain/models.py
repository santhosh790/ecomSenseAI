from dataclasses import dataclass


@dataclass
class VegetableDetection:
    source_name: str
    tamil_name: str
    quantity: str
    confidence_score: int
    status: str
    raw_line: str = ""

    def as_record(self):
        return {
            "Source Name": self.source_name,
            "Tamil Name": self.tamil_name,
            "Quantity": self.quantity,
            "Status": self.status,
            "Confidence": f"{self.confidence_score}%",
        }


@dataclass(frozen=True)
class VegetableCatalog:
    vegetable_tamil_map: dict[str, str]
    vegetable_aliases: dict[str, str]
    noise_line_patterns: list[str]
