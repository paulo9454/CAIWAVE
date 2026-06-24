"""
CAIWAVE Kenya Locations Data
Counties and constituencies for coverage targeting.
"""
from typing import List


KENYA_LOCATIONS = {
    "Nairobi": [
        "Westlands", "Dagoretti North", "Dagoretti South", "Langata", 
        "Kibra", "Roysambu", "Kasarani", "Ruaraka", "Embakasi South",
        "Embakasi North", "Embakasi Central", "Embakasi East", "Embakasi West",
        "Makadara", "Kamukunji", "Starehe", "Mathare"
    ],
    "Mombasa": [
        "Changamwe", "Jomvu", "Kisauni", "Nyali", "Likoni", "Mvita"
    ],
    "Kisumu": [
        "Kisumu East", "Kisumu West", "Kisumu Central", "Seme", "Nyando", 
        "Muhoroni", "Nyakach"
    ],
    "Nakuru": [
        "Nakuru Town East", "Nakuru Town West", "Naivasha", "Gilgil", 
        "Subukia", "Rongai", "Bahati", "Molo", "Kuresoi South", "Kuresoi North", "Njoro"
    ],
    "Kiambu": [
        "Gatundu South", "Gatundu North", "Juja", "Thika Town", "Ruiru",
        "Githunguri", "Kiambu", "Kiambaa", "Kabete", "Kikuyu", "Limuru", "Lari"
    ],
    "Machakos": [
        "Masinga", "Yatta", "Kangundo", "Matungulu", "Kathiani", "Mavoko",
        "Machakos Town", "Mwala"
    ],
    "Kajiado": [
        "Kajiado North", "Kajiado Central", "Kajiado East", "Kajiado West", "Kajiado South"
    ],
    "Uasin Gishu": [
        "Soy", "Turbo", "Moiben", "Ainabkoi", "Kapseret", "Kesses"
    ],
    "Trans Nzoia": [
        "Kwanza", "Endebess", "Saboti", "Kiminini", "Cherangany"
    ],
    "Kakamega": [
        "Lugari", "Likuyani", "Malava", "Lurambi", "Navakholo", "Mumias West",
        "Mumias East", "Matungu", "Butere", "Khwisero", "Shinyalu", "Ikolomani"
    ],
    "Bungoma": [
        "Mount Elgon", "Sirisia", "Kabuchai", "Bumula", "Kanduyi", 
        "Webuye East", "Webuye West", "Kimilili", "Tongaren"
    ],
    "Nyeri": [
        "Tetu", "Kieni", "Mathira", "Othaya", "Mukurweini", "Nyeri Town"
    ],
    "Meru": [
        "North Imenti", "South Imenti", "Central Imenti", "Tigania West",
        "Tigania East", "Igembe South", "Igembe Central", "Igembe North", "Buuri"
    ],
    "Kilifi": [
        "Kilifi North", "Kilifi South", "Kaloleni", "Rabai", "Ganze", "Malindi", "Magarini"
    ],
    "Kwale": [
        "Msambweni", "Lunga Lunga", "Matuga", "Kinango"
    ],
    "Turkana": [
        "Turkana North", "Turkana West", "Turkana Central", "Loima", 
        "Turkana South", "Turkana East"
    ],
    "Garissa": [
        "Garissa Township", "Balambala", "Lagdera", "Dadaab", "Fafi", "Ijara"
    ],
    "Wajir": [
        "Wajir North", "Wajir East", "Tarbaj", "Wajir West", "Eldas", "Wajir South"
    ],
    "Mandera": [
        "Mandera West", "Banissa", "Mandera North", "Mandera South", "Mandera East", "Lafey"
    ]
}


def get_all_counties() -> List[str]:
    """Get all Kenya counties."""
    return list(KENYA_LOCATIONS.keys())


def get_constituencies(county: str) -> List[str]:
    """Get constituencies for a county."""
    return KENYA_LOCATIONS.get(county, [])


def get_all_constituencies() -> List[dict]:
    """Get all constituencies with their counties."""
    result = []
    for county, constituencies in KENYA_LOCATIONS.items():
        for const in constituencies:
            result.append({"county": county, "constituency": const})
    return result
