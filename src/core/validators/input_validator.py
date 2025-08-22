
class InputValidator:
    def validate_deck_limit(self, limit) -> int:
        # Business rule: type coercion
        if isinstance(limit, str):
            limit = int(limit)
        
        # Business rule: range validation
        if limit < 1 or limit > 10:
            raise ValueError("Limit must be between 1 and 10")
        
        return limit
