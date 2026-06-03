import requests, xml.etree.ElementTree as ET

r = requests.get("https://eepublicdownloads.blob.core.windows.net/cio-lio/xml/allocated-eic-codes.xml")
# root = ET.fromstring(r.content)
# r_content = r.content
# # iterate and extract fields based on XML tags
# print()
print(r.status_code)
print(r.headers.get('content-type'))
print(len(r.content))
print(r.encoding)
print(r.url)
print(r.request.method)

print('\nparsed xml...')
root = ET.fromstring(r.content)
print(root.tag)
print(root.nsmap if hasattr(root, 'nsmap') else None)
print([child.tag for child in list(root)[:10]])

from api.parser import parse_eic_code

print('\nnamespaces...')
parse_eic_code(root, 'Bidding Zone')