#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
****************************************
*        coded by Lululla              *
*             28/12/2024               *
****************************************
# --------------------#
# Info Linuxsat-support.com & corvoboys.org

USAGE:
put this file in /tmp
telnet command:
---> cd /tmp
---> python Vavoo_m3u.py

explore folder VavooGen
'''

import os
import requests
import sys


# Function to generate M3U content for a single item
def generate_m3u(group, name, logo, tvg_id, url):
    url = url.replace(".ts", "/index.m3u8").replace("/live2/play", "/play")
    if not url.endswith("/index.m3u8"):
        url += "/index.m3u8"
    url = url.replace(".m3u8.m3u8", ".m3u8")
    m3u_entry = (
        "#EXTINF:-1 tvg-id=\"{}\" tvg-name=\"{}\" tvg-logo=\"{}\" group-title=\"{}\" "
        "http-user-agent=\"VAVOO/1.0\" http-referrer=\"https://vavoo.to/\",{}\n"
        "#EXTVLCOPT:http-user-agent=VAVOO/1.0\n"
        "#EXTVLCOPT:http-referrer=https://vavoo.to/\n"
        "#KODIPROP:http-user-agent=VAVOO/1.0\n"
        "#KODIPROP:http-referrer=https://vavoo.to/\n"
        "#EXTHTTP:{{\"User-Agent\":\"VAVOO/1.0\",\"Referer\":\"https://vavoo.to/\"}}\n"
        "{}").format(
        tvg_id, name, logo, group, name, url)
    return m3u_entry, group, url


# Function to download JSON data
def fetch_json_data():
    response = requests.get(
        "https://www2.vavoo.to/live2/index?countries=all&output=json")
    response.raise_for_status()
    return response.json()


# Function to process a single item
def process_item(item):
    return generate_m3u(
        item.get(
            "group", ""), item.get(
            "name", ""), item.get(
                "logo", ""), item.get(
                    "tvg_id", ""), item.get(
                        "url", ""))


# Main function
def main(output_dir):
    os.makedirs(output_dir, exist_ok=True)

    try:
        items = fetch_json_data()
    except Exception as e:
        print("Error while downloading JSON data: {}".format(e))
        return

    index_m3u_path = os.path.join(output_dir, "index.m3u")
    ids_txt_path = os.path.join(output_dir, "ids.txt")

    if os.path.exists(index_m3u_path):
        os.remove(index_m3u_path)

    ids_content = ""
    processed_count = 0
    groups = {}

    with open(index_m3u_path, "w") as index_m3u:
        index_m3u.write("#EXTM3U\n")

    for item in items:
        try:
            m3u_content, group, htaccess_url = process_item(item)
        except Exception as e:
            print("Error while processing an item: {}".format(e))
            continue

        with open(index_m3u_path, "a") as index_m3u:
            index_m3u.write(m3u_content + "\n")

        if group not in groups:
            group_file_path = os.path.join(
                output_dir, "index_{}.m3u".format(group))
            groups[group] = group_file_path
            with open(group_file_path, "w") as group_file:
                group_file.write("#EXTM3U\n")

        with open(groups[group], "a") as group_file:
            group_file.write(m3u_content + "\n")

        item_id = item.get(
            "url",
            "").replace(
            "https://vavoo.to/live2/play/",
            "").replace(
            ".ts",
            "")
        ids_content += item_id + "\n"

        processed_count += 1
        print("Processed {}/{} channels".format(processed_count, len(items)))

    with open(ids_txt_path, "w") as ids_file:
        ids_file.write(ids_content)

    print("Generation completed. Files saved in: {}".format(output_dir))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: {} <output_directory>".format(sys.argv[0]))
        sys.exit(1)
    output_dir = sys.argv[1]
    main(output_dir)
