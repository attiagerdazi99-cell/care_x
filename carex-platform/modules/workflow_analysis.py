import pandas as pd


def workflow_metrics(df):

    warning_start = df[df['sbp'] < 100].index[0]

    escalation_time = df[df['sbp'] < 90].index[0]

    delay = escalation_time - warning_start

    return {
        'warning_to_escalation_interval': delay,
        'median_escalation_delay': delay,
        'delayed_escalation_risk': 'HIGH' if delay > 2 else 'MODERATE'
    }
