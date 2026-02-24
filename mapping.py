# mapping.py

VINYEAR_map = {
    "1": "2001", "2": "2002", "3": "2003", "4": "2004", "5": "2005",
    "6": "2006", "7": "2007", "8": "2008", "9": "2009", "A": "2010",
    "B": "2011", "C": "2012", "D": "2013", "E": "2014", "F": "2015",
    "G": "2016", "H": "2017", "J": "2018", "K": "2019", "L": "2020",
    "M": "2021", "N": "2022", "P": "2023", "R": "2024", "S": "2025",
    "T": "2026", "V": "2027",
}

COLOR_map = {
    "silver gray": "GRAY", "Silver gray": "GRAY", "sable": "BLACK", 
    "rat color": "GRAY", "pearl gray": "WHITE", "mouse gray": "GRAY",
    "흰색": "WHITE", "검정색": "BLACK", "빨간색": "RED", 
    "쥐색": "GRAY", "주황색": "ORANGE"
}

ADDRESS_REGION_MAP = {
    "서울": "서울", "인천": "인천", "김포": "김포", "양주": "양주",
    "용인": "용인", "광명": "광명", "의정부": "의정부", "부천": "부천",
    "수원": "수원", "부산": "부산", "대구": "대구", "대전": "대전",
    "울산": "울산", "세종": "세종", "춘천": "춘천", "청주": "청주",
    "천안": "천안", "전주": "전주", "순천": "순천", "포항": "포항",
    "경주": "경주", "창원": "창원", "진주": "진주", "양산": "양산", "광주": "광주"
}
def get_region_from_address(address):
    """주소 문자열에서 매핑된 지역명을 찾아 반환"""
    if not address:
        return ""
    
    for keyword, region_name in ADDRESS_REGION_MAP.items():
        if keyword in address:
            return region_name
    return ""
    
COUNTRY_PORT_MAP = {
    "AB": ["DURRES , ALBANIA"],
    "GR": ["PIRAEUS, GREECE"],
    "HN": ["SAN LORENZO, HONDURAS"],
    "CL": ["IQUIQUE, CHILE"],
    "PY": ["ASUNCION, PARAGUAY"],
    "SV": ["LA UNION, EL SALVADOR"],
    "UA": ["CHORNOMORSK, UKRAINE"],
    "AO": ["LUANDA, ANGOLA"],
    "UZ": ["TASHKENT, UZBEKISTAN"],
    "GE": ["POTI, GEORGIA"],
    "CR": ["LIMON, COSTA RICA", "Puerto Caldera, COSTA RICA"],
    "DJ": ["DJIBOUTI, DJIBOUTI"],
    "RU": ["VLADIVOSTOK, RUSSIA"],
    "KG": ["BISHKEK, KYRGYZSTAN"],
    "GT": ["QUETZAL, GUATEMALA"],
    "DZ": ["ALGIERS, ALGERIA"],
    "DR": ["CAUCEDO, DOMINICAN REP.", "RIO HAINA, DOMINICAN REP.", "SANTO DOMINGO, DR"],
    "TR": ["ISKENDERUN, TURKEY"],
    "SY": ["TARTUS, SYRIA"],
    "GQ": ["MALABO, EQUATORIAL GUINEA"],
    "AZ": ["DAKU , AZERBAIJAN"],
    "BG": ["VARNA , BULGARIA"],
    "DE": ["BREMERHAVEN, GERMANY"],
    "UAE": ["JEBEL ALI, DUBAI"],
    "BF": ["BURKINA FASO"],
    "FR": ["FOS-SUR-MER, FRANCE"],
    "VE": ["MARACAIBO , VENEZUELLA"],
    "KH": ["SIHANOUKVILLE, CAMBODIA"],
    "CU": ["MARIEL, CUBA"]
}

def get_port_display_list(code):
    """코드를 입력받아 드롭다운에 표시할 리스트 반환"""
    if not code:
        return []
    # 대문자로 변환하여 매칭
    return COUNTRY_PORT_MAP.get(code.strip().upper(), [])
