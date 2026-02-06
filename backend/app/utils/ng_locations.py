# Nigeria state -> cities dataset (curated from Britannica list of cities and towns in Nigeria)

NIGERIA_LOCATIONS = [
    {"state": "Abia", "cities": ["Aba", "Arochukwu", "Umuahia"]},
    {"state": "Adamawa", "cities": ["Jimeta", "Mubi", "Numan", "Yola"]},
    {"state": "Akwa Ibom", "cities": ["Ikot Abasi", "Ikot Ekpene", "Oron", "Uyo"]},
    {"state": "Anambra", "cities": ["Awka", "Onitsha"]},
    {"state": "Bauchi", "cities": ["Azare", "Bauchi", "Jama'are", "Katagum", "Misau"]},
    {"state": "Bayelsa", "cities": ["Brass", "Yenagoa"]},
    {"state": "Benue", "cities": ["Makurdi"]},
    {"state": "Borno", "cities": ["Biu", "Dikwa", "Maiduguri"]},
    {"state": "Cross River", "cities": ["Calabar", "Ogoja"]},
    {"state": "Delta", "cities": ["Asaba", "Burutu", "Koko", "Sapele", "Ughelli", "Warri"]},
    {"state": "Ebonyi", "cities": ["Abakaliki"]},
    {"state": "Edo", "cities": ["Benin City"]},
    {"state": "Ekiti", "cities": ["Ado-Ekiti", "Effon-Alaiye", "Ikere-Ekiti"]},
    {"state": "Enugu", "cities": ["Enugu", "Nsukka"]},
    {"state": "FCT", "cities": ["Abuja"]},
    {"state": "Gombe", "cities": ["Deba Habe", "Gombe", "Kumo"]},
    {"state": "Imo", "cities": ["Owerri"]},
    {"state": "Jigawa", "cities": ["Birnin Kudu", "Dutse", "Gumel", "Hadejia", "Kazaure"]},
    {"state": "Kaduna", "cities": ["Jemaa", "Kaduna", "Zaria"]},
    {"state": "Kano", "cities": ["Kano"]},
    {"state": "Katsina", "cities": ["Daura", "Katsina"]},
    {"state": "Kebbi", "cities": ["Argungu", "Birnin Kebbi", "Gwandu", "Yelwa"]},
    {"state": "Kogi", "cities": ["Idah", "Kabba", "Lokoja", "Okene"]},
    {"state": "Kwara", "cities": ["Ilorin", "Jebba", "Lafiagi", "Offa", "Pategi"]},
    {"state": "Lagos", "cities": ["Badagry", "Epe", "Ikeja", "Ikorodu", "Lagos", "Lekki", "Mushin", "Shomolu", "Victoria Island"]},
    {"state": "Nasarawa", "cities": ["Keffi", "Lafia", "Nasarawa"]},
    {"state": "Niger", "cities": ["Agaie", "Baro", "Bida", "Kontagora", "Lapai", "Minna", "Suleja"]},
    {"state": "Ogun", "cities": ["Abeokuta", "Ijebu-Ode", "Ilaro", "Shagamu"]},
    {"state": "Ondo", "cities": ["Akure", "Ikare", "Oka-Akoko", "Ondo", "Owo"]},
    {"state": "Osun", "cities": ["Ede", "Ikire", "Ikirun", "Ila", "Ile-Ife", "Ilesha", "Ilobu", "Inisa", "Iwo", "Oshogbo"]},
    {"state": "Oyo", "cities": ["Ibadan", "Iseyin", "Ogbomosho", "Oyo", "Saki"]},
    {"state": "Plateau", "cities": ["Bukuru", "Jos", "Vom", "Wase"]},
    {"state": "Rivers", "cities": ["Bonny", "Degema", "Okrika", "Port Harcourt"]},
    {"state": "Sokoto", "cities": ["Sokoto"]},
    {"state": "Taraba", "cities": ["Ibi", "Jalingo", "Muri"]},
    {"state": "Yobe", "cities": ["Damaturu", "Nguru"]},
    {"state": "Zamfara", "cities": ["Gusau", "Kaura Namoda"]},
]


# -------------------------------------------------------------------
# Helpers (single source of truth for demo seeds + validation)
# -------------------------------------------------------------------

CITY_COORDS = {
    "Ikeja": (6.6018, 3.3515),
    "Lagos": (6.4550, 3.3841),
    "Ikorodu": (6.6157, 3.5079),
    "Lekki": (6.4698, 3.5852),
    "Victoria Island": (6.4281, 3.4219),
    "Abuja": (9.0765, 7.3986),
    "Ibadan": (7.3775, 3.9470),
    "Port Harcourt": (4.8156, 7.0498),
    "Kano": (12.0022, 8.5919),
}

_STATE_TO_CITIES = {row.get("state"): set(row.get("cities") or []) for row in (NIGERIA_LOCATIONS or [])}


def normalize_state(value: str | None) -> str | None:
    if not value:
        return None
    v = str(value).strip()
    return v or None


def normalize_city(value: str | None) -> str | None:
    if not value:
        return None
    v = str(value).strip()
    return v or None


def is_valid_state(state: str | None) -> bool:
    s = normalize_state(state)
    return bool(s and s in _STATE_TO_CITIES)


def is_valid_city(state: str | None, city: str | None) -> bool:
    s = normalize_state(state)
    c = normalize_city(city)
    if not s or not c:
        return False
    return c in (_STATE_TO_CITIES.get(s) or set())


def get_city_coords(city: str | None):
    c = normalize_city(city)
    if not c:
        return None
    return CITY_COORDS.get(c)
