"""
Unit tests for core interface classes and data structures.

Tests the fundamental data structures (PrimerData, AmpliconData) and
abstract base classes that form the foundation of PrePrimer.
"""

from preprimer.core.interfaces import AmpliconData, PrimerData


class TestPrimerData:
    """Test the PrimerData dataclass."""

    def test_primer_data_creation(self):
        """Test basic PrimerData creation and properties."""
        primer = PrimerData(
            name="test_primer",
            sequence="ATCGATCGATCG",
            start=100,
            stop=112,
            strand="+",
            direction="forward",
            amplicon_id="amplicon_1",
            reference_id="test_ref",
        )

        assert primer.name == "test_primer"
        assert primer.sequence == "ATCGATCGATCG"
        assert primer.start == 100
        assert primer.stop == 112
        assert primer.strand == "+"
        assert primer.direction == "forward"
        assert primer.amplicon_id == "amplicon_1"
        assert primer.reference_id == "test_ref"
        assert primer.length == 12

    def test_primer_artic_name(self):
        """Test ARTIC name generation."""
        primer = PrimerData(
            name="test_primer",
            sequence="ATCGATCGATCG",
            start=100,
            stop=112,
            strand="+",
            direction="forward",
            amplicon_id="amplicon_1",
            reference_id="test_ref",
        )

        assert primer.artic_name == "test_ref_1_LEFT_0"

    def test_primer_artic_name_reverse(self):
        """Test ARTIC name generation for reverse primer."""
        primer = PrimerData(
            name="test_primer",
            sequence="CGATCGATCGAT",
            start=200,
            stop=212,
            strand="-",
            direction="reverse",
            amplicon_id="amplicon_2",
            reference_id="test_ref",
        )

        assert primer.artic_name == "test_ref_2_RIGHT_0"

    def test_primer_optional_fields(self):
        """Test PrimerData with optional quality metrics."""
        primer = PrimerData(
            name="test_primer",
            sequence="ATCGATCGATCG",
            start=100,
            stop=112,
            strand="+",
            direction="forward",
            amplicon_id="amplicon_1",
            reference_id="test_ref",
            gc_content=50.0,
            tm=60.0,
            score=0.95,
            pool=2,
        )

        assert primer.gc_content == 50.0
        assert primer.tm == 60.0
        assert primer.score == 0.95
        assert primer.pool == 2

    def test_primer_metadata(self):
        """Test PrimerData metadata handling."""
        metadata = {"custom_field": "value", "score_alt": 0.8}
        primer = PrimerData(
            name="test_primer",
            sequence="ATCGATCGATCG",
            start=100,
            stop=112,
            strand="+",
            direction="forward",
            amplicon_id="amplicon_1",
            reference_id="test_ref",
            metadata=metadata,
        )

        assert primer.metadata == metadata
        assert primer.metadata["custom_field"] == "value"

    def test_primer_defaults(self):
        """Test PrimerData default values."""
        primer = PrimerData(
            name="test_primer",
            sequence="ATCGATCGATCG",
            start=100,
            stop=112,
            strand="+",
            direction="forward",
        )

        assert primer.pool is None
        assert primer.amplicon_id == ""
        assert primer.reference_id == ""
        assert primer.gc_content is None
        assert primer.tm is None
        assert primer.score is None
        assert primer.metadata == {}


class TestAmpliconData:
    """Test the AmpliconData dataclass."""

    def test_amplicon_data_creation(self):
        """Test basic AmpliconData creation."""
        primer1 = PrimerData("p1", "ATCG", 100, 104, "+", "forward", amplicon_id="amp1")
        primer2 = PrimerData("p2", "CGAT", 200, 204, "-", "reverse", amplicon_id="amp1")

        amplicon = AmpliconData("amp1", [primer1, primer2])

        assert amplicon.amplicon_id == "amp1"
        assert len(amplicon.primers) == 2
        assert amplicon.primers[0] == primer1
        assert amplicon.primers[1] == primer2

    def test_amplicon_forward_primers(self):
        """Test forward primer filtering."""
        primer1 = PrimerData("p1", "ATCG", 100, 104, "+", "forward", amplicon_id="amp1")
        primer2 = PrimerData("p2", "CGAT", 200, 204, "-", "reverse", amplicon_id="amp1")
        primer3 = PrimerData("p3", "GCTA", 150, 154, "+", "forward", amplicon_id="amp1")

        amplicon = AmpliconData("amp1", [primer1, primer2, primer3])

        forward_primers = amplicon.forward_primers
        assert len(forward_primers) == 2
        assert primer1 in forward_primers
        assert primer3 in forward_primers
        assert primer2 not in forward_primers

    def test_amplicon_reverse_primers(self):
        """Test reverse primer filtering."""
        primer1 = PrimerData("p1", "ATCG", 100, 104, "+", "forward", amplicon_id="amp1")
        primer2 = PrimerData("p2", "CGAT", 200, 204, "-", "reverse", amplicon_id="amp1")
        primer3 = PrimerData("p3", "GCTA", 250, 254, "-", "reverse", amplicon_id="amp1")

        amplicon = AmpliconData("amp1", [primer1, primer2, primer3])

        reverse_primers = amplicon.reverse_primers
        assert len(reverse_primers) == 2
        assert primer2 in reverse_primers
        assert primer3 in reverse_primers
        assert primer1 not in reverse_primers

    def test_amplicon_primer_pairs(self):
        """Test primer pair generation."""
        fwd1 = PrimerData("f1", "ATCG", 100, 104, "+", "forward", amplicon_id="amp1")
        fwd2 = PrimerData("f2", "GCTA", 110, 114, "+", "forward", amplicon_id="amp1")
        rev1 = PrimerData("r1", "CGAT", 200, 204, "-", "reverse", amplicon_id="amp1")
        rev2 = PrimerData("r2", "TACG", 210, 214, "-", "reverse", amplicon_id="amp1")

        amplicon = AmpliconData("amp1", [fwd1, fwd2, rev1, rev2])

        pairs = amplicon.get_primer_pairs()
        assert len(pairs) == 4  # 2 forward × 2 reverse

        # Check all combinations are present
        expected_pairs = [(fwd1, rev1), (fwd1, rev2), (fwd2, rev1), (fwd2, rev2)]

        for expected_pair in expected_pairs:
            assert expected_pair in pairs

    def test_amplicon_optional_fields(self):
        """Test AmpliconData optional fields."""
        primer1 = PrimerData("p1", "ATCG", 100, 104, "+", "forward", amplicon_id="amp1")

        amplicon = AmpliconData(
            amplicon_id="amp1",
            primers=[primer1],
            length=500,
            reference_id="ref1",
            metadata={"custom": "data"},
        )

        assert amplicon.length == 500
        assert amplicon.reference_id == "ref1"
        assert amplicon.metadata == {"custom": "data"}

    def test_amplicon_defaults(self):
        """Test AmpliconData default values."""
        primer1 = PrimerData("p1", "ATCG", 100, 104, "+", "forward", amplicon_id="amp1")
        amplicon = AmpliconData("amp1", [primer1])

        assert amplicon.length is None
        assert amplicon.reference_id == ""
        assert amplicon.metadata == {}

    def test_empty_amplicon(self):
        """Test amplicon with no primers."""
        amplicon = AmpliconData("empty", [])

        assert len(amplicon.primers) == 0
        assert len(amplicon.forward_primers) == 0
        assert len(amplicon.reverse_primers) == 0
        assert len(amplicon.get_primer_pairs()) == 0


class TestDataStructureIntegration:
    """Test integration between data structures."""

    def test_primer_amplicon_consistency(self):
        """Test that primer and amplicon IDs are consistent."""
        primer1 = PrimerData("p1", "ATCG", 100, 104, "+", "forward", amplicon_id="amp1")
        primer2 = PrimerData("p2", "CGAT", 200, 204, "-", "reverse", amplicon_id="amp1")

        amplicon = AmpliconData("amp1", [primer1, primer2])

        for primer in amplicon.primers:
            assert primer.amplicon_id == amplicon.amplicon_id

    def test_multiple_amplicons(self):
        """Test handling multiple amplicons with different primers."""
        # Amplicon 1
        p1_f = PrimerData("p1_f", "ATCG", 100, 104, "+", "forward", amplicon_id="amp1")
        p1_r = PrimerData("p1_r", "CGAT", 200, 204, "-", "reverse", amplicon_id="amp1")
        amp1 = AmpliconData("amp1", [p1_f, p1_r])

        # Amplicon 2
        p2_f = PrimerData("p2_f", "GCTA", 300, 304, "+", "forward", amplicon_id="amp2")
        p2_r = PrimerData("p2_r", "TACG", 400, 404, "-", "reverse", amplicon_id="amp2")
        amp2 = AmpliconData("amp2", [p2_f, p2_r])

        amplicons = [amp1, amp2]

        assert len(amplicons) == 2
        assert amplicons[0].amplicon_id == "amp1"
        assert amplicons[1].amplicon_id == "amp2"
        assert len(amplicons[0].primers) == 2
        assert len(amplicons[1].primers) == 2

    def test_complex_amplicon_structure(self):
        """Test amplicon with multiple primers per direction."""
        # Multiple forward primers
        f1 = PrimerData(
            "f1", "ATCGATCG", 100, 108, "+", "forward", amplicon_id="complex"
        )
        f2 = PrimerData(
            "f2", "ATCGATCC", 105, 113, "+", "forward", amplicon_id="complex"
        )
        f3 = PrimerData(
            "f3", "ATCGATCT", 110, 118, "+", "forward", amplicon_id="complex"
        )

        # Multiple reverse primers
        r1 = PrimerData(
            "r1", "CGATCGAT", 400, 408, "-", "reverse", amplicon_id="complex"
        )
        r2 = PrimerData(
            "r2", "GGATCGAT", 405, 413, "-", "reverse", amplicon_id="complex"
        )

        amplicon = AmpliconData("complex", [f1, f2, f3, r1, r2])

        assert len(amplicon.primers) == 5
        assert len(amplicon.forward_primers) == 3
        assert len(amplicon.reverse_primers) == 2
        assert len(amplicon.get_primer_pairs()) == 6  # 3 × 2 combinations
