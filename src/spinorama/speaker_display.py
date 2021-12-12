# -*- coding: utf-8 -*-
import logging
import altair as alt
import numpy as np
import pandas as pd
import datas.metadata as metadata
from .compute_normalize import resample
from .compute_estimates import estimates
from .compute_scores import speaker_pref_rating
from .plot import (
    plot_params_default,
    contour_params_default,
    plot_spinorama,
    plot_graph,
    plot_graph_regression,
    plot_contour,
    plot_radar,
    plot_image,
    plot_summary,
    plot_compare_spinorama,
    plot_compare_graph,
    plot_compare_graph_regression,
)

logger = logging.getLogger("spinorama")


alt.data_transformers.disable_max_rows()


def display_spinorama(df, graph_params=plot_params_default):
    spin = df.get("CEA2034_unmelted")
    if spin is None:
        logger.info("Display CEA2034 not in dataframe {0}".format(df.keys()))
        return None
    return plot_spinorama(spin, graph_params)


def display_reflection_early(df, graph_params=plot_params_default):
    try:
        if "Early Reflections_unmelted" not in df.keys():
            return None
        return plot_graph(df["Early Reflections_unmelted"], graph_params)
    except KeyError as ke:
        logger.warning("Display Early Reflections failed with {0}".format(ke))
        return None


def display_onaxis(df, graph_params=plot_params_default):
    try:
        onaxis = None
        if "CEA2034_unmelted" in df.keys():
            return plot_graph_regression(
                df["CEA2034_unmelted"], "On Axis", graph_params
            )
        elif "On Axis_unmelted" in df.keys():
            return plot_graph_regression(df["On Axis"], "On Axis", graph_params)
        else:
            return None
    except KeyError as ke:
        logger.warning("Display On Axis failed with {0}".format(ke))
        return None
    except AttributeError as ae:
        logger.warning("Display On Axis failed with {0}".format(ae))
        return None


def display_inroom(df, graph_params=plot_params_default):
    try:
        if "Estimated In-Room Response_unmelted" not in df.keys():
            return None
        return plot_graph_regression(
            df["Estimated In-Room Response_unmelted"],
            "Estimated In-Room Response",
            graph_params,
        )
    except KeyError as ke:
        logger.warning("Display In Room failed with {0}".format(ke))
        return None


def display_reflection_horizontal(df, graph_params=plot_params_default):
    try:
        if "Horizontal Reflections_unmelted" not in df.keys():
            return None
        return plot_graph(df["Horizontal Reflections_unmelted"], graph_params)
    except KeyError as ke:
        logger.warning("Display Horizontal Reflections failed with {0}".format(ke))
        return None


def display_reflection_vertical(df, graph_params=plot_params_default):
    try:
        if "Vertical Reflections_unmelted" not in df.keys():
            return None
        return plot_graph(df["Vertical Reflections_unmelted"], graph_params)
    except KeyError:
        return None


def display_spl(df, axis, graph_params=plot_params_default):
    try:
        if axis not in df.keys():
            return None
        spl = df[axis].loc[
            :, {"Freq", "On Axis", "10°", "20°", "30°", "40°", "50°", "60°"}
        ]
        # print('spl {}'.format(spl.keys()))
        return plot_graph(spl, graph_params)
    except KeyError as ke:
        logger.warning("Display SPL failed with {0}".format(ke))
        return None


def display_spl_horizontal(df, graph_params=plot_params_default):
    return display_spl(df, "SPL Horizontal_unmelted", graph_params)


def display_spl_vertical(df, graph_params=plot_params_default):
    return display_spl(df, "SPL Vertical_unmelted", graph_params)


def display_spl_horizontal_normalized(df, graph_params=plot_params_default):
    return display_spl(df, "SPL Horizontal_normalized_unmelted", graph_params)


def display_spl_vertical_normalized(df, graph_params=plot_params_default):
    return display_spl(df, "SPL Vertical_normalized_unmelted", graph_params)


def display_contour(df, direction, graph_params=contour_params_default):
    # print('Display SPL: {} {}'.format(direction, df.keys()))
    if direction not in df.keys():
        return None
    return plot_contour(df[direction], graph_params)


def display_contour_horizontal(df, graph_params=contour_params_default):
    return display_contour(df, "SPL Horizontal_unmelted", graph_params)


def display_contour_vertical(df, graph_params=contour_params_default):
    return display_contour(df, "SPL Vertical_unmelted", graph_params)


def display_contour_horizontal_normalized(df, graph_params=contour_params_default):
    spl = df["SPL Horizontal_normalized_unmelted"]
    # print('Display SPL: {}'.format(spl.keys()))
    # for k in spl.keys():
    #    if k != 'Freq':
    #        print('{} min {} max {}'.format(
    #            k,
    #            np.min(spl[k]),
    #            np.max(spl[k])))
    return display_contour(df, "SPL Horizontal_normalized_unmelted", graph_params)


def display_contour_vertical_normalized(df, graph_params=contour_params_default):
    return display_contour(df, "SPL Vertical_normalized_unmelted", graph_params)


def display_radar(df, direction, graph_params):
    dfs = df.get(direction)
    if dfs is None:
        return None
    return plot_radar(dfs, graph_params)


def display_radar_horizontal(df, graph_params=plot_params_default):
    return display_radar(df, "SPL Horizontal_unmelted", graph_params)


def display_radar_vertical(df, graph_params=plot_params_default):
    return display_radar(df, "SPL Vertical_unmelted", graph_params)


def display_compare(df, graph_filter, graph_params=plot_params_default):
    def augment(dfa, name):
        # print(name)
        namearray = [name for i in range(0, len(dfa))]
        dfa["Speaker"] = namearray
        return dfa

    try:
        source = pd.concat(
            [
                augment(
                    resample(
                        df[speaker][origin][key][graph_filter], 1000
                    ),  # max 1000 Freq points to minimise space
                    "{0} - {1} - {2}".format(speaker, origin, key),
                )
                for speaker in df.keys()
                for origin in df[speaker].keys()
                for key in df[speaker][origin].keys()
                if df is not None
                and df[speaker] is not None
                and df[speaker][origin] is not None
                and df[speaker][origin][key] is not None
                and graph_filter in df[speaker][origin][key]
            ]
        )

        speaker1 = "KEF LS50 - ASR - asr"
        speaker2 = "KEF LS50 - Princeton - princeton"

        if graph_filter == "CEA2034":
            graph = plot_compare_spinorama(source, graph_params, speaker1, speaker2)
        elif graph_filter in ("On Axis", "Estimated In-Room Response"):
            graph = plot_compare_graph_regression(
                source, graph_params, speaker1, speaker2
            )
        else:
            graph = plot_compare_graph(source, graph_params, speaker1, speaker2)
        return graph
    except KeyError as e:
        logger.warning("failed for {0} with {1}".format(graph_filter, e))
        return None
    except ValueError as e:
        logger.warning("failed for {0} with {1}".format(graph_filter, e))
        return None


def display_summary(df, params, speaker, origin, key):
    try:
        speaker_type = ""
        speaker_shape = ""
        if speaker in metadata.speakers_info.keys():
            speaker_type = metadata.speakers_info[speaker].get("type", "")
            speaker_shape = metadata.speakers_info[speaker].get("shape", "")

        if "CEA2034" not in df.keys():
            return None
        spin = df["CEA2034"]
        splH = df.get("SPL Horizontal_unmelted", None)
        splV = df.get("SPL Vertical_unmelted", None)
        est = estimates(spin, splH, splV)

        # 1
        speaker_summary = [
            "{0} {1}".format(speaker_shape.capitalize(), speaker_type.capitalize())
        ]

        if est is None:
            #                    2   3   4   5   6   7   8
            speaker_summary += ["", "", "", "", "", "", ""]
        else:
            # 2, 3
            if "ref_level" in est.keys():
                speaker_summary += [
                    "• Reference level {0} dB".format(est["ref_level"]),
                    "(mean over {0}-{1}k Hz)".format(
                        int(est["ref_from"]), int(est["ref_to"]) / 1000
                    ),
                ]
            else:
                speaker_summary += ["", ""]

            # 4
            if "ref_3dB" in est.keys():
                speaker_summary += ["• -3dB at {0}Hz wrt Ref.".format(est["ref_3dB"])]
            else:
                speaker_summary += [""]

            # 5
            if "ref_6dB" in est.keys():
                speaker_summary += ["• -6dB at {0}Hz wrt Ref.".format(est["ref_6dB"])]
            else:
                speaker_summary += [""]

            # 6
            if "ref_band" in est.keys():
                speaker_summary += ["• +/-{0}dB wrt Ref.".format(est["ref_band"])]
            else:
                speaker_summary += [""]

            # 7
            if "dir_horizontal_p" in est.keys() and "dir_horizontal_m" in est.keys():
                speaker_summary += [
                    "• Horizontal directivity ({}°, {}°)".format(
                        int(est["dir_horizontal_m"]), int(est["dir_horizontal_p"])
                    )
                ]
            else:
                speaker_summary += [""]

            # 8
            if "dir_vertical_p" in est.keys() and "dir_vertical_m" in est.keys():
                speaker_summary += [
                    "• Vertical directivity ({}°, {}°)".format(
                        int(est["dir_vertical_m"]), int(est["dir_vertical_p"])
                    )
                ]
            else:
                speaker_summary += [""]

        pref_score = None
        if "Estimated In-Room Response" in df.keys():
            inroom = df["Estimated In-Room Response"]
            if inroom is not None:
                pref_score = speaker_pref_rating(spin, inroom)

        # 9-17
        if pref_score is not None:
            speaker_summary += [
                "Preference score: {0}".format(pref_score.get("pref_score", "--")),
                "• Low Frequency:",
                "  • Extension: {0} Hz".format(pref_score.get("lfx_hz", "--")),
                "  • Quality : {0}".format(pref_score.get("lfq", "--")),
                "• Narrow Bandwidth Deviation",
                "  • On Axis: {0}".format(pref_score.get("nbd_on_axis", "--")),
                "  • Predicted In-Room: {0}".format(
                    pref_score.get("nbd_pred_in_room", "--")
                ),
                "• SM Deviation:",
                "  • Predicted In-Room: {0}".format(
                    pref_score.get("sm_pred_in_room", "--")
                ),
            ]
        else:
            #                    9  10  11  12, 13, 14, 15  16  17
            speaker_summary += ["", "", "", "", "", "", "", "", ""]

        if len(speaker_summary) != 17:
            logger.error(
                "speaker summary lenght is incorrect {0}".format(speaker_summary)
            )

        return plot_summary(speaker, speaker_summary, params)
    except KeyError as ke:
        logger.warning("Display Summary failed with {0}".format(ke))
        return None


def display_pict(speaker, params):
    return plot_image(speaker, params)
