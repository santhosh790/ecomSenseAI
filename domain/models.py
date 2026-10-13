from dataclasses import dataclass


@dataclass
class ProductDetection:
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


# Backward-compatible alias
VegetableDetection = ProductDetection


@dataclass(frozen=True)
class ProductCatalog:
    product_tamil_map: dict[str, str]
    product_aliases: dict[str, str]
    noise_line_patterns: list[str]

    @property
    def vegetable_tamil_map(self) -> dict[str, str]:
        return self.product_tamil_map

    @property
    def vegetable_aliases(self) -> dict[str, str]:
        return self.product_aliases


# Backward-compatible alias
VegetableCatalog = ProductCatalog

