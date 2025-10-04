### Code Generation Examples

**English (default):**
from fastapi_email_auth import generate_code

code = generate_code(2) # "abandon ability"

**Russian with hyphen:**
code = generate_code(2, "russian", "-") # "солнце-река"

**Spanish with 3 words:**
code = generate_code(3, "spanish", "-") # "casa-perro-gato"

**Reusable generator:**
from fastapi_email_auth import BIP39Generator

generator = BIP39Generator("russian")
code1 = generator.generate_code(2, "-")
code2 = generator.generate_code(2, "-")

### Configuration

from fastapi_email_auth import EmailAuthService

#Russian codes with 2 words and hyphen separator
service = EmailAuthService(
code_language="russian",
word_count=2,
code_separator="-",

# ... other params

)
