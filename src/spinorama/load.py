# -*- coding: utf-8 -*-
import logging
import numpy as np
import pandas as pd

from .compute_cea2034 import (
    early_reflections,
    vertical_reflections,
    horizontal_reflections,
    compute_cea2034,
    compute_onaxis,
    estimated_inroom,
    estimated_inroom_HV,
)

from .load_misc import graph_melt, sort_angles
from .compute_misc import unify_freq

logger = logging.getLogger("spinorama")


def shift_spl(spl, mean):
    # shift all measurement by means
    df = pd.DataFrame()
    for k in spl.keys():
        if k == "Freq":
            df[k] = spl[k]
        else:
            df[k] = spl[k] - mean
        if k == "180°" and "-180°" not in df.keys():
            df.insert(1, "-180°", spl["180°"] - mean)
    return df


def shift_spl_melted(spl, mean):
    # shift all measurement by means
    df = spl.copy()
    df.dB -= mean
    return df


def shift_spl_melted_cea2034(spl, mean):
    # spl
    # print(spl.head())
    # for k in spl.keys():
    #    count = spl[k].isna().sum().sum()
    #    print('{} {}'.format(k, count))
    # shift all measurement by means
    df = pd.DataFrame({"Freq": spl.loc[spl.Measurements == "On Axis"].Freq})
    for col in set(spl.Measurements):
        # print(spl.loc[spl.Measurements == col].dB)
        if "DI" in col:
            df[col] = spl.loc[spl.Measurements == col].dB.values
        else:
            df[col] = spl.loc[spl.Measurements == col].dB.values - mean
    # print('melted_cea {} {}'.format(mean, df.keys()))
    # print(df.head())
    # for k in df.keys():
    #    count = df[k].isna().sum().sum()
    #    print('{} {}'.format(k, count))
    return graph_melt(df)


def norm_spl(spl):
    # nornalize v.s. on axis
    df = pd.DataFrame({"Freq": spl.Freq})
    for k in spl.keys():
        if k != "Freq" and k != "On Axis":
            df[k] = spl[k] - spl["On Axis"]
    df["On Axis"] = 0
    return df


def filter_graphs(speaker_name, h_spl, v_spl):
    dfs = {}
    # add H and V SPL graphs
    mean = None
    sv_spl = None
    sh_spl = None
    if h_spl is not None:
        mean = np.mean(h_spl.loc[(h_spl.Freq > 300) & (h_spl.Freq < 3000)]["On Axis"])
        sh_spl = shift_spl(h_spl, mean)
        dfs["SPL Horizontal"] = graph_melt(sh_spl)
        dfs["SPL Horizontal_unmelted"] = sh_spl
        dfs["SPL Horizontal_normalized_unmelted"] = norm_spl(sh_spl)
    else:
        logger.info("h_spl is None for speaker {}".format(speaker_name))

    if v_spl is not None:
        if mean is None:
            mean = np.mean(
                v_spl.loc[(v_spl.Freq > 300) & (v_spl.Freq < 3000)]["On Axis"]
            )
        sv_spl = shift_spl(v_spl, mean)
        dfs["SPL Vertical"] = graph_melt(sv_spl)
        dfs["SPL Vertical_unmelted"] = sv_spl
        dfs["SPL Vertical_normalized_unmelted"] = norm_spl(sv_spl)
    else:
        logger.info("v_spl is None for speaker {}".format(speaker_name))

    # add computed graphs
    table = [
        ["Early Reflections", early_reflections],
        ["Horizontal Reflections", horizontal_reflections],
        ["Vertical Reflections", vertical_reflections],
        ["Estimated In-Room Response", estimated_inroom_HV],
        ["On Axis", compute_onaxis],
        ["CEA2034", compute_cea2034],
    ]

    if sh_spl is None or sv_spl is None:
        #
        df = compute_onaxis(sh_spl, sv_spl)
        dfs["On Axis_unmelted"] = df
        dfs["On Axis"] = graph_melt(df)
        # SPL H
        if sh_spl is not None:
            df = horizontal_reflections(sh_spl, sv_spl)
            dfs["Horizontal Reflections_unmelted"] = df
            dfs["Horizontal Reflections"] = graph_melt(df)
        # SPL V
        if sv_spl is not None:
            df = vertical_reflections(sh_spl, sv_spl)
            dfs["Vectical Reflections_unmelted"] = df
            dfs["Vectical Reflections"] = graph_melt(df)
        # that's all folks
        return dfs

    for title, functor in table:
        try:
            df = functor(sh_spl, sv_spl)
            if df is not None:
                dfs[title + "_unmelted"] = df
                dfs[title] = graph_melt(df)
            else:
                logger.info(
                    "{0} computation is None for speaker{1:s}".format(
                        title, speaker_name
                    )
                )
        except KeyError as ke:
            logger.warning(
                "{0} computation failed with key:{1} for speaker{2:s}".format(
                    title, ke, speaker_name
                )
            )

    # print(
    #    "min {} max {}".format(
    #        np.min(dfs["CEA2034_unmelted"]["On Axis"]),
    #        np.max(dfs["CEA2034_unmelted"]["On Axis"]),
    #    )
    # )
    return dfs


def filter_graphs_partial(df):
    dfs = {}
    # normalize first
    mean = None
    on = None
    if "CEA2034" in df:
        on = df["CEA2034"]
    if on is None and "On Axis" in df and "On Axis" in df["On Axis"]:
        on = df["On Axis"]
    if on is not None:
        mean = np.mean(
            on.loc[
                (on.Freq > 300) & (on.Freq < 3000) & (on.Measurements == "On Axis")
            ].dB
        )
        for k in df.keys():
            if k == "CEA2034":
                aligned = graph_melt(unify_freq(df[k]))
                dfs[k] = shift_spl_melted_cea2034(aligned, mean)
            else:
                dfs[k] = shift_spl_melted(df[k], mean)
    else:
        for k in df.keys():
            dfs[k] = df[k]

    for k in df.keys():
        dfs["{}_unmelted".format(k)] = (
            dfs[k]
            .pivot_table(index="Freq", columns="Measurements", values="dB", aggfunc=max)
            .reset_index()
        )
    # print('filter in: keys={} out: mean={} keys={}'.format(df.keys(), mean, dfs.keys()))
    return dfs


def parse_graph_freq_check(speaker_name: str, df_spin: pd.DataFrame) -> bool:
    status = True
    spin_cols = set(df_spin.Measurements.values)
    mandatory_cols = ("Listening Window", "On Axis", "Early Reflections", "Sound Power")
    other_cols = ("Early Reflections DI", "Sound Power DI")
    for col in mandatory_cols:
        if col not in spin_cols:
            logger.info(
                "{} measurement doesn't have a {} column".format(speaker_name, col)
            )
            status = False
        else:
            logging.debug(
                "Loading {:s} {:s} {:.1f}--{:.1f}Hz {:.1f}--{:.1f}dB".format(
                    speaker_name,
                    col,
                    df_spin.loc[df_spin.Measurements == col].Freq.min(),
                    df_spin.loc[df_spin.Measurements == col].Freq.max(),
                    df_spin.loc[df_spin.Measurements == col].dB.min(),
                    df_spin.loc[df_spin.Measurements == col].dB.max(),
                )
            )
    for col in spin_cols:
        if col not in mandatory_cols and col not in other_cols:
            logger.warning(
                "{} measurement have extra column {}".format(speaker_name, col)
            )
    return status


def spin_compute_di_eir(
    speaker_name: str, title: str, spin_uneven: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    dfs = {}
    # some checks
    if title != "CEA2034":
        logger.debug("title is {0}".format(title))
        return {}

    if not parse_graph_freq_check(speaker_name, spin_uneven):
        dfs[title] = spin_uneven
        return dfs

    spin_even = unify_freq(spin_uneven)
    spin = graph_melt(spin_even)

    if spin is None:
        logger.error("spin is None")
        return {}

    # compute EIR
    on = spin.loc[spin["Measurements"] == "On Axis"].reset_index(drop=True)
    lw = spin.loc[spin["Measurements"] == "Listening Window"].reset_index(drop=True)
    er = spin.loc[spin["Measurements"] == "Early Reflections"].reset_index(drop=True)
    sp = spin.loc[spin["Measurements"] == "Sound Power"].reset_index(drop=True)

    # check DI index
    if 0 not in (lw.shape[0], sp.shape[0]):
        sp_di_computed = lw.dB - sp.dB
        sp_di = spin.loc[spin["Measurements"] == "Sound Power DI"].reset_index(
            drop=True
        )
        if sp_di.shape[0] == 0:
            logger.debug("No Sound Power DI curve, computing one!")
            df2 = pd.DataFrame(
                {
                    "Freq": on.Freq,
                    "dB": sp_di_computed,
                    "Measurements": "Sound Power DI",
                }
            )
            spin = spin.append(df2).reset_index(drop=True)
        else:
            delta = np.mean(sp_di) - np.mean(sp_di_computed)
            logger.debug("Sound Power DI curve: removing {0}".format(delta))
            spin.loc[spin["Measurements"] == "Sound Power DI", "dB"] -= delta

        # sp_di = spin.loc[spin['Measurements'] == 'Sound Power DI'].reset_index(drop=True)
        logger.debug(
            "Post treatment SP DI: shape={0} min={1} max={2}".format(
                sp_di.shape, sp_di_computed.min(), sp_di_computed.max()
            )
        )
        # print(sp_di)
    else:
        logger.debug("Shape LW={0} SP={1}".format(lw.shape, sp.shape))

    if 0 not in (lw.shape[0], er.shape[0]):
        er_di_computed = lw.dB - er.dB
        er_di = spin.loc[spin["Measurements"] == "Early Reflections DI"].reset_index(
            drop=True
        )
        if er_di.shape[0] == 0:
            logger.debug("No Early Reflections DI curve!")
            df2 = pd.DataFrame(
                {
                    "Freq": on.Freq,
                    "dB": er_di_computed,
                    "Measurements": "Early Reflections DI",
                }
            )
            spin = spin.append(df2).reset_index(drop=True)
        else:
            delta = np.mean(er_di) - np.mean(er_di_computed)
            logger.debug("Early Reflections DI curve: removing {0}".format(delta))
            spin.loc[spin["Measurements"] == "Early Reflections DI", "dB"] -= delta

        # er_di = spin.loc[spin['Measurements'] == 'Early Reflections DI'].reset_index(drop=True)
        logger.debug(
            "Post treatment ER DI: shape={0} min={1} max={2}".format(
                er_di.shape, er_di_computed.min(), er_di_computed.max()
            )
        )
        # print(er_di)
    else:
        logger.debug("Shape LW={0} ER={1}".format(lw.shape, er.shape))

    di_offset = spin.loc[spin["Measurements"] == "DI offset"].reset_index(drop=True)
    if di_offset.shape[0] == 0:
        logger.debug("No DI offset curve!")
        df2 = pd.DataFrame({"Freq": on.Freq, "dB": 0, "Measurements": "DI offset"})
        spin = spin.append(df2).reset_index(drop=True)

    logger.debug(
        "Shape ON {0} LW {1} ER {2} SP {3}".format(
            on.shape, lw.shape, er.shape, sp.shape
        )
    )
    if 0 not in (lw.shape[0], er.shape[0], sp.shape[0]):
        eir = estimated_inroom(lw, er, sp)
        logger.debug("eir {0}".format(eir.shape))
        # print(eir)
        dfs["Estimated In-Room Response"] = graph_melt(eir)
    else:
        logger.debug("Shape LW={0} ER={1} SP={2}".format(lw.shape, er.shape, sp.shape))

    # add spin (at the end because we could have modified DI curves
    dfs[title] = spin

    if on.isna().values.any():
        logger.error("On Axis has NaN values")

    return dfs


def symmetrise_measurement(spl: pd.DataFrame) -> pd.DataFrame:
    if spl.empty:
        return pd.DataFrame()

    # look for min and max
    cols = spl.columns
    min_angle = 180
    max_angle = -180
    for col in cols:
        if col != "Freq":
            angle = None
            if col == "On Axis":
                angle = 0
            else:
                angle = int(col[:-1])
            min_angle = min(min_angle, angle)
            max_angle = max(max_angle, angle)
    logger.debug("min {} max {}".format(min_angle, max_angle))

    # extend 0-180 to -170 0 180
    # extend 0-90  to -90 to 90
    new_spl = spl.copy()
    for col in cols:
        if col not in ("Freq", "On Axis", "180°") and col[0] != "-":
            mangle = "-{}".format(col)
            if mangle not in spl.columns:
                new_spl[mangle] = spl[col]
    return sort_angles(new_spl)
