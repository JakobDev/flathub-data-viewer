from typing import Any, Optional
from datetime import datetime
import appstream_python
import requests
import tempfile
import random
import shutil
import json
import time
import os


def download_file(url: str, path: str):
    r = requests.get(url, stream=True)
    with open(path, "wb") as f:
        shutil.copyfileobj(r.raw, f)


def get_appstream_data() -> appstream_python.AppstreamCollection:
    temp_path = os.path.join(tempfile.gettempdir(), f"Flathub_Appstream_{random.randint(1, 1000000)}.tmp")
    download_file("https://hub.flathub.org/repo/appstream/x86_64/appstream.xml.gz", temp_path)
    appstream_collection = appstream_python.AppstreamCollection()
    appstream_collection.load_compressed_appstream_collection(temp_path)
    os.remove(temp_path)
    return appstream_collection


def add_to_data(data: dict, key: str, first: str, second: str, value: str):
    if first not in data[key]:
        data[key][first] = {}

    if second not in data[key][first]:
        data[key][first][second] = []

    data[key][first][second].append(value)


def add_simple_to_data(data: dict, key: str, name: str, app_id: str):
    if name not in data[key]:
        data[key][name] = []

    if app_id not in data[key][name]:
        data[key][name].append(app_id)


def clear_filename(name: str) -> str:
    name = name.replace("/", "{SLASH}")
    name = name.replace("\\", "{BACKSLASH}")
    name = name.replace("\"", "{DOUBLEQUOTE}")
    name = name.replace(" ", "{SPACE}")
    name = name.replace("*", "{ASTERISK}")
    return name


def try_request(url: str) -> Any:
    for i in range(10):
        try:
            return requests.get(url).json()
        except Exception:
            time.sleep(1)
    raise Exception()


SKIP_PERMISSIONS = [
    "unset-environment"
]


PERMISSON_NAMES = {
    "shared": "share",
    "sockets": "socket",
    "devices": "device",
    "features": "allow",
    "filesystems": "filesystem"
}


def parse_summary_api(app_id: str, data: dict):
    r = try_request("https://flathub.org/api/v2/summary/" + app_id)

    runtime_name, _, runtime_version = r["metadata"]["runtime"].split("/")
    add_to_data(data, "runtime", runtime_name, runtime_version, app_id)

    sdk_name, _, sdk_version = r["metadata"]["sdk"].split("/")
    add_to_data(data, "sdk", sdk_name, sdk_version, app_id)

    if "base" in r["metadata"]:
        _, base_name, _, base_version = r["metadata"]["base"].split("/")

        add_to_data(data, "base_app", base_name, base_version, app_id)

    if "extensions" in r["metadata"]:
        for i in r["metadata"]["extensions"].keys():
            if not i.startswith(app_id.replace("-", "_")):
                add_simple_to_data(data, "extensions", i, app_id)

    if "permissions" in r["metadata"]:
        for key in r["metadata"]["permissions"].keys():
            if key in SKIP_PERMISSIONS:
                continue
            elif key == "session-bus":
                for bus_type in r["metadata"]["permissions"][key].keys():
                    for i in r["metadata"]["permissions"][key][bus_type]:
                        add_to_data(data, "permissions", bus_type + "-name", i, app_id)
            elif key == "system-bus":
                for bus_type in r["metadata"]["permissions"][key].keys():
                    for i in r["metadata"]["permissions"][key][bus_type]:
                        add_to_data(data, "permissions", f"system-{bus_type}-name", i, app_id)
            else:
                for i in r["metadata"]["permissions"][key]:
                    if key in PERMISSON_NAMES:
                        add_to_data(data, "permissions", PERMISSON_NAMES[key], i, app_id)
                    else:
                        add_to_data(data, "permissions", key, i, app_id)

    for i in r["arches"]:
        add_simple_to_data(data, "arch", i, app_id)


def parse_appstream(app_id: str, data: dict, appstream_collection: appstream_python.AppstreamCollection):
    component = appstream_collection.get_component(app_id)

    if component is None:
        component = appstream_collection.get_component(app_id + ".desktop")
        if component is None:
            print("Error " + app_id)
            return

    for i in list(component.urls.keys()):
        add_simple_to_data(data, "url", i, app_id)

    for i in component.categories:
        add_simple_to_data(data, "categories", i, app_id)

    if component.project_license == "":
        add_simple_to_data(data, "license", "Unknown", app_id)
    elif component.project_license.startswith("LicenseRef"):
        add_simple_to_data(data, "license", "Proprietary", app_id)
    else:
        add_simple_to_data(data, "license", component.project_license, app_id)

    for key, value in component.oars.items():
        add_to_data(data, "oars", key, value, app_id)

    for i in component.keywords.get_default_list():
        i = clear_filename(i)
        if i != "":
            add_simple_to_data(data, "keywords", i, app_id)

    for i in component.provides["mediatype"]:
        add_simple_to_data(data, "mimetypes", clear_filename(i), app_id)

    if component.project_group:
        add_simple_to_data(data, "project_group", clear_filename(component.project_group), app_id)

    for i in component.kudos:
        add_simple_to_data(data, "kudos", i, app_id)

    for i in component.translation:
        add_simple_to_data(data, "translation_type", i["type"], app_id)

    for i in list(component.languages.keys()):
        add_simple_to_data(data, "app_language", i, app_id)

    for i in component.get_aviable_languages():
        add_simple_to_data(data, "appstream_language", i, app_id)

    if len(component.releases) >= 1:
        last_updated_days = (datetime.now().date() - component.releases[0].date).days
        if last_updated_days <= 7:
            add_simple_to_data(data, "last_updated", "Week", app_id)
        elif last_updated_days <= 31:
            add_simple_to_data(data, "last_updated", "Month", app_id)
        elif last_updated_days <= 182:
            add_simple_to_data(data, "last_updated", "HalfYear", app_id)
        elif last_updated_days <= 365:
            add_simple_to_data(data, "last_updated", "Year", app_id)
        else:
            add_simple_to_data(data, "last_updated", "Older", app_id)
    else:
        add_simple_to_data(data, "last_updated", "Unknown", app_id)


def write_data(path: str, data: dict, description: str, enable_all: bool = False, all_text: Optional[str] = None, data_names: Optional[dict[str, str]] = None, sort_alphabetically: bool = True):
    try:
        os.makedirs(path)
    except Exception:
        pass

    index = {}
    index["description"] = description

    if enable_all:
        index["enableAll"] = True

    if all_text:
        index["allText"] = all_text

    if sort_alphabetically:
        index["data"] = sorted(data)
    else:
        index["data"] = list(data.keys())

    index["dataNames"] = data_names or {}

    with open(os.path.join(path, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=4)

    for i in sorted(data):
        with open(os.path.join(path, i + ".json"), "w", encoding="utf-8") as f:
            json.dump(data[i], f, ensure_ascii=False, indent=4)


def main():
    data = {}
    data["runtime"] = {}
    data["sdk"] = {}
    data["base_app"] = {}
    data["extensions"] = {}
    data["permissions"] = {}
    data["arch"] = {}
    data["url"] = {}
    data["categories"] = {}
    data["license"] = {}
    data["oars"] = {}
    data["keywords"] = {}
    data["mimetypes"] = {}
    data["project_group"] = {}
    data["kudos"] = {}
    data["translation_type"] = {}
    data["app_language"] = {}
    data["appstream_language"] = {}
    data["last_updated"] = {"Week": [], "Month": [], "HalfYear": [], "Year": [], "Older": [], "Unknown": []}

    app_list = requests.get("https://flathub.org/api/v2/appstream").json()

    appstream_collection = get_appstream_data()

    for i in app_list:
        print(i)
        parse_summary_api(i, data)
        parse_appstream(i, data, appstream_collection)

    data_path = "web/data"

    try:
        shutil.rmtree(data_path)
    except Exception:
        pass

    try:
        os.makedirs(data_path)
    except Exception:
        pass

    write_data(os.path.join(data_path, "Runtime"), data["runtime"], "Shows all Apps with the given Runtime")
    write_data(os.path.join(data_path, "SDK"), data["sdk"], "Shows all Apps with the given SDK")
    write_data(os.path.join(data_path, "BaseApp"), data["base_app"], "Shows all Apps with the given BaseApp")
    write_data(os.path.join(data_path, "Extensions"), data["extensions"], "Shows all Apps with the given Extensions")
    write_data(os.path.join(data_path, "Permissions"), data["permissions"], "Shows all Apps with the given Permission")
    write_data(os.path.join(data_path, "Architecture"), data["arch"], "Shows all Apps which supports the given Architecture")
    write_data(os.path.join(data_path, "Url"), data["url"], "Shows all Apps which has a URL with the given type")
    write_data(os.path.join(data_path, "Categories"), data["categories"], "Shows all Apps with the given Categorie")
    write_data(os.path.join(data_path, "License"), data["license"], "Shows all Apps with the given License")
    write_data(os.path.join(data_path, "OARS"), data["oars"], "Shows all Apps with the OARS type")
    write_data(os.path.join(data_path, "Keywords"), data["keywords"], "Shows all Apps with the given Keyword")
    write_data(os.path.join(data_path, "Mimetypes"), data["mimetypes"], "Shows all Apps with the given Mimetype")
    write_data(os.path.join(data_path, "ProjectGroup"), data["project_group"], "Shows all Apps with the given ProjectGroup")
    write_data(os.path.join(data_path, "Kudos"), data["kudos"], "Shows all Apps with the given Kudo")
    write_data(os.path.join(data_path, "TranslationType"), data["translation_type"], "Shows all Apps with the given Translation Type", enable_all=True)
    write_data(os.path.join(data_path, "AppLanguage"), data["app_language"], "Shows all Apps which are aviable in the given Language")
    write_data(os.path.join(data_path, "AppstreamLanguage"), data["appstream_language"], "Shows all Apps with has a Appstream Translation in the given Language", enable_all=True, all_text="All Apps with at least one translation")
    write_data(os.path.join(data_path, "LastUpdated"), data["last_updated"], "Shows all Apps that are last updated in the given range", data_names={"Week": "In the last Week", "Month": "In the last Month", "HalfYear": "In the last half Year", "Year": "In the last Year"}, sort_alphabetically=False)

    with open(os.path.join(data_path, "types.json"), "w", encoding="utf-8") as f:
        json.dump([
            {"name": "Runtime", "value": "Runtime"},
            {"name": "SDK", "value": "SDK"},
            {"name": "BaseApp", "value": "BaseApp"},
            {"name": "Extension", "value": "Extensions"},
            {"name": "Permission", "value": "Permissions"},
            {"name": "Architecture", "value": "Architecture"},
            {"name": "URL", "value": "Url"},
            {"name": "Categorie", "value": "Categories"},
            {"name": "License", "value": "License"},
            {"name": "OARS", "value": "OARS"},
            {"name": "Keyword", "value": "Keywords"},
            {"name": "Mimetype", "value": "Mimetypes"},
            {"name": "Project Group", "value": "ProjectGroup"},
            {"name": "Kudo", "value": "Kudos"},
            {"name": "Translation Type", "value": "TranslationType"},
            {"name": "App Language", "value": "AppLanguage"},
            {"name": "Appstream Language", "value": "AppstreamLanguage"},
            {"name": "Last Updated", "value": "LastUpdated"}
        ], f, ensure_ascii=False, indent=4)

    with open(os.path.join(data_path, "appcount.json"), "w", encoding="utf-8") as f:
        json.dump(len(app_list), f, ensure_ascii=False, indent=4)

    with open(os.path.join(data_path, "updated.json"), "w", encoding="utf-8") as f:
        json.dump(int(time.time() * 1000), f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()
