# tools/binary_string.py
import json

class BinaryString:

    @staticmethod
    def encode(text: str, sep: str = ' ') -> str:
        return sep.join(format(ord(c), '08b') for c in text)

    @staticmethod
    def decode(binary_str: str, sep: str = ' ') -> str:
        try:
            bits = [b for b in binary_str.split(sep) if b]
            chars = [chr(int(b, 2)) for b in bits]
            return ''.join(chars)
        except Exception as e:
            return f"[DECODE ERROR: {e}]"

    @staticmethod
    def to_python(binary_str: str) -> str:
        return BinaryString.decode(binary_str)

    @staticmethod
    def to_json(binary_str: str) -> str:
        text = BinaryString.decode(binary_str)
        try:
            parsed = json.loads(text)
            return json.dumps(parsed, indent=2)
        except json.JSONDecodeError:
            return text

    @staticmethod
    def to_markdown(binary_str: str) -> str:
        return BinaryString.decode(binary_str)

    @staticmethod
    def to_html(binary_str: str) -> str:
        return BinaryString.decode(binary_str)

    @staticmethod
    def to_text(binary_str: str) -> str:
        return BinaryString.decode(binary_str)

    @staticmethod
    def to_format(binary_str: str, format: str) -> str:
        if format == 'py':
            return BinaryString.to_python(binary_str)
        elif format == 'json':
            return BinaryString.to_json(binary_str)
        elif format == 'md':
            return BinaryString.to_markdown(binary_str)
        elif format == 'html':
            return BinaryString.to_html(binary_str)
        else:
            return BinaryString.to_text(binary_str)