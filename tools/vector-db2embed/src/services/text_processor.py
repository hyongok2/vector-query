"""Text processing and chunking service"""
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
from jinja2 import Template, TemplateError
import pandas as pd


class TextProcessorInterface(ABC):
    """Abstract interface for text processing"""

    @abstractmethod
    def build_text_documents(
        self,
        df: pd.DataFrame,
        template: str,
        pk_column: str,
        max_chars: int = 1000,
        strip_whitespace: bool = True
    ) -> List[Dict[str, Any]]:
        """Build text documents from DataFrame"""
        pass


class TextChunker:
    """Text chunking utilities"""

    @staticmethod
    def chunk_text(text: str, max_chars: int) -> List[str]:
        """Split text into chunks of max_chars size"""
        if not text or max_chars <= 0:
            return []

        text = text.strip()
        if len(text) <= max_chars:
            return [text]

        chunks = []
        # Try to split on sentences first
        sentences = re.split(r'[.!?]+', text)

        current_chunk = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # If adding this sentence would exceed max_chars
            if len(current_chunk) + len(sentence) + 1 > max_chars:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    # Single sentence is too long, split by chars
                    chunks.extend(TextChunker._split_by_chars(sentence, max_chars))
            else:
                if current_chunk:
                    current_chunk += ". " + sentence
                else:
                    current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk.strip())

        return [chunk for chunk in chunks if chunk.strip()]

    @staticmethod
    def _split_by_chars(text: str, max_chars: int) -> List[str]:
        """Split text by characters when no good sentence breaks exist"""
        chunks = []
        for i in range(0, len(text), max_chars):
            chunk = text[i:i + max_chars].strip()
            if chunk:
                chunks.append(chunk)
        return chunks


class TemplateRenderer:
    """Jinja2 template rendering utilities"""

    @staticmethod
    def render_template(template_str: str, row_data: Dict[str, Any]) -> str:
        """Render Jinja2 template with row data"""
        try:
            template = Template(template_str)
            return template.render(**row_data)
        except TemplateError as e:
            raise TextProcessingError(f"Template rendering failed: {e}")
        except Exception as e:
            raise TextProcessingError(f"Unexpected template error: {e}")

    @staticmethod
    def validate_template(template_str: str, sample_data: Dict[str, Any]) -> bool:
        """Validate template with sample data"""
        try:
            TemplateRenderer.render_template(template_str, sample_data)
            return True
        except Exception:
            return False


class TextProcessor(TextProcessorInterface):
    """Main text processing implementation"""

    def __init__(self):
        self.chunker = TextChunker()
        self.renderer = TemplateRenderer()

    def build_text_documents(
        self,
        df: pd.DataFrame,
        template: str,
        pk_column: str,
        max_chars: int = 1000,
        strip_whitespace: bool = True
    ) -> List[Dict[str, Any]]:
        """Build text documents from DataFrame with chunking"""
        if df.empty:
            return []

        if pk_column not in df.columns:
            raise TextProcessingError(f"PK column '{pk_column}' not found in DataFrame")

        documents = []

        for row_index, row in df.iterrows():
            try:
                # Convert row to dict for template rendering
                row_dict = row.to_dict()

                # Render template
                text = self.renderer.render_template(template, row_dict)

                if strip_whitespace:
                    text = self._clean_whitespace(text)

                if not text.strip():
                    continue  # Skip empty texts

                # Get PK value
                pk_value = row_dict[pk_column]

                # Chunk text
                chunks = self.chunker.chunk_text(text, max_chars)

                # Create document for each chunk
                for chunk_index, chunk in enumerate(chunks):
                    # Convert source_row to JSON string for type safety
                    # This prevents numpy/pandas type serialization issues with Qdrant
                    source_row_json = json.dumps(row_dict, default=str, ensure_ascii=False)

                    documents.append({
                        "text": chunk,
                        "pk": pk_value,
                        "chunk_index": chunk_index,
                        "row_index": int(row_index),
                        "source_row": source_row_json
                    })

            except Exception as e:
                # Log error but continue processing other rows
                print(f"Error processing row {row_index}: {e}")
                continue

        return documents

    def _clean_whitespace(self, text: str) -> str:
        """Clean excessive whitespace from text"""
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        return text.strip()


class TextProcessingError(Exception):
    """Text processing error"""
    pass


class TextProcessorFactory:
    """Factory for creating text processors"""

    @staticmethod
    def create_processor() -> TextProcessorInterface:
        """Create text processor instance"""
        return TextProcessor()


class TemplateValidator:
    """Template validation utilities"""

    @staticmethod
    def validate_template_syntax(template_str: str) -> Tuple[bool, Optional[str]]:
        """Validate Jinja2 template syntax"""
        try:
            Template(template_str)
            return True, None
        except TemplateError as e:
            return False, str(e)

    @staticmethod
    def get_template_variables(template_str: str) -> List[str]:
        """Extract variable names from template"""
        try:
            template = Template(template_str)
            return list(template.get_corresponding_lineno(template_str))
        except Exception:
            # Fallback: simple regex extraction
            import re
            variables = re.findall(r'\{\{\s*(\w+)', template_str)
            return list(set(variables))

    @staticmethod
    def check_template_compatibility(template_str: str, column_names: List[str]) -> Tuple[bool, List[str]]:
        """Check if template variables match available columns"""
        try:
            template_vars = TemplateValidator.get_template_variables(template_str)
            missing_vars = [var for var in template_vars if var not in column_names]
            return len(missing_vars) == 0, missing_vars
        except Exception:
            return False, []