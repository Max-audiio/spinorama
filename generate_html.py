#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# A library to display spinorama charts
#
# Copyright (C) 2020-21 Pierre Aubert pierreaubert(at)yahoo(dot)fr
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
usage: generate_html.py [--help] [--version] [--dev]\
 [--sitedev=<http>]  [--log-level=<level>]

Options:
  --help            display usage()
  --version         script version number
  --sitedev=<http>  default: http://localhost:8000/docs
  --log-level=<level> default is WARNING, options are DEBUG INFO ERROR.
"""
import json
import os
import shutil
import sys
from glob import glob
from mako.template import Template
from mako.lookup import TemplateLookup
from docopt import docopt

from datas.metadata import speakers_info as extradata
from generate_common import get_custom_logger, args2level

siteprod = "https://pierreaubert.github.io/spinorama"
sitedev = "http://localhost:8000/docs"
root = "./"


def generate_speaker(mako, dataframe, meta, site, useSearch):
    speaker_html = mako.get_template("speaker.html")
    graph_html = mako.get_template("graph.html")
    for speaker_name, origins in dataframe.items():
        if extradata[speaker_name].get("skip", False):
            continue
        for origin, measurements in origins.items():
            for key, dfs in measurements.items():
                logger.debug("generate {0} {1} {2}".format(speaker_name, origin, key))
                # freq
                freq_filter = [
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
                freq = {k: dfs[k] for k in freq_filter if k in dfs}
                # contour
                contour_filter = [
                    "SPL Horizontal Contour",
                    "SPL Vertical Contour",
                    "SPL Horizontal Contour Normalized",
                    "SPL Vertical Contour Normalized",
                ]
                contour = {k: dfs[k] for k in contour_filter if k in dfs}
                # radar
                radar_filter = [
                    "SPL Horizontal Radar",
                    "SPL Vertical Radar",
                ]
                radar = {k: dfs[k] for k in radar_filter if k in dfs}
                # eq
                eq = None
                if key != "default_eq":
                    eq_filter = [
                        "ref_vs_eq",
                    ]
                    eq = {k: dfs[k] for k in eq_filter if k in dfs}
                # get index.html filename
                dirname = "docs/" + speaker_name + "/"
                if origin in ("ASR", "Princeton", "ErinsAudioCorner", "Misc"):
                    dirname += origin
                else:
                    dirname += meta[speaker_name]["brand"]
                index_name = "{0}/index_{1}.html".format(dirname, key)

                # write index.html
                logger.info("Writing {0} for {1}".format(index_name, speaker_name))
                with open(index_name, "w") as f_index:
                    # write all
                    f_index.write(
                        speaker_html.render(
                            speaker=speaker_name,
                            g_freq=freq,
                            g_contour=contour,
                            g_radar=radar,
                            g_key=key,
                            g_eq=eq,
                            meta=meta,
                            origin=origin,
                            site=site,
                            useSearch=useSearch,
                        )
                    )
                    f_index.close()

                # write a small file per graph to render the json generated by Vega
                for kind in [freq, contour, radar]:  # isoband, directivity]:
                    for graph_name in kind:
                        graph_filename = "{0}/{1}/{2}.html".format(
                            dirname, key, graph_name
                        )
                        logger.info(
                            "Writing {2}/{0} for {1}".format(
                                graph_filename, speaker_name, key
                            )
                        )
                        with open(graph_filename, "w") as f_graph:
                            f_graph.write(
                                graph_html.render(
                                    graph=graph_name, meta=meta, site=site
                                )
                            )
                            f_graph.close()
    return 0


if __name__ == "__main__":
    args = docopt(__doc__, version="update_html.py version 1.22", options_first=True)

    # check args section
    dev = args["--dev"]
    site = siteprod
    if dev is True:
        if args["--sitedev"] is not None:
            sitedev = args["--sitedev"]
            if len(sitedev) < 4 or sitedev[0:4] != "http":
                print("sitedev {} does not start with http!".format(sitedev))
                sys.exit(1)
        site = sitedev

    level = args2level(args)
    logger = get_custom_logger(True)
    logger.setLevel(level)

    # load all metadata from generated json file
    json_filename = "./docs/assets/metadata.json"
    if not os.path.exists(json_filename):
        logger.error("Cannot find {0}".format(json_filename))
        sys.exit(1)

    meta = None
    with open(json_filename, "r") as f:
        meta = json.load(f)

    # only build a dictionnary will all graphs
    df = {}
    speakers = glob("./docs/*")
    for speaker in speakers:
        if not os.path.isdir(speaker):
            continue
        # humm annoying
        speaker_name = speaker.replace("./docs/", "")
        if speaker_name in ("score", "assets", "stats", "compare", "logos", "pictures"):
            continue
        df[speaker_name] = {}
        origins = glob(speaker + "/*")
        for origin in origins:
            if not os.path.isdir(origin):
                continue
            origin_name = os.path.basename(origin)
            df[speaker_name][origin_name] = {}
            defaults = glob(origin + "/*")
            for default in defaults:
                if not os.path.isdir(default):
                    continue
                default_name = os.path.basename(default)
                df[speaker_name][origin_name][default_name] = {}
                graphs = glob(default + "/*_large.png")
                for graph in graphs:
                    g = os.path.basename(graph).replace("_large.png", "")
                    df[speaker_name][origin_name][default_name][g] = {}

    # configure Mako
    mako_templates = TemplateLookup(
        directories=["src/website"], module_directory="/tmp/mako_modules"
    )

    # write index.html
    logger.info("Write index.html")
    index_html = mako_templates.get_template("index.html")

    def sort_meta_score(s):
        if (
            s is not None
            and "pref_rating" in s.keys()
            and "pref_score" in s["pref_rating"]
        ):
            return s["pref_rating"]["pref_score"]
        return -1

    def sort_meta_date(s):
        if s is not None:
            return s.get("review_published", "20170101")
        return "20170101"

    keys_sorted_date = sorted(
        meta,
        key=lambda a: sort_meta_date(
            meta[a]["measurements"].get(meta[a].get("default_measurement"))
        ),
        reverse=True,
    )
    keys_sorted_score = sorted(
        meta,
        key=lambda a: sort_meta_score(
            meta[a]["measurements"].get(meta[a].get("default_measurement"))
        ),
        reverse=True,
    )
    meta_sorted_score = {k: meta[k] for k in keys_sorted_score}
    meta_sorted_date = {k: meta[k] for k in keys_sorted_date}

    try:
        with open("docs/index.html", "w") as f:
            # by default sort by pref_rating decreasing
            f.write(
                index_html.render(
                    df=df, meta=meta_sorted_date, site=site, useSearch=True
                )
            )
            f.close()
    except KeyError as ke:
        print("Generating index.htmlfailed with {}".format(ke))
        sys.exit(1)

    # write eqs.html
    logger.info("Write eqs.html")
    eqs_html = mako_templates.get_template("eqs.html")

    try:
        with open("docs/eqs.html", "w") as f:
            # by default sort by pref_rating decreasing
            f.write(
                eqs_html.render(df=df, meta=meta_sorted_date, site=site, useSearch=True)
            )
            f.close()
    except KeyError as ke:
        print("Generating eqs.htmlfailed with {}".format(ke))
        sys.exit(1)

    # write various html files
    try:
        for item in ("scores",):
            item_name = "{0}.html".format(item)
            logger.info("Write {0}".format(item_name))
            item_html = mako_templates.get_template(item_name)
            with open("./docs/" + item_name, "w") as f:
                f.write(
                    item_html.render(
                        df=df, meta=meta_sorted_score, site=site, useSearch=True
                    )
                )
                f.close()
        for item in ("help", "compare", "statistics"):
            item_name = "{0}.html".format(item)
            logger.info("Write {0}".format(item_name))
            item_html = mako_templates.get_template(item_name)
            with open("./docs/" + item_name, "w") as f:
                f.write(
                    item_html.render(
                        df=df, meta=meta_sorted_score, site=site, useSearch=False
                    )
                )
                f.close()
    except KeyError as ke:
        print("Generating various html files failed with {}".format(ke))
        sys.exit(1)

    # write a file per speaker
    logger.info("Write a file per speaker")
    try:
        generate_speaker(mako_templates, df, meta=meta, site=site, useSearch=False)
    except KeyError as ke:
        print("Generating a file per speaker failed with {}".format(ke))
        sys.exit(1)

    # copy css/js files
    logger.info("Copy js/css files to docs")
    try:
        for item in ("misc",):
            item_name = "assets/{0}.js".format(item)
            logger.info("Write {0}".format(item_name))
            item_html = mako_templates.get_template(item_name)
            with open("./docs/" + item_name, "w") as f:
                f.write(item_html.render(df=df, meta=meta_sorted_score, site=site))
                f.close()
    except KeyError as ke:
        print("Generating various html files failed with {}".format(ke))
        sys.exit(1)
    # copy favicon(s)
    for f in [
        "favicon.ico",
        "favicon-16x16.png",
        "spinorama.css",
        "compare.js",
        "search.js",
        "index.js",
        "sort.js",
        "eqs.js",
        "scores.js",
        "statistics.js",
        "onload.js",
        "tabs.js",
        "graph.js",
        "zip.min.js",
        "downloadzip.js",
    ]:
        file_in = "./src/website/assets/" + f
        file_out = "./docs/assets/" + f
        shutil.copy(file_in, file_out)

    sys.exit(0)
