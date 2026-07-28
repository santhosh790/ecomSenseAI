from application.extraction_service import apply_confidence_policy
from application.extraction_service import detect_vegetables as detect_vegetables_raw
from application.extraction_service import detect_vegetables_from_mapped_rows as detect_vegetables_from_mapped_rows_raw
from application.extraction_service import find_canonical_vegetable_name as find_canonical_vegetable_name_raw
from application.vegetable_catalog_service import load_vegetable_catalog


def find_canonical_vegetable_name(text, confidence_threshold=75):
    catalog = load_vegetable_catalog()
    return find_canonical_vegetable_name_raw(
        text,
        vegetable_aliases=catalog.vegetable_aliases,
        confidence_threshold=confidence_threshold,
    )


def detect_vegetables(
    text,
    return_details=False,
    confidence_threshold=75,
    auto_extract_threshold=90,
    client_name=None,
):
    catalog = load_vegetable_catalog()
    output = detect_vegetables_raw(
        text,
        vegetable_aliases=catalog.vegetable_aliases,
        vegetable_tamil_map=catalog.vegetable_tamil_map,
        noise_line_patterns=catalog.noise_line_patterns,
        return_details=return_details,
        confidence_threshold=confidence_threshold,
        client_name=client_name,
    )

    if return_details:
        items, report = output
        items = apply_confidence_policy(items, auto_extract_threshold=auto_extract_threshold)
        return items, report

    return apply_confidence_policy(output, auto_extract_threshold=auto_extract_threshold)


def detect_vegetables_from_mapped_rows(
    mapped_rows,
    return_details=False,
    confidence_threshold=75,
    auto_extract_threshold=90,
    client_name=None,
):
    catalog = load_vegetable_catalog()
    output = detect_vegetables_from_mapped_rows_raw(
        mapped_rows,
        vegetable_aliases=catalog.vegetable_aliases,
        vegetable_tamil_map=catalog.vegetable_tamil_map,
        return_details=return_details,
        confidence_threshold=confidence_threshold,
        client_name=client_name,
    )

    if return_details:
        items, report = output
        items = apply_confidence_policy(items, auto_extract_threshold=auto_extract_threshold)
        return items, report

    return apply_confidence_policy(output, auto_extract_threshold=auto_extract_threshold)