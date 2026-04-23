import pytest


class TestContentSplitting:

    def test_split_content_small(self):
        """Conteúdo pequeno não deve ser dividido"""
        from app.routes import split_content_into_parts

        content = "Texto curto"
        parts = split_content_into_parts(content, max_chars=10000)

        assert len(parts) == 1
        assert parts[0]["content"] == "Texto curto"
        assert parts[0]["part_index"] == 0

    def test_split_content_large(self):
        """Conteúdo grande deve ser dividido"""
        from app.routes import split_content_into_parts

        content = "A" * 25000
        parts = split_content_into_parts(content, max_chars=10000)

        assert len(parts) == 3
        assert parts[0]["content"] == "A" * 10000
        assert parts[1]["content"] == "A" * 10000
        assert parts[2]["content"] == "A" * 5000
        assert parts[0]["part_index"] == 0
        assert parts[1]["part_index"] == 1
        assert parts[2]["part_index"] == 2

    def test_split_content_shows_metadata(self):
        """Cada parte deve ter metadados corretos"""
        from app.routes import split_content_into_parts

        content = "X" * 25000
        parts = split_content_into_parts(content, max_chars=10000)

        for part in parts:
            assert "part_index" in part
            assert "content" in part
            assert "char_count" in part
            assert "total_parts" in part

    def test_split_content_exact_boundary(self):
        """Conteúdo exatamente no limite não deve ser dividido"""
        from app.routes import split_content_into_parts

        content = "B" * 10000
        parts = split_content_into_parts(content, max_chars=10000)

        assert len(parts) == 1

    def test_split_content_empty(self):
        """Conteúdo vazio retorna lista vazia"""
        from app.routes import split_content_into_parts

        content = ""
        parts = split_content_into_parts(content, max_chars=10000)

        assert len(parts) == 0