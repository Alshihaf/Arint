# tools/validator.py
class Validator:
    def __init__(self):
        pass

    def validate_structure(self, data, expected_keys):
        if not isinstance(data, dict):
            return False
        return all(key in data for key in expected_keys)

    def validate_content_length(self, text, min_length=10, max_length=10000):
        length = len(text.strip())
        return min_length <= length <= max_length

    def validate_no_binary(self, text):
        try:
            text.encode('utf-8').decode('ascii')
            return True
        except UnicodeDecodeError:
            return True
        except:
            return False