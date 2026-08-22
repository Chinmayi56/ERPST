"""
Small reusable validation helpers.
"""
import re

MOBILE_REGEX = re.compile(r"^[6-9]\d{9}$")  # 10-digit Indian mobile format


def is_valid_mobile(mobile: str) -> bool:
    if not mobile:
        return False
    return bool(MOBILE_REGEX.match(mobile.strip()))


def is_valid_otp(otp: str) -> bool:
    return bool(otp) and otp.strip().isdigit() and len(otp.strip()) == 6
