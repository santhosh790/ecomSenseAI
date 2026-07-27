import re

try:
    from rapidfuzz import fuzz, process
except ImportError:
    fuzz = None
    process = None

from domain.models import VegetableDetection


def normalize_text(text):
    normalized = re.sub(r"[^A-Za-z0-9]+", " ", str(text).upper())
    return re.sub(r"\s+", " ", normalized).strip()


def normalize_material_name(name):
    value = normalize_text(name)
    value = re.sub(r"\bUB\b", " ", value)
    value = re.sub(r"\b\d+\s*X+\s*\d+\s*(?:K+G|KGS|NOS|EA)\b", " ", value)
    value = re.sub(r"\b\d+(?:\.\d+)?\s*(?:KG|KGS|NOS|EA)\b", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def is_noise_line(line, noise_line_patterns):
    value = line.strip().lower()
    if not value:
        return True

    for pattern in noise_line_patterns:
        if re.search(pattern, value):
            return True

    return False


def extract_row_quantity(text):
    compact = re.sub(r"\s+", " ", str(text)).strip().upper()
    compact = re.sub(r"\b\d+\s*X+\s*\d+\s*(?:K+G|KGS|NOS|EA)\b", " ", compact)
    compact = re.sub(r"\s+", " ", compact).strip()

    # Prefer quantity-then-unit first. In PDF table text, this avoids taking rate as quantity
    # for lines like "6 Kgs 22.00" where 22.00 is the rate.
    qty_unit_match = re.search(
        r"\b(\d+(?:\.\d+)?)\s*(KG|KGS|G|GM|GRAMS?|NOS|EA)\.?\b",
        compact,
        flags=re.IGNORECASE,
    )
    if qty_unit_match:
        qty = qty_unit_match.group(1)
        unit = qty_unit_match.group(2).upper()
        if unit in ["KGS", "KG"]:
            unit = "KG"
        return f"{qty} {unit}"

    unit_qty_match = re.search(
        r"\b(KG|KGS|NOS|EA)\.?\b\s*(\d+(?:\.\d+)?)\b",
        compact,
        flags=re.IGNORECASE,
    )
    if unit_qty_match:
        unit = unit_qty_match.group(1).upper()
        qty = unit_qty_match.group(2)
        if unit in ["KGS", "KG"]:
            unit = "KG"
        return f"{qty} {unit}"

    return ""


def extract_row_fields(text):
    compact = re.sub(r"\s+", " ", str(text)).strip()
    compact = re.sub(r"\b\d+\s*X+\s*\d+\s*(?:K+G|KGS|NOS|EA)\b", " ", compact, flags=re.IGNORECASE)
    compact = re.sub(r"\s+", " ", compact).strip()

    po_match = re.search(
        r"^\s*\d+\s+\d{6,7}\s+(.+?)\s+(\d+(?:\.\d+)?)\s*(KG|KGS|NOS|EA)\b",
        compact,
        flags=re.IGNORECASE,
    )
    if po_match:
        material = po_match.group(1).strip()
        qty = po_match.group(2)
        unit = po_match.group(3).upper()
        if unit in ["KG", "KGS"]:
            unit = "KG"
        return material, f"{qty} {unit}"

    table_match = re.search(
        r"^\s*[\[\(\{\|_\-]*\s*\d+[\.)\]|_:\-]*\s+(?:\d+\s+)?(.+?)\s+(KG|KGS|NOS|EA)\.?\s+(\d+(?:\.\d+)?)\b",
        compact,
        flags=re.IGNORECASE,
    )
    if table_match:
        material = table_match.group(1).strip()
        unit = table_match.group(2).upper()
        qty = table_match.group(3)
        if unit in ["KG", "KGS"]:
            unit = "KG"
        return material, f"{qty} {unit}"

    freeform_match = re.search(
        r"^\s*(.+?)\s+(\d+(?:\.\d+)?)\s*(KG|KGS|NOS|EA)\.?\s*$",
        compact,
        flags=re.IGNORECASE,
    )
    if freeform_match:
        material = freeform_match.group(1).strip()
        qty = freeform_match.group(2)
        unit = freeform_match.group(3).upper()
        if unit in ["KG", "KGS"]:
            unit = "KG"
        return material, f"{qty} {unit}"

    return "", ""


def build_row_candidates(lines, noise_line_patterns):
    row_candidates = []
    current_row = ""
    serial_row_pattern = r"^\s*[\[\(\{\|_\-]*\s*\d+[\.)\]|_:\-]*\s*"
    quantity_fragment_pattern = r"^\d+(?:\.\d+)?\s*(?:KG|KGS|NOS|EA)\b"
    unit_first_fragment_pattern = r"^(?:KG|KGS|NOS|EA)\b\s*\d"
    amount_fragment_pattern = r"^\d{1,3}(?:,\d{3})*(?:\.\d+)?$"

    for raw_line in lines:
        line = raw_line.strip()

        if not line or is_noise_line(line, noise_line_patterns):
            continue

        serial_match = re.match(serial_row_pattern, line)
        if serial_match:
            remainder = line[serial_match.end():].strip()
            has_item_code = bool(re.search(r"\b\d{6,7}\b", line))
            is_quantity_fragment = bool(re.match(quantity_fragment_pattern, remainder, flags=re.IGNORECASE))
            is_unit_first_fragment = bool(re.match(unit_first_fragment_pattern, remainder, flags=re.IGNORECASE))
            is_amount_fragment = bool(re.match(amount_fragment_pattern, remainder))

            # Some PDF extracts split one row into multiple lines where continuation starts
            # with a number (e.g. "6 Kgs 22.00" or "132.00"). Keep them in the same row.
            if current_row and not has_item_code and (is_quantity_fragment or is_unit_first_fragment or is_amount_fragment):
                current_row = f"{current_row} {line}"
                continue

            if current_row:
                row_candidates.append(current_row)
            current_row = line
        else:
            if current_row:
                current_row = f"{current_row} {line}"
            else:
                row_candidates.append(line)

    if current_row:
        row_candidates.append(current_row)

    return row_candidates


def build_fragmented_pdf_candidates(lines, noise_line_patterns):
    candidates = []
    qty_line_pattern = r"^\d+(?:\.\d+)?\s*(?:KG|KGS|NOS|EA)\b"
    unit_only_pattern = r"^(?:KG|KGS|NOS|EA)\.?$"
    standalone_qty_pattern = r"^\d+(?:\.\d+)?$"

    for idx, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line or is_noise_line(line, noise_line_patterns):
            continue

        quantity = ""
        if re.match(qty_line_pattern, line, flags=re.IGNORECASE):
            quantity = extract_row_quantity(line)
        elif re.match(standalone_qty_pattern, line):
            prev_idx = idx - 1
            prev = lines[prev_idx].strip() if prev_idx >= 0 else ""
            if re.match(unit_only_pattern, prev, flags=re.IGNORECASE):
                unit = prev.upper().replace("KGS", "KG")
                quantity = f"{line} {unit}"

        if not quantity:
            continue

        material = ""
        for back in range(idx - 1, max(-1, idx - 5), -1):
            prev = lines[back].strip()
            if not prev or is_noise_line(prev, noise_line_patterns):
                continue

            # Skip numeric-only fragments commonly emitted by PDF extraction.
            if re.match(r"^\d+(?:\.\d+)?$", prev):
                continue
            if re.match(r"^\d{1,3}(?:,\d{3})*(?:\.\d+)?$", prev):
                continue
            if re.match(r"^\d{6,7}$", prev):
                continue
            if re.match(unit_only_pattern, prev, flags=re.IGNORECASE):
                continue

            if re.search(r"[A-Za-z]", prev):
                material = prev
                break

        if material:
            candidates.append(f"{material} {quantity}")

    return candidates


def is_fragmented_pdf_layout(lines, noise_line_patterns):
    qty_line_pattern = r"^\d+(?:\.\d+)?\s*(?:KG|KGS|NOS|EA)\b"
    standalone_item_code_pattern = r"^\d{6,7}$"
    unit_only_pattern = r"^(?:KG|KGS|NOS|EA)\.?$"
    standalone_qty_pattern = r"^\d+(?:\.\d+)?$"

    qty_lines = 0
    item_code_lines = 0
    material_lines = 0
    split_qty_lines = 0

    for idx, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line or is_noise_line(line, noise_line_patterns):
            continue

        if re.match(qty_line_pattern, line, flags=re.IGNORECASE):
            qty_lines += 1
        elif re.match(standalone_item_code_pattern, line):
            item_code_lines += 1
        elif re.match(standalone_qty_pattern, line):
            prev = lines[idx - 1].strip() if idx > 0 else ""
            if re.match(unit_only_pattern, prev, flags=re.IGNORECASE):
                split_qty_lines += 1
        elif re.search(r"[A-Za-z]", line):
            material_lines += 1

    return (qty_lines + split_qty_lines) >= 2 and item_code_lines >= 1 and material_lines >= 2


def fuzzy_match_vegetable_name(text, vegetable_aliases, confidence_threshold=75):
    material = normalize_material_name(text)
    if not material:
        return "", 0

    aliases = sorted(vegetable_aliases.keys(), key=len, reverse=True)

    for alias in aliases:
        if alias in material:
            return vegetable_aliases[alias], 99

    if process is None or fuzz is None:
        return "", 0

    match = process.extractOne(material, aliases, scorer=fuzz.token_set_ratio)
    if not match:
        return "", 0

    alias, score, _ = match
    score = int(score)

    if score >= int(confidence_threshold):
        return vegetable_aliases[alias], score

    return "", score


def build_extraction_report(results, unmatched_lines, candidate_count, total_lines):
    extracted_count = len(results)
    with_quantity = sum(1 for item in results if item.get("Quantity", "").strip())

    high_confidence = 0
    for item in results:
        score_text = str(item.get("Confidence", "0")).replace("%", "").strip()
        try:
            score = int(float(score_text))
        except ValueError:
            score = 0
        if score >= 90:
            high_confidence += 1

    return {
        "total_lines": total_lines,
        "candidate_lines": candidate_count,
        "extracted_rows": extracted_count,
        "with_quantity": with_quantity,
        "without_quantity": max(extracted_count - with_quantity, 0),
        "high_confidence": high_confidence,
        "unmatched_lines": unmatched_lines,
    }


def deduplicate_detections(results):
    # Prefer rows that include a quantity when the same source appears multiple times
    # due to mixed candidate builders.
    has_qty_by_source = {}
    for row in results:
        source = str(row.get("Source Name", "")).strip()
        has_qty = bool(str(row.get("Quantity", "")).strip())
        if source:
            has_qty_by_source[source] = has_qty_by_source.get(source, False) or has_qty

    filtered = []
    seen_source_qty = set()

    for row in results:
        source = str(row.get("Source Name", "")).strip()
        quantity = str(row.get("Quantity", "")).strip()

        if source and not quantity and has_qty_by_source.get(source, False):
            continue

        dedupe_key = (source, quantity)
        if dedupe_key in seen_source_qty:
            continue

        seen_source_qty.add(dedupe_key)
        filtered.append(row)

    return filtered


def detect_vegetables(
    text,
    vegetable_aliases,
    vegetable_tamil_map,
    noise_line_patterns,
    return_details=False,
    confidence_threshold=75,
):
    if not text:
        empty_report = build_extraction_report([], [], 0, 0)
        return ([], empty_report) if return_details else []

    lines = [line.strip() for line in str(text).splitlines() if line.strip()]
    row_candidates = build_row_candidates(lines, noise_line_patterns)
    fragmented_candidates = []
    if is_fragmented_pdf_layout(lines, noise_line_patterns):
        fragmented_candidates = build_fragmented_pdf_candidates(lines, noise_line_patterns)

    if fragmented_candidates:
        for row in fragmented_candidates:
            if row not in row_candidates:
                row_candidates.append(row)

    results = []
    unmatched_lines = []
    candidate_count = len(row_candidates)

    for idx, row in enumerate(row_candidates, start=1):
        material, quantity = extract_row_fields(row)
        material_for_match = material if material else row

        canonical_name, match_score = fuzzy_match_vegetable_name(
            material_for_match,
            vegetable_aliases=vegetable_aliases,
            confidence_threshold=confidence_threshold,
        )

        if not canonical_name:
            unmatched_lines.append({"Line": idx, "Text": row})
            continue

        if not quantity:
            quantity = extract_row_quantity(row)

        detection = VegetableDetection(
            source_name=canonical_name.title(),
            tamil_name=vegetable_tamil_map.get(canonical_name, ""),
            quantity=quantity,
            status="Needs Review" if not quantity else "Auto Extracted",
            confidence_score=match_score if quantity else max(min(match_score, 95), 60),
            raw_line=row,
        )
        results.append(detection.as_record())

    results = deduplicate_detections(results)

    if results:
        report = build_extraction_report(results, unmatched_lines, candidate_count, len(lines))
        return (results, report) if return_details else results

    normalized_text = normalize_material_name(text)
    seen_fallback = set()

    for alias, canonical_name in vegetable_aliases.items():
        if alias in normalized_text:
            if canonical_name in seen_fallback:
                continue

            seen_fallback.add(canonical_name)
            detection = VegetableDetection(
                source_name=canonical_name.title(),
                tamil_name=vegetable_tamil_map.get(canonical_name, ""),
                quantity="",
                status="Needs Review",
                confidence_score=70,
            )
            results.append(detection.as_record())

    report = build_extraction_report(results, unmatched_lines, candidate_count, len(lines))
    return (results, report) if return_details else results


def find_canonical_vegetable_name(text, vegetable_aliases, confidence_threshold=75):
    canonical_name, _ = fuzzy_match_vegetable_name(
        text,
        vegetable_aliases=vegetable_aliases,
        confidence_threshold=confidence_threshold,
    )
    return canonical_name


def parse_confidence_value(value):
    score_text = str(value).replace("%", "").strip()
    try:
        return int(float(score_text))
    except ValueError:
        return 0


def apply_confidence_policy(items, auto_extract_threshold=90):
    updated = []

    for item in items:
        row = dict(item)
        score = parse_confidence_value(row.get("Confidence", "0"))

        if row.get("Status") == "Manually Added":
            updated.append(row)
            continue

        if not str(row.get("Quantity", "")).strip():
            row["Status"] = "Needs Review"
        elif score >= int(auto_extract_threshold):
            row["Status"] = "Auto Extracted"
        else:
            row["Status"] = "Needs Review"

        updated.append(row)

    return updated
