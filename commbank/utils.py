import re


def strip_spaces(text: str):
    return re.sub(" +", " ", text)


def capitalize(text):
    return text[0].upper() + text[1:]
