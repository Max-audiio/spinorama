#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# A library to display spinorama charts
#
# Copyright (C) 2020-2024 Pierre Aubert pierre(at)spinorama(dot)org
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
usage: generate_html.py [--help] [--version] [--dev] [--optim]\
 [--sitedev=<http>]  [--log-level=<level>] [--skip-speakers]

Options:
  --help            display usage()
  --version         script version number
  --sitedev=<http>  default: http://localhost:8000/docs
  --dev             if you want to generate the dev websites
  --optim           if you want an optimised built
  --skip-speakers   skip speaker html page generation (useful for debugging)
  --log-level=<level> default is WARNING, options are DEBUG INFO ERROR.
"""
from glob import glob
import json
import os
import shutil
import subprocess
import pathlib
import sys

from docopt import docopt

from mako.lookup import TemplateLookup

from datas.metadata import speakers_info as extradata
from generate_common import (
    args2level,
    get_custom_logger,
    find_metadata_file,
    find_metadata_chunks,
    sort_metadata_per_score,
    sort_metadata_per_date,
)

import spinorama.constant_paths as cpaths
from spinorama.need_update import need_update

SITEPROD = "https://www.spinorama.org"
SITEDEV = "https://dev.spinorama.org"
CACHE_VERSION = "v2"


def get_versions(filename):
    versions = {}
    with open(filename, "r") as fd:
        lines = fd.readlines()
        for line in lines:
            tokens = line[:-1].split("=")
            if len(tokens) != 2:
                continue
            if not (tokens[0].isalpha() and tokens[0].isupper()):
                continue
            numbers = tokens[1].split(".")
            if not (
                len(numbers) == 3
                and numbers[0].isdigit()
                and numbers[1].isdigit()
                and numbers[2].isdigit()
            ):
                continue
            versions[tokens[0]] = tokens[1]
    versions["CACHE"] = CACHE_VERSION
    return versions


def write_if_different(new_content: str, filename: str, force: bool):  # noqa: FBT001
    """Write the new content to disk only if it is different from the current one.
    The unchanged html files are then untouched and http cache effect is better.
    """
    identical = False
    path = pathlib.Path(filename)
    if path.exists():
        old_content = path.read_text(encoding="utf-8")
        if old_content == new_content:
            identical = True

    if not identical or force:
        path.write_text(new_content, encoding="utf-8")


FREQ_FILTER = [
    "CEA2034",
    "On Axis",
    "Early Reflections",
    "Estimated In-Room Response",
    "Horizontal Reflections",
    "Vertical Reflections",
    "SPL Horizontal",
    "SPL Vertical",
    "SPL Horizontal Normalized",
    "SPL Vertical Normalized",
]

CONTOUR_FILTER = [
    "SPL Horizontal Contour",
    "SPL Vertical Contour",
    "SPL Horizontal Contour Normalized",
    "SPL Vertical Contour Normalized",
    "SPL Horizontal Contour 3D",
    "SPL Vertical Contour 3D",
    "SPL Horizontal Contour Normalized 3D",
    "SPL Vertical Contour Normalized 3D",
]

RADAR_FILTER = [
    "SPL Horizontal Radar",
    "SPL Vertical Radar",
]


def generate_measurement(
    dataframe,
    meta,
    site,
    use_search,
    versions,
    speaker_name,
    origins,
    speaker_html,
    graph_html,
    origin,
    measurements,
    key,
    dfs,
):
    logger.debug("generate %s %s %s", speaker_name, origin, key)
    freq = {k: dfs[k] for k in FREQ_FILTER if k in dfs}
    contour = {k: dfs[k] for k in CONTOUR_FILTER if k in dfs}
    radar = {k: dfs[k] for k in RADAR_FILTER if k in dfs}
    # eq
    eq = None
    if key != "default_eq":
        eq_filter = [
            "ref_vs_eq",
        ]
    eq = {k: dfs[k] for k in eq_filter if k in dfs}
    # get index.html filename
    dirname = "{}/{}/".format(cpaths.CPATH_DOCS_SPEAKERS, speaker_name)
    if origin in ("ASR", "Princeton", "ErinsAudioCorner", "Misc"):
        dirname += origin
    else:
        dirname += meta[speaker_name]["brand"]
    index_name = "{0}/index_{1}.html".format(dirname, key)

    # write index.html
    logger.info("Writing %s for %s", index_name, speaker_name)
    speaker_content = speaker_html.render(
        speaker=speaker_name,
        g_freq=freq,
        g_contour=contour,
        g_radar=radar,
        g_key=key,
        g_eq=eq,
        meta=meta,
        origin=origin,
        site=site,
        use_search=use_search,
        min=".min" if flag_optim else "",
        versions=versions,
    )
    meta_file, eq_file = find_metadata_file()
    index_deps = [
        "./src/website/speaker.html",
        "./src/website/speaker_desc.html",
        "./src/website/utils.py",
        "./datas/metadata.py",
        meta_file,
        eq_file,
        *find_metadata_chunks().values(),
        *glob("./src/website/assets/*.js"),
    ]
    index_force = need_update(index_name, index_deps)
    write_if_different(speaker_content, index_name, index_force)

    # write a small file per graph to render the json generated by Vega
    for kind in [freq, contour, radar]:
        for graph_name in kind:
            graph_filename = "{0}/{1}/{2}.html".format(dirname, key, graph_name)
            logger.info("Writing %s/%s for %s", key, graph_filename, speaker_name)
            graph_content = graph_html.render(
                speaker=speaker_name,
                graph=graph_name,
                meta=meta,
                site=site,
                min=".min" if flag_optim else "",
                versions=versions,
            )
            graph_deps = [
                *glob("./datas/measurements/{}/{}/*.*".format(speaker_name, key)),
                *glob("./src/spinorama/*.py"),
            ]
            graph_force = need_update(graph_filename, graph_deps)
            write_if_different(graph_content, graph_filename, graph_force)


def generate_speaker(
    dataframe, meta, site, use_search, versions, speaker_name, origins, speaker_html, graph_html
):
    for origin, measurements in origins.items():
        for key, dfs in measurements.items():
            try:
                # print('DEBUG: '+speaker_name+' origin='+origin+' version='+key)
                generate_measurement(
                    dataframe,
                    meta,
                    site,
                    use_search,
                    versions,
                    speaker_name,
                    origins,
                    speaker_html,
                    graph_html,
                    origin,
                    measurements,
                    key,
                    dfs,
                )
            except KeyError as key_error:
                print(
                    "generate_speaker: a file per speaker for {} failed with {}".format(
                        speaker_name, key_error
                    )
                )


def generate_speakers(mako, dataframe, meta, site, use_search, versions):
    """For each speaker, generates a set of HTML files driven by templates"""
    speaker_html = mako.get_template("speaker.html")
    graph_html = mako.get_template("graph.html")
    for speaker_name, origins in dataframe.items():
        logger.debug("html generation for speaker_name %s", speaker_name)
        if speaker_name in extradata and extradata[speaker_name].get("skip", False):
            logger.debug("skipping %s", speaker_name)
            continue
        generate_speaker(
            dataframe,
            meta,
            site,
            use_search,
            versions,
            speaker_name,
            origins,
            speaker_html,
            graph_html,
        )

    return 0


def main():
    # create some directories
    for dir in (
            cpaths.CPATH_DOCS,
            cpaths.CPATH_DOCS_JS,
            cpaths.CPATH_DOCS_JS3RD,
            cpaths.CPATH_DOCS_JSON,
            cpaths.CPATH_DOCS_CSS
    ):
        os.makedirs(dir, mode=0o755, exist_ok=True)

    # load all metadata from generated json file
    metadata_json_filename, eqdata_json_filename = find_metadata_file()
    metadata_json_chunks = find_metadata_chunks()
    for radical, json_check in (
        ("metadata", metadata_json_filename),
        ("eqdata", eqdata_json_filename),
    ):
        if json_check is None:
            logger.error("Cannot find %s, you should run generate_meta.py again!", radical)
            sys.exit(1)

    meta = None
    with open(metadata_json_filename, "r") as f:
        meta = json.load(f)

    # load versions for various css and js files
    versions = get_versions("{}/update_3rdparties.sh".format(cpaths.CPATH_SCRIPTS))

    # only build a dictionnary will all graphs
    main_df = {}
    speakers = glob("{}/*".format(cpaths.CPATH_DOCS_SPEAKERS))
    for speaker in speakers:
        if not os.path.isdir(speaker):
            continue
        # humm annoying
        speaker_name = speaker.replace(cpaths.CPATH_DOCS_SPEAKERS + "/", "")
        if speaker_name in ("score", "assets", "stats", "compare", "logos", "pictures"):
            continue
        main_df[speaker_name] = {}
        origins = glob(speaker + "/*")
        for origin in origins:
            if not os.path.isdir(origin):
                continue
            origin_name = os.path.basename(origin)
            main_df[speaker_name][origin_name] = {}
            defaults = glob(origin + "/*")
            for default in defaults:
                if not os.path.isdir(default):
                    continue
                default_name = os.path.basename(default)
                main_df[speaker_name][origin_name][default_name] = {}
                graphs = glob(default + "/*_large.png")
                for graph in graphs:
                    g = os.path.basename(graph).replace("_large.png", "")
                    main_df[speaker_name][origin_name][default_name][g] = {}

    # configure Mako
    mako_templates = TemplateLookup(
        directories=[cpaths.CPATH_WEBSITE, cpaths.CPATH_BUILD_WEBSITE],
        module_directory=cpaths.CPATH_BUILD_MAKO,
    )

    # write index.html
    logger.info("Write index.html")
    index_html = mako_templates.get_template("index.html")
    meta_sorted_date = sort_metadata_per_date(meta)

    try:
        html_content = index_html.render(
            df=main_df,
            meta=meta_sorted_date,
            site=site,
            use_search=True,
            min=".min" if flag_optim else "",
            versions=versions,
        )
        html_filename = f"{cpaths.CPATH_DOCS}/index.html"
        write_if_different(html_content, html_filename, force=False)
    except KeyError as key_error:
        print("Generating index.html failed with {}".format(key_error))
        sys.exit(1)

    # write eqs.html
    logger.info("Write eqs.html")
    eqs_html = mako_templates.get_template("eqs.html")

    try:
        eqs_content = eqs_html.render(
            df=main_df,
            meta=meta_sorted_date,
            site=site,
            use_search=True,
            min=".min" if flag_optim else "",
            versions=versions,
        )
        eqs_filename = f"{cpaths.CPATH_DOCS}/eqs.html"
        write_if_different(eqs_content, eqs_filename, force=False)
    except KeyError as key_error:
        print("Generating eqs.htmlfailed with {}".format(key_error))
        sys.exit(1)

    # write various html files
    meta_sorted_score = sort_metadata_per_score(meta)
    try:
        for item in (
            "scores",
            "help",
            "compare",
            "statistics",
            "similar",
        ):
            item_name = "{0}.html".format(item)
            logger.info("Write %s", item_name)
            item_html = mako_templates.get_template(item_name)
            use_search = False
            if item in ("scores", "similar"):
                use_search = True
            item_content = item_html.render(
                df=main_df,
                meta=meta_sorted_score,
                site=site,
                use_search=use_search,
                min=".min" if flag_optim else "",
                versions=versions,
            )
            item_filename = cpaths.CPATH_DOCS + "/" + item_name
            write_if_different(item_content, item_filename, force=False)

    except KeyError as key_error:
        print("Generating various html files failed with {}".format(key_error))
        sys.exit(1)

    # write a file per speaker
    if not skip_speakers:
        logger.info("Write a file per speaker")
        try:
            generate_speakers(
                mako_templates, main_df, meta=meta, site=site, use_search=False, versions=versions
            )
        except KeyError as key_error:
            print("Generating a file per speaker failed with {}".format(key_error))
            sys.exit(1)
    else:
        logger.info("Skip speaker html generation!")

    # copy favicon(s) and logos
    for f in [
        "3d3a.png",
        "asr.png",
        "asr-small.png",
        "BIC America.jpg",
        "bose.png",
        "Buchardt Audio.png",
        "eac.png",
        "favicon-16x16.png",
        "favicon.ico",
        "fulcrum-acoustic.png",
        "icon-bookshelves.svg",
        "icon-bookshelves.png",
        "icon-bookshelves.webp",
        "icon-bookshelves-48x48.png",
        "icon-bookshelves-48x48.webp",
        "icon-bookshelves-144x144.png",
        "icon-bookshelves-144x144.webp",
        "icon-bookshelves-zigzag.svg",
        "infinity.png",
        "infinity-small.png",
        "jbl.jpg",
        "jtr.png",
        "jtr-small.png",
        "kef.png",
        "kling-freitag.png",
        "magico.png",
        "meyersound.png",
        "neumann.png",
        "paradigm.png",
        "pmc.png",
        "revel.png",
        "spin.svg",
    ]:
        file_in = cpaths.CPATH_DATAS_ICONS + "/" + f
        file_out = cpaths.CPATH_DOCS + "/pictures/" + f
        shutil.copy(file_in, file_out)

    # copy custom css
    for f in [
        "spinorama.css",
    ]:
        file_in = cpaths.CPATH_WEBSITE + "/" + f
        file_out = cpaths.CPATH_DOCS + "/css/" + f
        shutil.copy(file_in, file_out)

    # copy manifest
    for f in [
        "manifest.json",
    ]:
        file_in = cpaths.CPATH_WEBSITE + "/" + f
        file_out = cpaths.CPATH_DOCS + "/" + f
        shutil.copy(file_in, file_out)

    # cleanup flow directives: currently unused
    # flow_bin = "./node_modules/.bin/flow-remove-types"
    # flow_param = ""  # "--pretty --sourcemaps"
    # 
    # flow_command = "{} {} {} {} {}".format(
    # flow_bin,
    # flow_param,
    # cpaths.CPATH_WEBSITE,
    # "--out-dir",
    # cpaths.CPATH_BUILD_WEBSITE,
    # )
    # status = subprocess.run(
    # [flow_command], shell=True, check=True, capture_output=True  # noqa: S602
    # )
    # if status.returncode != 0:
    # print("flow failed")

    # copy css/js files
    logger.info("Copy js files to %s", cpaths.CPATH_DOCS_JS)
    try:
        for item in (
            "compare",
            "download",
            "eqs",
            "graph",
            "index",
            "meta",
            "misc",
            "onload",
            "pagination",
            "plot",
            "scores",
            "search",
            "similar",
            "statistics",
            "tabs",
        ):
            item_name = "{}.js".format(item)
            item_html = mako_templates.get_template(item_name)
            # remove the ./docs parts
            len_docs = len("/docs/")
            metadata_filename = metadata_json_filename[len_docs:]
            metadata_filename_head = metadata_json_chunks["head"][len_docs:]
            js_chunks = "[{}]".format(
                ", ".join(
                    [
                        "'{}'".format(v[len_docs:])
                        for k, v in metadata_json_chunks.items()
                        if k != "head"
                    ]
                )
            )
            eqdata_filename = eqdata_json_filename[len_docs:]
            item_content = item_html.render(
                df=main_df,
                meta=meta_sorted_score,
                site=site,
                metadata_filename=metadata_filename,
                metadata_filename_head=metadata_filename_head,
                metadata_filename_chunks=js_chunks,
                eqdata_filename=eqdata_filename,
                min=".min" if flag_optim else "",
                versions=versions,
            )
            item_filename = "{}/{}-1-gen.js".format(cpaths.CPATH_BUILD_WEBSITE, item)
            write_if_different(item_content, item_filename, force=True)
            # compress files with terser
            if flag_optim:
                terser_command = "{0} {1}/{2} > {3}/{4}".format(
                    "./node_modules/.bin/terser",
                    cpaths.CPATH_BUILD_WEBSITE,
                    "{}-1-gen.js".format(item),
                    cpaths.CPATH_DOCS_JS,
                    "{}-{}.min.js".format(item, CACHE_VERSION),
                )
                # print(terser_command)
                try:
                    status = subprocess.run(
                        [terser_command], shell=True, check=True, capture_output=True  # noqa: S602
                    )
                    if status.returncode != 0:
                        print("terser failed for item {}".format(item))
                except subprocess.CalledProcessError as e:
                    print("terser failed for item {} with {}".format(item, e))
            # optimise files with critical
            if flag_optim:
                pass
    except KeyError as key_error:
        print("Generating various html files failed with {}".format(key_error))
        sys.exit(1)

    # generate robots.txt and sitemap.xml
    logger.info("Copy robots/sitemap files to %s", cpaths.CPATH_DOCS)
    try:
        for item_name in (
            "robots.txt",
            "sitemap.xml",
        ):
            logger.info("Write %s", item_name)
            item_html = mako_templates.get_template(item_name)
            item_content = item_html.render(
                df=main_df,
                meta=meta_sorted_score,
                site=site,
                isProd=(site == SITEPROD),
                min=".min" if flag_optim else "",
                versions=versions,
            )
            item_filename = cpaths.CPATH_DOCS + "/" + item_name
            # ok for robots but likely doesn't work for sitemap
            write_if_different(item_content, item_filename, force=True)
    except KeyError as key_error:
        print("Generating various html files failed with {}".format(key_error))
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    args = docopt(__doc__, version="update_html.py version 1.23", options_first=True)
    flag_dev = args["--dev"]
    flag_optim = args["--optim"]
    site = SITEPROD
    skip_speakers = False
    if flag_dev:
        site = SITEDEV
        if args["--sitedev"] is not None:
            site = args["--sitedev"]
            if len(site) < 4 or site[0:4] != "http":
                print("sitedev {} does not start with http!".format(site))
                sys.exit(1)
        skip_speakers = args["--skip-speakers"]

    logger = get_custom_logger(level=args2level(args), duplicate=True)
    main()
