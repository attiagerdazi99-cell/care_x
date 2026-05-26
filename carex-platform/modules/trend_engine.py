import numpy as np


def calculate_trends(df):

    sbp_drop = df['sbp'].iloc[0] - df['sbp'].iloc[-1]
    lactate_rise = df['lactate'].iloc[-1] - df['lactate'].iloc[0]
    hr_rise = df['hr'].iloc[-1] - df['hr'].iloc[0]
    oxygen_rise = df['oxygen'].iloc[-1] - df['oxygen'].iloc[0]

    evolving_instability = False

    if sbp_drop > 15:
        evolving_instability = True

    if lactate_rise > 1:
        evolving_instability = True

    if hr_rise > 15:
        evolving_instability = True

    return {
        'sbp_drop': sbp_drop,
        'lactate_rise': lactate_rise,
        'hr_rise': hr_rise,
        'oxygen_rise': oxygen_rise,
        'evolving_instability': evolving_instability
    }
