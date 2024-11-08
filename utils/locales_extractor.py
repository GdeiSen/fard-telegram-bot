class DictExtractor:
    def __init__(self, data: dict[str, dict[str, str]]):
        self.data: dict[str, dict[str, str]] = data
        self.group: str = 'RU'
        
    def get(self, key: str, content: list[str] | None = None, group: None | str = None) -> str | None:
        # Use the provided group or default to the instance's group
        group = group or self.group
        
        # Retrieve group data
        group_data: dict[str, str] = self.data.get(group, {})
        
        # Retrieve the text for the given key
        text = group_data.get(key)
        
        if text is None:
            return key

        # Replace placeholders `{?}` with content items
        if content:
            for fill in content:
                text = text.replace('{?}', fill, 1)
        
        return text
