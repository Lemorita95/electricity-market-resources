import xml.etree.ElementTree as ET

def parse_eic_code(root: ET.Element, function_filter: str) -> list[dict]:
    ns = {'ns': 'urn:iec62325.351:tc57wg16:451-n:eicdocument:1:2'}
    records = []
    for eic_elem in root.findall('ns:EICCode_MarketDocument', ns):
        print(eic_elem.find('ns:mRID', ns).text)
        print(eic_elem.find('ns:long_Names.name', ns).text)
        
        function_names = eic_elem.findall("ns:Function_Names", ns)
        print([f.find("ns:name", ns).text for f in function_names])

    return records