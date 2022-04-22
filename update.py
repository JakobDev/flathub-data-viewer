from typing import Any
import requests
import shutil
import json
import time
import os


def add_to_data(data: dict, key: str, first: str, second: str, value: str):
    if first not in data[key]:
        data[key][first] = {}

    if second not in data[key][first]:
        data[key][first][second] = []

    data[key][first][second].append(value)


def add_simple_to_data(data: dict, key: str, name: str, app_id: str):
    if name not in data[key]:
        data[key][name] = []

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
        except:
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
            if not i.startswith(app_id):
                add_simple_to_data(data, "extensions", i, app_id)

    if "permissions" in r["metadata"]:
        for key in r["metadata"]["permissions"].keys():
            if key == "session-bus":
                for bus_type in r["metadata"]["permissions"][key].keys():
                    for i in r["metadata"]["permissions"][key][bus_type]:
                        add_to_data(data, "permissions", bus_type + "-name", i, app_id)
            elif key == "system-bus":
                for bus_type in r["metadata"]["permissions"][key].keys():
                    for i in r["metadata"]["permissions"][key][bus_type]:
                        add_to_data(data, "permissions", f"system-{bus_type}-name", i, app_id)
            else:
                for i in r["metadata"]["permissions"][key]:
                    if i in SKIP_PERMISSIONS:
                        continue
                    elif key in PERMISSON_NAMES:
                        add_to_data(data, "permissions", PERMISSON_NAMES[key], i, app_id)
                    else:
                        add_to_data(data, "permissions", key, i, app_id)


def parse_appstream_api(app_id: str, data: dict):
    r = try_request("https://flathub.org/api/v2/appstream/" + app_id)

    for i in r["urls"].keys():
        add_simple_to_data(data, "url", i, app_id)

    if "categories" in r:
        for i in r["categories"]:
            add_simple_to_data(data, "categories", i, app_id)

    if "project_license" in r:
        if r["project_license"].startswith("LicenseRef"):
            add_simple_to_data(data, "license", "Proprietary", app_id)
        else:
            add_simple_to_data(data, "license", r["project_license"], app_id)
    else:
        add_simple_to_data(data, "license", "Unknown", app_id)

    if "content_rating" in r:
        if not isinstance(r["content_rating"], list):
            for key, value in r["content_rating"].items():
                if key == "type":
                    continue

                add_to_data(data, "oars", key, value, app_id)

    if "keywords" in r:
        for i in r["keywords"]:
            i = clear_filename(i)
            if i != "":
                add_simple_to_data(data, "keywords", i, app_id)

    if "mimetypes" in r:
        for i in r["mimetypes"]:
            add_simple_to_data(data, "mimetypes", clear_filename(i), app_id)

    if "project_group" in r:
        add_simple_to_data(data, "project_group", clear_filename(i), app_id)


def write_data(path: str, data: dict, description: str):
    try:
        os.makedirs(path)
    except:
        pass

    with open(os.path.join(path, "index.json"), "w", encoding="utf-8") as f:
        json.dump({"description": description, "data": sorted(data)}, f, ensure_ascii=False, indent=4)

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
    data["url"] = {}
    data["categories"] = {}
    data["license"] = {}
    data["oars"] = {}
    data["keywords"] = {}
    data["mimetypes"] = {}
    data["project_group"] = {}

    for i in requests.get("https://flathub.org/api/v2/appstream").json():
        print(i)
        parse_summary_api(i, data)
        parse_appstream_api(i, data)

    data_path = "web/data"

    try:
        shutil.rmtree(data_path)
    except:
        pass

    try:
        os.makedirs(data_path)
    except:
        pass

    write_data(os.path.join(data_path, "Runtime"), data["runtime"], "Shows all Apps with the given Runtime")
    write_data(os.path.join(data_path, "SDK"), data["sdk"], "Shows all Apps with the given SDK")
    write_data(os.path.join(data_path, "BaseApp"), data["base_app"], "Shows all Apps with the given BaseApp")
    write_data(os.path.join(data_path, "Extensions"), data["extensions"], "Shows all Apps with the given Extensions")
    write_data(os.path.join(data_path, "Permissions"), data["permissions"], "Shows all Apps with the given Permission")
    write_data(os.path.join(data_path, "Url"), data["url"], "Shows all Apps which has a URL with the given type")
    write_data(os.path.join(data_path, "Categories"), data["categories"], "Shows all Apps with the given Categorie")
    write_data(os.path.join(data_path, "License"), data["license"], "Shows all Apps with the given License")
    write_data(os.path.join(data_path, "OARS"), data["oars"], "Shows all Apps with the OARS type")
    write_data(os.path.join(data_path, "Keywords"), data["keywords"], "Shows all Apps with the given Keyword")
    write_data(os.path.join(data_path, "Mimetypes"), data["mimetypes"], "Shows all Apps with the given Mimetype")
    write_data(os.path.join(data_path, "ProjectGroup"), data["project_group"], "Shows all Apps with the given ProjectGroup")

    with open(os.path.join(data_path, "types.json"), "w", encoding="utf-8") as f:
        json.dump([
            {"name": "Runtime", "value": "Runtime"},
            {"name": "SDK", "value": "SDK"},
            {"name": "BaseApp", "value": "BaseApp"},
            {"name": "Extension", "value": "Extensions"},
            {"name": "Permission", "value": "Permissions"},
            {"name": "URL", "value": "Url"},
            {"name": "Categorie", "value": "Categories"},
            {"name": "License", "value": "License"},
            {"name": "OARS", "value": "OARS"},
            {"name": "Keyword", "value": "Keywords"},
            {"name": "Mimetype", "value": "Mimetypes"},
            {"name": "Project Group", "value": "ProjectGroup"}
        ], f, ensure_ascii=False, indent=4)

    with open(os.path.join(data_path, "updated.json"), "w", encoding="utf-8") as f:
        json.dump(int(time.time() * 1000), f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()
