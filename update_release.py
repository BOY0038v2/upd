import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET

TARGET_REPO = os.environ.get("TARGET_REPO", "gorhill/uBlock")
XML_FILE = "update.xml"
XMLNS = "http://www.google.com/update2/response"
ASSET_ENDS_WITH = os.environ.get("ASSET_ENDS_WITH", ".chromium.crx")

ET.register_namespace("", XMLNS)

api_url = f"https://api.github.com/repos/{TARGET_REPO}/releases/latest"
headers = {"User-Agent": "GitHub Action"}

token = os.environ.get("GITHUB_TOKEN")
if token:
    headers["Authorization"] = f"token {token}"

request = urllib.request.Request(api_url, headers=headers)

with urllib.request.urlopen(request) as response:
    release = json.loads(response.read().decode())

latest_version = release.get("tag_name", "")

if latest_version.startswith("v"):
    latest_version = latest_version[1:]

if not latest_version:
    raise SystemExit("Could not determine latest version from GitHub release.")

tree = ET.parse(XML_FILE)
root = tree.getroot()

updatecheck = root.find(f".//{{{XMLNS}}}updatecheck")

if updatecheck is None:
    raise SystemExit("Could not find <updatecheck> in update.xml")

current_version = updatecheck.get("version")

if current_version == latest_version:
    print(f"Already up to date: {current_version}")
    raise SystemExit(0)

print(f"Updating from {current_version} to {latest_version}")

updatecheck.set("version", latest_version)

download_url = None

for asset in release.get("assets", []):
    name = asset.get("name", "")
    if name.endswith(ASSET_ENDS_WITH):
        download_url = asset.get("browser_download_url")
        break

if download_url:
    updatecheck.set("codebase", download_url)
else:
    old_codebase = updatecheck.get("codebase", "")
    if current_version:
        updatecheck.set("codebase", old_codebase.replace(current_version, latest_version))

# Apply standard 2-space indentation
if hasattr(ET, "indent"):
    ET.indent(tree, space="  ")

# Write the XML with the declaration
tree.write(XML_FILE, encoding="utf-8", xml_declaration=True)

# Read the file back to fix the formatting exactly as you requested
with open(XML_FILE, "r", encoding="utf-8") as f:
    content = f.read()

# Fix XML declaration to use double quotes and uppercase UTF-8
content = content.replace("<?xml version='1.0' encoding='utf-8'?>", '<?xml version="1.0" encoding="UTF-8"?>')
content = content.replace("<?xml version='1.0' encoding='UTF-8'?>", '<?xml version="1.0" encoding="UTF-8"?>')

# Ensure exactly one space before the closing /> on the updatecheck tag
content = re.sub(r'(<updatecheck[^>]*?)(\s*/>)', r'\1 />', content)

# Save the perfectly formatted file
with open(XML_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print("update.xml has been updated and formatted.")
