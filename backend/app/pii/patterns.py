"""Regex patterns and validation functions for PII detection."""

import re
from typing import List, Tuple, Optional
from app.pii.entities import PIIEntity, PIIType


# Regex patterns for Turkish formats
TCKN_PATTERN = re.compile(r"\b\d{11}\b")
PHONE_PATTERN = re.compile(r"(\+90\s?)?(\(?\d{3}\)?[\s.-]?)?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}\b")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
IBAN_PATTERN = re.compile(r"\bTR\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2}\b")
CREDIT_CARD_PATTERN = re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b")
AMOUNT_PATTERN = re.compile(r"\b\d+[.,]\d{2}\s*(TL|TRY|USD|EUR|GBP)\b", re.IGNORECASE)


def validate_tckn(tckn: str) -> bool:
    """
    Validate Turkish ID number (TCKN) using checksum algorithm.

    Args:
        tckn: TCKN string

    Returns:
        True if valid, False otherwise
    """
    if len(tckn) != 11 or not tckn.isdigit():
        return False

    digits = [int(d) for d in tckn]

    # First 10 digits sum check
    sum_first_10 = sum(digits[:10])
    if sum_first_10 % 10 != digits[10]:
        return False

    # Odd and even position checks
    odd_sum = sum(digits[0:9:2])
    even_sum = sum(digits[1:9:2])
    check_digit = (odd_sum * 7 - even_sum) % 10
    if check_digit < 0:
        check_digit += 10

    return check_digit == digits[9]


def validate_iban(iban: str) -> bool:
    """
    Validate IBAN using checksum algorithm.

    Args:
        iban: IBAN string

    Returns:
        True if valid, False otherwise
    """
    # Remove spaces
    iban = iban.replace(" ", "").upper()

    if len(iban) < 4:
        return False

    # Move first 4 characters to end
    rearranged = iban[4:] + iban[:4]

    # Replace letters with numbers (A=10, B=11, ..., Z=35)
    numeric = ""
    for char in rearranged:
        if char.isdigit():
            numeric += char
        elif char.isalpha():
            numeric += str(ord(char) - ord("A") + 10)
        else:
            return False

    # Calculate mod 97
    remainder = int(numeric) % 97
    return remainder == 1


def luhn_check(card_number: str) -> bool:
    """
    Validate credit card number using Luhn algorithm.

    Args:
        card_number: Credit card number string

    Returns:
        True if valid, False otherwise
    """
    # Remove spaces and dashes
    card_number = re.sub(r"[\s-]", "", card_number)

    if not card_number.isdigit():
        return False

    digits = [int(d) for d in card_number]
    digits.reverse()

    total = 0
    for i, digit in enumerate(digits):
        if i % 2 == 1:
            doubled = digit * 2
            total += doubled if doubled < 10 else doubled - 9
        else:
            total += digit

    return total % 10 == 0


def find_pattern_matches(text: str, pattern: re.Pattern, pii_type: PIIType) -> List[PIIEntity]:
    """
    Find pattern matches in text.

    Args:
        text: Text to search
        pattern: Regex pattern
        pii_type: PII type

    Returns:
        List of PIIEntity instances
    """
    entities = []
    for match in pattern.finditer(text):
        entity_text = match.group()
        
        # Validate based on type
        is_valid = True
        if pii_type == PIIType.TCKN:
            is_valid = validate_tckn(entity_text)
        elif pii_type == PIIType.IBAN:
            is_valid = validate_iban(entity_text)
        elif pii_type == PIIType.CREDIT_CARD:
            is_valid = luhn_check(entity_text)

        if is_valid:
            entities.append(
                PIIEntity(
                    type=pii_type,
                    text=entity_text,
                    start=match.start(),
                    end=match.end(),
                    confidence=1.0,
                )
            )

    return entities


def detect_patterns(text: str) -> List[PIIEntity]:
    """
    Detect PII using regex patterns.

    Args:
        text: Text to analyze

    Returns:
        List of detected PII entities
    """
    entities = []

    # TCKN
    entities.extend(find_pattern_matches(text, TCKN_PATTERN, PIIType.TCKN))

    # Phone
    entities.extend(find_pattern_matches(text, PHONE_PATTERN, PIIType.PHONE))

    # Email
    entities.extend(find_pattern_matches(text, EMAIL_PATTERN, PIIType.EMAIL))

    # IBAN
    entities.extend(find_pattern_matches(text, IBAN_PATTERN, PIIType.IBAN))

    # Credit Card
    entities.extend(find_pattern_matches(text, CREDIT_CARD_PATTERN, PIIType.CREDIT_CARD))

    # Amount
    entities.extend(find_pattern_matches(text, AMOUNT_PATTERN, PIIType.AMOUNT))

    # Remove duplicates (same position)
    seen = set()
    unique_entities = []
    for entity in entities:
        key = (entity.start, entity.end, entity.type)
        if key not in seen:
            seen.add(key)
            unique_entities.append(entity)

    return unique_entities

