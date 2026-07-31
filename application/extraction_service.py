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


def normalize_quantity_number(value):
    text = str(value).strip()
    if not text:
        return text

    try:
        parsed = float(text)
    except ValueError:
        return text

    if parsed.is_integer():
        return str(int(parsed))

    normalized = f"{parsed:.6f}".rstrip("0").rstrip(".")
    return normalized or text


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
        qty = normalize_quantity_number(qty_unit_match.group(1))
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
        qty = normalize_quantity_number(unit_qty_match.group(2))
        if unit in ["KGS", "KG"]:
            unit = "KG"
        return f"{qty} {unit}"

    return ""


def extract_row_fields(text):
    compact = re.sub(r"\s+", " ", str(text)).strip()
    compact = re.sub(r"\b\d+\s*X+\s*\d+\s*(?:K+G|KGS|NOS|EA)\b", " ", compact, flags=re.IGNORECASE)
    compact = re.sub(r"\s+", " ", compact).strip()

    # Handle "material UOM quantity" format (UOM before quantity)
    # Example: "4 ONION BIG_UB_1X1KG KG 45 25.07.2026" or "2_|POTATO LARGE_UB_1X1KG KG 20"
    # Make space after serial decorations optional to handle "2_|POTATO" (no space after |)
    # Remove \b word boundary to handle "30__" (underscore after number)
    uom_before_qty_match = re.search(
        r"^\s*[\[\(\{\|_\-]*\s*\d{1,4}[\.)\]|_:\-]*\s*(.+?)\s+(KG|KGS|NOS|EA)\.?\s+(\d+(?:\.\d+)?)",
        compact,
        flags=re.IGNORECASE,
    )
    if uom_before_qty_match:
        material = uom_before_qty_match.group(1).strip()
        unit = uom_before_qty_match.group(2).upper()
        qty = normalize_quantity_number(uom_before_qty_match.group(3))
        if unit in ["KG", "KGS"]:
            unit = "KG"
        return material, f"{qty} {unit}"
    
    # Handle OCR errors in UOM (Ko, Ke, Kq → KG) and quantity after pipe
    # Example: "206569 |[CABBAGE_UB_1X1KG Ko | 150" or "206607 |ONION BIG_UB_1X1KG Ke | 250"
    uom_typo_match = re.search(
        r"^\s*[\[\(\{\|_\-]*\s*\d{1,6}[\.)\]|_:\-]*\s*(.+?)\s+(?:K[oegq]|KGS|NOS|EA)\.?\s*[\|\]]*\s*(\d+(?:\.\d+)?)",
        compact,
        flags=re.IGNORECASE,
    )
    if uom_typo_match:
        material = uom_typo_match.group(1).strip()
        qty = normalize_quantity_number(uom_typo_match.group(2))
        # Default to KG for Ko/Ke/Kq typos
        return material, f"{qty} KG"
    
    # Handle UOM with decorations embedded in material name
    # Example: "206578 [COCONUT FRESH_UB_1X1NOS|_EA 300" or "206579 [CORIANDER LEAVES_UB_1X1K|_KG 8"
    uom_decorated_match = re.search(
        r"^\s*[\[\(\{\|_\-]*\s*\d{1,6}[\.)\]|_:\-]*\s*(.+?)[\|\]_\-]+(?:KG|KGS|NOS|EA)\s+(\d+(?:\.\d+)?)",
        compact,
        flags=re.IGNORECASE,
    )
    if uom_decorated_match:
        material = uom_decorated_match.group(1).strip()
        qty = normalize_quantity_number(uom_decorated_match.group(2))
        # Check if material ends with NOS to use EA
        if "NOS" in material.upper():
            return material, f"{qty} EA"
        return material, f"{qty} KG"

    hsn_then_uom_match = re.search(
        r"^\s*\d{1,4}\s+\d{6,7}\s+(.+?)\s+\d{6,8}(?:_[A-Z])?\s+(KG|KGS|NOS|EA)\s+(\d+(?:\.\d+)?)\b",
        compact,
        flags=re.IGNORECASE,
    )
    if hsn_then_uom_match:
        material = hsn_then_uom_match.group(1).strip()
        unit = hsn_then_uom_match.group(2).upper()
        qty = normalize_quantity_number(hsn_then_uom_match.group(3))
        if unit in ["KG", "KGS"]:
            unit = "KG"
        return material, f"{qty} {unit}"

    po_match = re.search(
        r"^\s*\d+\s+\d{6,7}\s+(.+?)\s+(\d+(?:\.\d+)?)\s*(KG|KGS|NOS|EA)\b",
        compact,
        flags=re.IGNORECASE,
    )
    if po_match:
        material = po_match.group(1).strip()
        qty = normalize_quantity_number(po_match.group(2))
        unit = po_match.group(3).upper()
        if unit in ["KG", "KGS"]:
            unit = "KG"
        return material, f"{qty} {unit}"

    # Some PDFs render rows without item-code as:
    # "15 GINGER FRESH 1.5 Kgs 43.00 64.50".
    # Parse qty-before-unit first so rate is not treated as quantity.
    table_qty_unit_match = re.search(
        r"^\s*[\[\(\{\|_\-]*\s*\d{1,4}[\.)\]|_:\-]*\s+(?:\d+\s+)?(.+?)\s+(\d+(?:\.\d+)?)\s*(KG|KGS|NOS|EA)\b",
        compact,
        flags=re.IGNORECASE,
    )
    if table_qty_unit_match:
        material = table_qty_unit_match.group(1).strip()
        qty = normalize_quantity_number(table_qty_unit_match.group(2))
        unit = table_qty_unit_match.group(3).upper()
        if unit in ["KG", "KGS"]:
            unit = "KG"
        return material, f"{qty} {unit}"

    table_match = re.search(
        r"^\s*[\[\(\{\|_\-]*\s*\d{1,4}[\.)\]|_:\-]*\s+(?:\d+\s+)?(.+?)\s+(KG|KGS|NOS|EA)\.?\s+(\d+(?:\.\d+)?)\b",
        compact,
        flags=re.IGNORECASE,
    )
    if table_match:
        material = table_match.group(1).strip()
        unit = table_match.group(2).upper()
        qty = normalize_quantity_number(table_match.group(3))
        if unit in ["KG", "KGS"]:
            unit = "KG"
        return material, f"{qty} {unit}"

    # Handle OCR errors in units for simple freeform lines (Rg, Ko, Ke, Kq → KG)
    # Example: "Onion 100Rg" or "Gobi 20Rg" or "Jinger 5Ko"
    freeform_ocr_match = re.search(
        r"^\s*(.+?)\s+(\d+(?:\.\d+)?)\s*(?:Rg|R[gq]|K[oegq]|KGS|Kgs)\.?\s*$",
        compact,
        flags=re.IGNORECASE,
    )
    if freeform_ocr_match:
        material = freeform_ocr_match.group(1).strip()
        qty = normalize_quantity_number(freeform_ocr_match.group(2))
        # All these OCR errors should map to KG
        return material, f"{qty} KG"

    freeform_match = re.search(
        r"^\s*(.+?)\s+(\d+(?:\.\d+)?)\s*(KG|KGS|NOS|EA)\.?\s*$",
        compact,
        flags=re.IGNORECASE,
    )
    if freeform_match:
        material = freeform_match.group(1).strip()
        qty = normalize_quantity_number(freeform_match.group(2))
        unit = freeform_match.group(3).upper()
        if unit in ["KG", "KGS"]:
            unit = "KG"
        return material, f"{qty} {unit}"

    return "", ""


def build_row_candidates(lines, noise_line_patterns):
    row_candidates = []
    current_row = ""
    # Make trailing space optional (\s*) to handle formats like "2_|POTATO" (no space after |)
    serial_row_pattern = r"^\s*[\[\(\{\|_\-]*\s*\d{1,4}[\.)\]|_:\-]*\s*"
    quantity_fragment_pattern = r"^\d+(?:\.\d+)?\s*(?:KG|KGS|NOS|EA)\b"
    unit_first_fragment_pattern = r"^(?:KG|KGS|NOS|EA)\b\s*\d"
    amount_fragment_pattern = r"^\d{1,3}(?:,\d{3})*(?:\.\d+)?$"
    # Pattern to recognize standalone item lines: "Name Qty Unit" (with possible OCR errors in unit)
    standalone_item_pattern = r"^[A-Za-z][\w\s]{2,}\s+\d+(?:\.\d+)?\s*(?:Rg|R[gq]|K[oegq]|KGS|Kgs|kg|nos|ea|NOS|EA)\b"

    for raw_line in lines:
        line = raw_line.strip()

        if not line or is_noise_line(line, noise_line_patterns):
            continue

        # Check if this is a standalone item line (e.g., "Onion 100Rg", "Tomato 80kg")
        is_standalone_item = bool(re.match(standalone_item_pattern, line, flags=re.IGNORECASE))
        
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
            # If it's a standalone item line, treat it as a new row
            if is_standalone_item:
                if current_row:
                    row_candidates.append(current_row)
                current_row = ""
                row_candidates.append(line)
            else:
                # Otherwise, append to current row or add as standalone
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


def is_vit_document_text(text):
    compact = normalize_text(text)
    if not compact:
        return False

    vit_markers = [
        "PURCHASE ORDER",
        "VENDOR CODE",
        "PO NUMBER",
        "MATERIAL CODE",
        "HSN SAC",
        "PRICE PER UOM",
    ]
    marker_hits = sum(1 for marker in vit_markers if marker in compact)

    has_vit_location = (
        "VELLORE INSTITUTE OF TECHNOLOGY" in compact
        or " VIT CAMPUS " in f" {compact} "
        or " VIT UNIVERSITY " in f" {compact} "
    )

    return marker_hits >= 4 and has_vit_location


def clean_vit_description(text):
    value = re.sub(r"\s+", " ", str(text)).strip()
    value = re.sub(r"\b(KG|KGS|EA|NOS)\b\s*$", "", value, flags=re.IGNORECASE).strip()
    value = re.sub(r"\s*_\s*", "_", value)
    return value


def build_fvit_row_candidates(lines):
    """
    Build FVIT row candidates from multi-line PDF extraction.
    
    FVIT PDFs extract with each field on a separate line (8 columns):
    - Line 1: Serial number (1-3 digits)
    - Line 2: Material name (e.g., "ONION_KG")
    - Line 3: HSN code (6-8 digits)
    - Line 4: UOM (e.g., "Kg", "EA")
    - Line 5: Quantity (e.g., "200")
    - Line 6: Rate/price
    - Line 7: GST% (e.g., "0%")
    - Line 8: Amount
    """
    candidates = []
    row_stop_pattern = re.compile(
        r"(gross amount|total amount|rupees in words|terms\s*&\s*conditions|prepared by|approved by)",
        flags=re.IGNORECASE,
    )
    
    # Header patterns to skip
    header_patterns = [
        r"^\s*S\.?\s*N\b",
        r"^\s*S\.?\s*NO\b",
        r"\bMATERIAL\b.*\bDESCRIPTION\b",
        r"\bDESCRIPTION\b",
        r"^\s*HSN\b",
        r"^\s*UOM\b",
        r"^\s*U\s*O\s*M\b",
        r"^\s*QTY\b",
        r"^\s*QUANTITY\b",
        r"^\s*RATE\b",
        r"^\s*PRICE\b",
        r"^\s*GST\b",
        r"^\s*AMOUNT\b",
        r"^PURCHASE\s+ORDER$",
        r"^VENDOR\b",
        r"^PO\s+(NUMBER|DATE|TYPE)\b",
    ]
    
    idx = 0
    total = len(lines)
    
    while idx < total:
        line = lines[idx].strip()
        
        # Skip empty, header, or stop lines
        if not line or row_stop_pattern.search(line):
            idx += 1
            continue
            
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in header_patterns):
            idx += 1
            continue
        
        # Look for serial number (1-3 digits standalone)
        if not re.match(r"^\d{1,3}$", line):
            idx += 1
            continue
        
        serial = line
        
        # Next line should be material name (not a 6-7 digit item code like VIT)
        if idx + 1 >= total:
            idx += 1
            continue
        
        material_line = lines[idx + 1].strip()
        
        # Skip if it looks like a VIT item code (6-7 digits)
        if re.match(r"^\d{6,7}$", material_line):
            idx += 1
            continue
        
        # Skip if it's empty or a header
        if not material_line or any(re.search(pattern, material_line, re.IGNORECASE) for pattern in header_patterns):
            idx += 1
            continue
        
        material = material_line
        
        # Look for HSN, UOM, and Quantity in next lines
        # Expected: HSN (6-8 digits) | UOM | Quantity
        hsn = ""
        uom = ""
        qty = ""
        
        scan_idx = idx + 2
        found_hsn = False
        found_uom = False
        found_qty = False
        
        # FVIT Format Variants:
        # Variant 1 (Original): Material → HSN → UOM → Quantity
        # Variant 2 (New): Material → UOM → HSN → UOM → Quantity
        
        # Scan next 6 lines for HSN, UOM, Qty (increased from 5 to 6 to handle variant 2)
        for offset in range(6):
            if scan_idx + offset >= total:
                break
            
            scan_line = lines[scan_idx + offset].strip()
            
            if not scan_line:
                continue
            
            # Check for stop pattern
            if row_stop_pattern.search(scan_line):
                break
            
            # Check for next serial (row boundary)
            if re.match(r"^\d{1,3}$", scan_line) and offset > 2:
                # Could be quantity if we already found UOM
                if found_uom and not found_qty:
                    qty = normalize_quantity_number(scan_line)
                    found_qty = True
                    break
                # Otherwise it's next row
                break
            
            # Try to find UOM first (for variant 2 where UOM comes before HSN)
            if not found_uom and re.match(r"^(KG|KGS|Kg|Kgs|EA|NOS|Nos)\.?$", scan_line, re.IGNORECASE):
                uom = scan_line.upper()
                if uom in ["KGS", "KG"]:
                    uom = "KG"
                found_uom = True
                continue
            
            # Try to find HSN (6-8 digits) - can come before or after UOM
            if not found_hsn and re.match(r"^\d{6,8}$", scan_line):
                hsn = scan_line
                found_hsn = True
                continue
            
            # Try to find UOM again (for variant 2 where UOM appears twice)
            if found_hsn and found_uom and re.match(r"^(KG|KGS|Kg|Kgs|EA|NOS|Nos)\.?$", scan_line, re.IGNORECASE):
                # Skip duplicate UOM, just continue
                continue
            
            # Try to find Quantity (pure number)
            if found_hsn and found_uom and not found_qty and re.match(r"^\d+(?:\.\d+)?$", scan_line):
                qty = normalize_quantity_number(scan_line)
                found_qty = True
                break
        
        # If we found all components, build candidate
        if found_hsn and found_uom and found_qty:
            material = clean_vit_description(material)
            # Build candidate in format: "serial material hsn uom qty"
            candidates.append(f"{serial} {material} {hsn} {uom} {qty}")
            # Move past this row
            idx = scan_idx + 6
        else:
            idx += 1
    
    return candidates


def extract_fvit_row_fields(candidate_text):
    """
    Extract material name and quantity from FVIT-specific candidate format.
    FVIT candidates are in format: "serial material hsn uom qty"
    Example: "1 ONION_KG 070310 KG 200"
    """
    # Pattern: serial (1-3 digits), material (text), hsn (6-8 digits), uom, qty
    pattern = re.compile(
        r"^\s*\d{1,3}\s+(?P<material>.+?)\s+\d{6,8}\s+(?P<unit>KG|KGS|EA|NOS)\s+(?P<qty>\d+(?:\.\d+)?)\s*$",
        flags=re.IGNORECASE,
    )
    
    match = pattern.match(candidate_text)
    if match:
        material = match.group("material").strip()
        qty = normalize_quantity_number(match.group("qty"))
        unit = match.group("unit").upper()
        if unit in ["KGS", "KG"]:
            unit = "KG"
        return material, f"{qty} {unit}"
    
    # Fallback: try to parse manually
    parts = candidate_text.split()
    if len(parts) >= 5:
        # Try to find unit and qty
        for i in range(len(parts) - 1):
            if parts[i].upper() in ["KG", "KGS", "EA", "NOS"]:
                if i + 1 < len(parts):
                    try:
                        qty = normalize_quantity_number(parts[i + 1])
                        unit = parts[i].upper()
                        if unit in ["KGS", "KG"]:
                            unit = "KG"
                        # Material is between serial and HSN
                        # Skip first part (serial), find material before HSN
                        material_parts = []
                        for j in range(1, i - 1):  # -1 to skip HSN before unit
                            if not re.match(r'^\d{6,8}$', parts[j]):
                                material_parts.append(parts[j])
                        material = " ".join(material_parts) if material_parts else ""
                        return material, f"{qty} {unit}"
                    except (ValueError, IndexError):
                        pass
    
    return "", ""


def extract_vit_row_fields(candidate_text):
    """
    Extract material name and quantity from VIT-specific candidate format.
    VIT candidates are in format: "serial item_code material hsn unit qty rate"
    Example: "10 206607 ONION BIG 07122000 KG 150.000 31.00"
    """
    # VIT candidates have: serial, item_code, material, hsn, unit, qty, rate
    # Pattern: serial (2-3 digits), item_code (6-7 digits), material (text), hsn (6-8 digits), unit, qty, rate
    pattern = re.compile(
        r"^\s*\d{2,3}\s+\d{6,7}\s+(?P<material>.+?)\s+\d{6,8}(?:_[A-Z])?\s+(?P<unit>KG|KGS|EA|NOS)\s+(?P<qty>\d+(?:\.\d+)?)(?:\s+\d+(?:\.\d+)?)?\s*$",
        flags=re.IGNORECASE,
    )
    
    match = pattern.match(candidate_text)
    if match:
        material = match.group("material").strip()
        qty = normalize_quantity_number(match.group("qty"))
        unit = match.group("unit").upper()
        if unit in ["KGS", "KG"]:
            unit = "KG"
        return material, f"{qty} {unit}"
    
    # Fallback: parse the VIT candidate text structure manually
    # Expected format: "serial item_code material ... hsn unit qty ..."
    parts = candidate_text.split()
    if len(parts) >= 5:
        # Try to find unit and qty by searching for unit keywords
        for i in range(len(parts) - 1):
            if parts[i].upper() in ["KG", "KGS", "EA", "NOS"]:
                # Found unit, next part should be qty
                if i + 1 < len(parts):
                    try:
                        qty = normalize_quantity_number(parts[i + 1])
                        unit = parts[i].upper()
                        if unit in ["KGS", "KG"]:
                            unit = "KG"
                        # Extract material: everything between item_code and HSN
                        # Skip first 2 parts (serial, item_code), find material before HSN
                        material_parts = []
                        for j in range(2, i - 1):  # -1 to skip HSN before unit
                            if not re.match(r'^\d{6,8}(?:_[A-Z])?$', parts[j]):
                                material_parts.append(parts[j])
                        material = " ".join(material_parts) if material_parts else ""
                        return material, f"{qty} {unit}"
                    except (ValueError, IndexError):
                        pass
    
    # Final fallback: use generic extraction
    return "", ""


def build_vit_row_candidates(lines):
    """
    Build VIT row candidates from multi-line PDF extraction.
    
    VIT PDFs extract with each field on a separate line:
    - Line 1: Serial number (2-3 digits)
    - Line 2: Item code (6-7 digits)
    - Lines 3+: Material description (one or more lines)
    - Next: HSN UOM Quantity pattern (e.g., "07122000 KG 150.000")
    - Next: Rate/price
    """
    candidates = []
    row_stop_pattern = re.compile(
        r"(gross amount|rupees in words|terms\s*&\s*conditions|prepared by|approved by)",
        flags=re.IGNORECASE,
    )
    
    # Header patterns to skip
    header_patterns = [
        r"^\s*S\.?\s*N\b",
        r"\bMATERIAL\s+CODE\b",
        r"\bDESCRIPTION\b",
        r"\bHSN\s*/\s*SAC\b",
        r"\bU\s*O\s*M\b",
        r"\bQUANTITY\b",
        r"\bPRICE\s+PER\b",
        r"\bSGST\b",
        r"\bCGST\b",
        r"\bIGST\b",
        r"\bTOTAL\s+NET\s+AMOUNT\b",
        r"^PURCHASE\s+ORDER$",
        r"^VENDOR\b",
        r"^PO\s+(NUMBER|DATE|TYPE|DELIVERY)\b",
        r"^DELIVERY\s+ADDRESS\b",
        r"^GST\s+AMOUNT\b",
    ]
    
    # Pattern for HSN + UOM + Quantity line (e.g., "07122000 KG 150.000")
    hsn_qty_line_pattern = re.compile(
        r"^\s*(?P<hsn>\d{6,8}(?:_[A-Z])?)\s+(?P<uom>KG|KGS|EA|NOS)\s+(?P<qty>\d+(?:\.\d+)?)\s*$",
        flags=re.IGNORECASE,
    )
    
    idx = 0
    total = len(lines)
    
    while idx < total:
        line = lines[idx].strip()
        
        # Skip empty, header, or stop lines
        if not line or row_stop_pattern.search(line):
            idx += 1
            continue
            
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in header_patterns):
            idx += 1
            continue
        
        # Look for serial number (2-3 digits standalone)
        if not re.match(r"^\d{2,3}$", line):
            idx += 1
            continue
        
        serial = line
        
        # Next line should be item code (6-7 digits)
        if idx + 1 >= total:
            idx += 1
            continue
            
        item_code_line = lines[idx + 1].strip()
        if not re.match(r"^\d{6,7}$", item_code_line):
            idx += 1
            continue
        
        item_code = item_code_line
        
        # Collect material description lines until we find HSN pattern
        material_parts = []
        scan_idx = idx + 2
        hsn_line_idx = None
        
        while scan_idx < total:
            scan_line = lines[scan_idx].strip()
            
            if not scan_line:
                scan_idx += 1
                continue
            
            # Check if this is stop pattern
            if row_stop_pattern.search(scan_line):
                break
            
            # Check if this is header
            if any(re.search(pattern, scan_line, re.IGNORECASE) for pattern in header_patterns):
                break
            
            # Check if this is another serial number (next row starting)
            if re.match(r"^\d{2,3}$", scan_line):
                break
            
            # Check if this is HSN+UOM+Qty line
            hsn_match = hsn_qty_line_pattern.match(scan_line)
            if hsn_match:
                hsn_line_idx = scan_idx
                break
            
            # Check for split HSN case: "07104000_" on one line, "A" on next, "KG QTY" on next
            # Pattern: line ends with "_", next line is 1-2 chars, next line has "UOM QTY"
            if scan_line.endswith("_") and re.match(r"^\d{6,8}_$", scan_line):
                # This might be a split HSN, check next lines
                if scan_idx + 2 < total:
                    next1 = lines[scan_idx + 1].strip()
                    next2 = lines[scan_idx + 2].strip()
                    
                    # Check if next1 is a short suffix (e.g., "A") and next2 has UOM + QTY
                    if len(next1) <= 2 and re.match(r"^[A-Z]$", next1, re.IGNORECASE):
                        uom_qty_pattern = re.compile(r"^(KG|KGS|EA|NOS)\s+(\d+(?:\.\d+)?)$", re.IGNORECASE)
                        uom_qty_match = uom_qty_pattern.match(next2)
                        if uom_qty_match:
                            # Found split HSN! Combine them
                            combined_hsn = scan_line + next1
                            combined_line = f"{combined_hsn} {next2}"
                            # Now check if combined line matches our pattern
                            combined_match = hsn_qty_line_pattern.match(combined_line)
                            if combined_match:
                                hsn_line_idx = scan_idx  # Mark position for later processing
                                # Store the combined line for later
                                lines[scan_idx] = combined_line
                                break
            
            # Check if it's just a number (could be rate, GST, amount) - stop collecting material
            if re.match(r"^\d+(?:\.\d+)?$", scan_line) or re.match(r"^\d{1,3}(?:,\d{3})*(?:\.\d+)?$", scan_line):
                # Could be rate after HSN line, skip for now
                scan_idx += 1
                continue
            
            # This must be part of material description
            material_parts.append(scan_line)
            scan_idx += 1
        
        # If we found HSN line and have material, build candidate
        if hsn_line_idx is not None and material_parts:
            hsn_line = lines[hsn_line_idx].strip()
            hsn_match = hsn_qty_line_pattern.match(hsn_line)
            
            if hsn_match:
                material = " ".join(material_parts)
                material = clean_vit_description(material)
                
                hsn = hsn_match.group("hsn").replace("_", "")
                unit = hsn_match.group("uom").upper()
                if unit in ["KGS", "KG"]:
                    unit = "KG"
                qty = normalize_quantity_number(hsn_match.group("qty"))
                
                # Try to find rate (next non-empty line after HSN that's a number)
                rate = "0"
                for rate_idx in range(hsn_line_idx + 1, min(hsn_line_idx + 3, total)):
                    rate_line = lines[rate_idx].strip()
                    if rate_line and re.match(r"^\d+(?:\.\d+)?$", rate_line):
                        rate = rate_line
                        break
                
                # Build candidate
                candidates.append(f"{serial} {item_code} {material} {hsn} {unit} {qty} {rate}")
                
                # Move to next row (after HSN line)
                idx = hsn_line_idx + 1
                continue
        
        # No valid row found, move to next line
        idx += 1
    
    return candidates


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


def extract_quantities_in_order(text):
    compact = re.sub(r"\s+", " ", str(text)).strip().upper()
    compact = re.sub(r"\b\d+\s*X+\s*\d+\s*(?:K+G|KGS|NOS|EA)\b", " ", compact)
    compact = re.sub(r"\s+", " ", compact).strip()

    found = []

    for match in re.finditer(
        r"\b(\d+(?:\.\d+)?)\s*(KG|KGS|G|GM|GRAMS?|NOS|EA)\.?\b",
        compact,
        flags=re.IGNORECASE,
    ):
        qty = match.group(1)
        unit = match.group(2).upper()
        if unit in ["KGS", "KG"]:
            unit = "KG"
        found.append((match.start(), f"{qty} {unit}"))

    found.sort(key=lambda item: item[0])

    quantities = []
    for _, quantity in found:
        if not quantities or quantities[-1] != quantity:
            quantities.append(quantity)

    return quantities


def split_collapsed_multi_item_row(row, vegetable_aliases):
    normalized = normalize_material_name(row)
    if not normalized:
        return [row]

    aliases = sorted(vegetable_aliases.keys(), key=len, reverse=True)
    hits = []

    for alias in aliases:
        for match in re.finditer(rf"\b{re.escape(alias)}\b", normalized):
            hits.append((match.start(), match.end(), alias))

    if not hits:
        return [row]

    hits.sort(key=lambda item: (item[0], -(item[1] - item[0])))

    selected = []
    for start, end, alias in hits:
        overlaps = any(not (end <= s or start >= e) for s, e, _ in selected)
        if overlaps:
            continue
        selected.append((start, end, alias))

    selected.sort(key=lambda item: item[0])
    quantities = extract_quantities_in_order(row)

    if len(selected) < 2 or len(quantities) < 2:
        return [row]

    canonical_hits = [vegetable_aliases.get(alias, alias) for _, _, alias in selected]
    if len(set(canonical_hits)) < 2:
        return [row]

    # Pair aliases and quantities in order when one OCR line collapses multiple rows.
    # This prevents the second row quantity from being attached to the first row name.
    split_rows = []
    pair_count = min(len(selected), len(quantities))
    for idx in range(pair_count):
        alias = selected[idx][2]
        split_rows.append(f"{alias} {quantities[idx]}")

    return split_rows if len(split_rows) >= 2 else [row]


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


# ============================================================
# MHS MULTI-LINE FORMAT PARSER
# ============================================================

def is_mhs_document_text(text):
    """
    Detect MHS format: Multi-line pattern with Item Name | Item Code | Quantity
    """
    if not text:
        return False
    
    text_upper = text.upper()
    
    # Check for MHS-specific keywords
    has_mhs_marker = any(marker in text_upper for marker in [
        "INDYA FOODS - MHS",
        "MHS/PR/",
        "PURCHASE REQUISITION",
    ])
    
    if not has_mhs_marker:
        return False
    
    # Check for multi-line pattern: lines with 6-7 digit codes
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    item_code_count = sum(1 for line in lines if re.match(r'^\d{7}$', line))
    
    # Should have multiple item codes (at least 3)
    return item_code_count >= 3


def build_mhs_row_candidates(lines):
    """
    Build MHS row candidates from multi-line format.
    Pattern: Item Name | Item Code (7 digits) | Quantity with UOM
    
    Example:
        BABY CORN PEELED
        1100006
        1 Kgs
    """
    row_candidates = []
    idx = 0
    total = len(lines)
    
    # Skip header lines
    header_keywords = ["ITEM CODE", "ITEM NAME", "QTY", "DESCRIPTION", "HSN", "GSTIN", "DOC NO", "DOC DATE"]
    
    while idx < total:
        line = lines[idx].strip()
        
        # Skip empty lines
        if not line:
            idx += 1
            continue
        
        # Skip header lines
        if any(keyword in line.upper() for keyword in header_keywords):
            idx += 1
            continue
        
        # Skip lines that look like metadata
        if re.match(r'^(Regd\.|Email|GSTIN|Purchase|Doc|Department|Buyer|Plant|Indent)', line, re.IGNORECASE):
            idx += 1
            continue
        
        # Check if this line looks like an item name (alphabetic, > 3 chars)
        if not re.match(r'^[A-Z][A-Z\s]{2,}', line, re.IGNORECASE):
            idx += 1
            continue
        
        item_name = line
        
        # Next line should be item code (exactly 7 digits)
        if idx + 1 >= total:
            idx += 1
            continue
        
        item_code_line = lines[idx + 1].strip()
        if not re.match(r'^\d{7}$', item_code_line):
            idx += 1
            continue
        
        item_code = item_code_line
        
        # Next line should be quantity with UOM
        if idx + 2 >= total:
            idx += 1
            continue
        
        qty_line = lines[idx + 2].strip()
        
        # Check if it has quantity pattern (number + unit)
        if not re.search(r'\d+(?:\.\d+)?\s*(?:Kgs?|kgs?|KGS?|Nos?|nos?|NOS?|EA|ea)', qty_line, re.IGNORECASE):
            idx += 1
            continue
        
        # Found a valid 3-line pattern, combine them
        combined = f"{item_name} | {item_code} | {qty_line}"
        row_candidates.append(combined)
        
        # Move to next potential item (skip the 3 lines we just processed)
        idx += 3
    
    return row_candidates


def extract_mhs_row_fields(candidate_text):
    """
    Extract material and quantity from MHS combined row.
    Format: "ITEM NAME | ITEM_CODE | QTY UNIT"
    """
    if not candidate_text or " | " not in candidate_text:
        return "", ""
    
    parts = candidate_text.split(" | ")
    if len(parts) < 3:
        return "", ""
    
    material = parts[0].strip()
    qty_text = parts[2].strip()
    
    # Extract quantity and unit
    qty_match = re.search(r'(\d+(?:\.\d+)?)\s*(Kgs?|kgs?|KGS?|Nos?|nos?|NOS?|EA|ea)', qty_text, re.IGNORECASE)
    if not qty_match:
        return material, ""
    
    qty = normalize_quantity_number(qty_match.group(1))
    unit = qty_match.group(2).upper()
    
    # Normalize units
    if unit.startswith("KG"):
        unit = "KG"
    elif unit.startswith("NO"):
        unit = "NOS"
    elif unit.upper() == "EA":
        unit = "EA"
    
    # Clean material name
    material = normalize_material_name(material)
    
    return material, f"{qty} {unit}"


def detect_vegetables(
    text,
    vegetable_aliases,
    vegetable_tamil_map,
    noise_line_patterns,
    return_details=False,
    confidence_threshold=75,
    client_name=None,
):
    if not text:
        empty_report = build_extraction_report([], [], 0, 0)
        empty_report["parser_strategy"] = "none"
        empty_report["vit_mode_activated"] = False
        empty_report["vit_activation_reason"] = "No text provided"
        return ([], empty_report) if return_details else []

    lines = [line.strip() for line in str(text).splitlines() if line.strip()]
    row_candidates = []
    
    # Determine which client-specific parser to use
    mhs_by_client = client_name and client_name.upper() == "MHS"
    fvit_by_client = client_name and client_name.upper() == "FVIT"
    vit_by_client = client_name and client_name.upper() == "VIT"
    
    mhs_by_detection = is_mhs_document_text(text)
    vit_by_detection = is_vit_document_text(text)
    
    # MHS mode (multi-line: Item Name | Item Code | Quantity)
    mhs_mode = mhs_by_client or (mhs_by_detection and not fvit_by_client and not vit_by_client)
    # FVIT mode (8-column format)
    fvit_mode = fvit_by_client
    # VIT mode (11-12 column format)
    vit_mode = vit_by_client or (vit_by_detection and not fvit_mode and not mhs_mode)
    
    # Track parser strategy for reporting
    parser_mode = None
    activation_reason = ""
    
    if mhs_mode:
        parser_mode = "mhs-multiline"
        if mhs_by_client:
            activation_reason = f"Client name: '{client_name}'"
        else:
            activation_reason = "Auto-detected MHS document signature"
        row_candidates = build_mhs_row_candidates(lines)
        extraction_attempted = True
        extraction_found_rows = len(row_candidates) > 0
    elif fvit_mode:
        parser_mode = "fvit-special"
        activation_reason = f"Client name: '{client_name}'"
        row_candidates = build_fvit_row_candidates(lines)
        extraction_attempted = True
        extraction_found_rows = len(row_candidates) > 0
    elif vit_mode:
        parser_mode = "vit-special"
        if vit_by_client:
            activation_reason = f"Client name: '{client_name}'"
        else:
            activation_reason = "Auto-detected VIT document signature"
        row_candidates = build_vit_row_candidates(lines)
        extraction_attempted = True
        extraction_found_rows = len(row_candidates) > 0
    else:
        extraction_attempted = False
        extraction_found_rows = False

    if not row_candidates:
        row_candidates = build_row_candidates(lines, noise_line_patterns)
        fragmented_candidates = []
        if is_fragmented_pdf_layout(lines, noise_line_patterns):
            fragmented_candidates = build_fragmented_pdf_candidates(lines, noise_line_patterns)

        if fragmented_candidates:
            for row in fragmented_candidates:
                if row not in row_candidates:
                    row_candidates.append(row)

    split_candidates = []
    for row in row_candidates:
        split_candidates.extend(split_collapsed_multi_item_row(row, vegetable_aliases))
    row_candidates = split_candidates

    results = []
    unmatched_lines = []
    candidate_count = len(row_candidates)

    for idx, row in enumerate(row_candidates, start=1):
        # Use client-specific extractor based on mode
        if mhs_mode:
            material, quantity = extract_mhs_row_fields(row)
        elif fvit_mode:
            material, quantity = extract_fvit_row_fields(row)
        elif vit_mode:
            material, quantity = extract_vit_row_fields(row)
        else:
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

        # For VIT/MHS mode, quantity should already be extracted; for generic, try to extract if missing
        if not quantity and not vit_mode and not mhs_mode:
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
        report["parser_strategy"] = parser_mode if parser_mode else "generic"
        report["vit_mode_activated"] = vit_mode or fvit_mode
        report["vit_activation_reason"] = activation_reason
        report["vit_extraction_attempted"] = extraction_attempted
        report["vit_extraction_found_rows"] = extraction_found_rows
        report["parser_fallback"] = extraction_attempted and not extraction_found_rows
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
    report["parser_strategy"] = parser_mode if parser_mode else "generic"
    report["vit_mode_activated"] = vit_mode or fvit_mode
    report["vit_activation_reason"] = activation_reason
    report["vit_extraction_attempted"] = extraction_attempted
    report["vit_extraction_found_rows"] = extraction_found_rows
    report["parser_fallback"] = extraction_attempted and not extraction_found_rows
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


def format_mapped_row_quantity(qty_value, unit_value=None):
    qty_text = str(qty_value).strip()
    if not qty_text or qty_text.lower() == "nan":
        return ""

    qty_text = qty_text.replace(",", "")
    match = re.search(r"\d+(?:\.\d+)?", qty_text)
    if not match:
        return ""

    qty_number = match.group(0)
    try:
        parsed = float(qty_number)
        qty_number = str(int(parsed)) if parsed.is_integer() else str(parsed)
    except ValueError:
        pass

    unit = ""
    if unit_value is not None:
        unit = str(unit_value).strip().upper()

    if unit in ["KGS", "KG"]:
        unit = "KG"

    if not unit or unit.lower() == "nan":
        return qty_number

    return f"{qty_number} {unit}"


def detect_vegetables_from_mapped_rows(
    mapped_rows,
    vegetable_aliases,
    vegetable_tamil_map,
    return_details=False,
    confidence_threshold=75,
    client_name=None,
):
    if not mapped_rows:
        empty_report = build_extraction_report([], [], 0, 0)
        return ([], empty_report) if return_details else []

    results = []
    unmatched_lines = []

    for idx, row in enumerate(mapped_rows, start=1):
        item_text = str(row.get("item", "")).strip()
        quantity = format_mapped_row_quantity(row.get("qty", ""), row.get("unit", ""))

        if not item_text:
            continue

        canonical_name, match_score = fuzzy_match_vegetable_name(
            item_text,
            vegetable_aliases=vegetable_aliases,
            confidence_threshold=confidence_threshold,
        )

        if not canonical_name:
            unmatched_lines.append({"Line": idx, "Text": item_text})
            continue

        detection = VegetableDetection(
            source_name=canonical_name.title(),
            tamil_name=vegetable_tamil_map.get(canonical_name, ""),
            quantity=quantity,
            status="Needs Review" if not quantity else "Auto Extracted",
            confidence_score=match_score if quantity else max(min(match_score, 95), 60),
            raw_line=item_text,
        )
        results.append(detection.as_record())

    results = deduplicate_detections(results)
    report = build_extraction_report(results, unmatched_lines, len(mapped_rows), len(mapped_rows))
    return (results, report) if return_details else results
