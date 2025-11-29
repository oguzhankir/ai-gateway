"""PII detector with fast and detailed modes."""

import time
from typing import List
from app.pii.entities import PIIDetectionResult, PIIEntity, PIIType
from app.pii.patterns import detect_patterns
from app.pii.nlp_models import nlp_models


class PIIDetector:
    """PII detector with fast and detailed modes."""

    def __init__(self):
        self.nlp_models = nlp_models

    def detect(self, text: str, mode: str = "fast") -> PIIDetectionResult:
        """
        Detect PII in text.

        Args:
            text: Text to analyze
            mode: Detection mode ("fast" or "detailed")

        Returns:
            PIIDetectionResult with detected entities
        """
        start_time = time.time()

        if mode == "fast":
            entities = detect_patterns(text)
        else:  # detailed
            entities = self._detect_detailed(text)

        processing_time = (time.time() - start_time) * 1000  # Convert to ms

        return PIIDetectionResult(
            entities=entities,
            mode=mode,
            processing_time_ms=processing_time,
        )

    def _detect_detailed(self, text: str) -> List[PIIEntity]:
        """
        Detailed detection using regex + spaCy NER.

        Args:
            text: Text to analyze

        Returns:
            List of detected PII entities
        """
        # Start with pattern-based detection
        entities = detect_patterns(text)

        # Detect language
        language = self.nlp_models.detect_language(text)

        # Load appropriate model
        if language == "tr":
            nlp = self.nlp_models.get_turkish_model()
        else:
            nlp = self.nlp_models.get_english_model()

        # Run NER
        doc = nlp(text)

        # Map spaCy entities to PII types
        entity_type_map = {
            "PERSON": PIIType.PERSON,
            "ORG": PIIType.ORGANIZATION,
            "GPE": PIIType.LOCATION,
            "LOC": PIIType.LOCATION,
            "MONEY": PIIType.AMOUNT,
            "DATE": PIIType.DATE,
        }

        # Extract NER entities
        for ent in doc.ents:
            pii_type = entity_type_map.get(ent.label_)
            if pii_type:
                # Check if entity overlaps with existing pattern-based entity
                overlaps = False
                for existing in entities:
                    if (
                        existing.start <= ent.start_char < existing.end
                        or existing.start < ent.end_char <= existing.end
                    ):
                        overlaps = True
                        break

                if not overlaps:
                    # Calculate confidence (simple heuristic)
                    confidence = 0.8 if ent.label_ in ["PERSON", "ORG"] else 0.9

                    entities.append(
                        PIIEntity(
                            type=pii_type,
                            text=ent.text,
                            start=ent.start_char,
                            end=ent.end_char,
                            confidence=confidence,
                        )
                    )

        # Sort by start position
        entities.sort(key=lambda e: e.start)

        # Merge overlapping entities (keep higher confidence)
        merged = []
        for entity in entities:
            if not merged:
                merged.append(entity)
                continue

            last = merged[-1]
            if entity.start < last.end:
                # Overlap: keep entity with higher confidence
                if entity.confidence > last.confidence:
                    merged[-1] = entity
            else:
                merged.append(entity)

        return merged


# Singleton instance
pii_detector = PIIDetector()

