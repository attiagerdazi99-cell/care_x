def generate_rationale(df, trends):

    rationale = []

    latest_sbp = df['sbp'].iloc[-1]
    latest_lactate = df['lactate'].iloc[-1]
    latest_hr = df['hr'].iloc[-1]

    if latest_sbp < 95:
        rationale.append(
            'Borderline hypotension may indicate worsening cardiovascular compensation.'
        )

    if latest_lactate > 2:
        rationale.append(
            'Rising lactate suggests evolving tissue hypoperfusion.'
        )

    if latest_hr > 110:
        rationale.append(
            'Persistent tachycardia suggests ongoing physiological stress.'
        )

    rationale.append(
        'Delayed escalation may increase risk of sudden decompensation.'
    )

    return rationale
