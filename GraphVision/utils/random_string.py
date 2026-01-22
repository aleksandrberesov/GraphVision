import random
import string

def generate_random_string(length=8, use_digits=True, use_specials=False):
    """
    Generate a random string.

    Args:
        length (int): Length of the string.
        use_digits (bool): Include digits 0-9.
        use_specials (bool): Include special characters.

    Returns:
        str: Randomly generated string.
    """
    chars = string.ascii_letters  # a-z, A-Z
    if use_digits:
        chars += string.digits
    if use_specials:
        chars += string.punctuation

    return ''.join(random.choice(chars) for _ in range(length))