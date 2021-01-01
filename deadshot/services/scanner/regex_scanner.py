import re
import json
import os
import math
from celery.utils.log import get_task_logger


# This file has function definitions used for matching each PR diff line against
# the defined regular expressions and also check for entropy on secrets identified

logger = get_task_logger(__name__)

BASE64_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
HEX_CHARS = "1234567890abcdefABCDEF"


def run(**kwargs):
    # This function initiates the regular expression match against each line of the PR diff lines
    #  and generates a dictionary item for all positive matches
    diff_line = kwargs["body"]

    issues = []
    temp_issues = {}
    try:
        with open(os.path.join(os.path.dirname(__file__), 'secrets_json/regex.json'), 'r') as f:
            data = json.load(f)
        for title, nested_dict in data.items():
            for regexp in nested_dict["regex"]:
                pattern = re.compile(regexp)
                if bool(pattern.search(str(diff_line))):
                    if nested_dict["entropy_check"] == "True":
                        if find_entropy(diff_line):
                            issues.append({title: nested_dict})
                            if title not in temp_issues.keys():
                                temp_issues[title] = {
                                    "recommendation":
                                        data[title]["recommendation"],
                                    "slack_alert":
                                        data[title]["slack_alert"]
                                }
                    else:
                        issues.append({title: nested_dict})
                        if title not in temp_issues.keys():
                            temp_issues[title] = {
                                "recommendation":
                                    data[title]["recommendation"],
                                "slack_alert":
                                    data[title]["slack_alert"]
                            }

        return temp_issues
    except Exception as e:
        logger.error(e)


def find_entropy(line):
    # Function to calculate the entropy for regexes that have entropy_check
    # set to True in the regex.json file
    high_entropy = False
    stringsFound = []
    for word in line.split():
        base64_strings = get_strings_of_set(word, BASE64_CHARS)
        hex_strings = get_strings_of_set(word, HEX_CHARS)
        for character in base64_strings:
            b64_entropy = shannon_entropy(character, BASE64_CHARS)
            if b64_entropy > 4.5:
                stringsFound.append(character)

        for character in hex_strings:
            hex_entropy = shannon_entropy(character, HEX_CHARS)
            if hex_entropy > 3:
                stringsFound.append(character)

    entropic_diff = {}
    if len(stringsFound) > 0:
        high_entropy = True
        entropic_diff['stringsFound'] = stringsFound

    return high_entropy


def shannon_entropy(data, iterator):
    """
    Borrowed from http://blog.dkbza.org/2007/05/scanning-data-for-entropy-anomalies.html
    """
    if not data:
        return 0
    entropy = 0
    for x in iterator:
        p_x = float(data.count(x))/len(data)
        if p_x > 0:
            entropy += - p_x*math.log(p_x, 2)
    return entropy


def get_strings_of_set(word, char_set, threshold=20):
    count = 0
    letters = ""
    strings = []
    for char in word:
        if char in char_set:
            letters += char
            count += 1
        else:
            if count >= threshold:
                strings.append(letters)
            letters = ""
            count = 0
    if count > threshold:
        strings.append(letters)
    return strings
