def check_char_preservation(original, modified):
    if len(original) - 2 != len(modified):
        return False
    
    for i in range(1, len(original) - 1):
        if original[i] != modified[i - 1]:
            return False

    return True

def remove_extra_quotes(s):
    if s.startswith("'\"") and s.endswith("\"'"):
        modified_string = s[1:-1]
        
        if check_char_preservation(s, modified_string):
            return modified_string

    return s

text_with_extra_quotes = "hello world"
text_without_extra_quotes = remove_extra_quotes(text_with_extra_quotes)


import re

pattern = r'^(?<!\')"([^"]*)"(?!\')$'

# This will match
test_string1 = '"hello world"'

# This will not match
test_string2 = '\'"hello world"\''

match1 = re.match(pattern, test_string1)
match2 = re.match(pattern, test_string2)

print(match1.group(1) if match1 else "No match")  # Output: hello world
print(match2.group(1) if match2 else "No match")  # Output: No match



print(text_without_extra_quotes)
