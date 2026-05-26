def generate_interpretation(df, trends):

    latest_sbp = df['sbp'].iloc[-1]
    latest_lactate = df['lactate'].iloc[-1]

    if latest_sbp < 90 and latest_lactate > 3:

        return (
            'This patient demonstrates evolving hemodynamic instability '
            'with signs of worsening tissue hypoperfusion.'
        )

    elif latest_lactate > 2:

        return (
            'Although overt shock is not yet fully established, '
            'the current pattern raises concern for delayed cardiovascular '
            'decompensation.'
        )

    else:

        return (
            'Persistent abnormalities despite transient physiological '
            'compensation may justify earlier escalation.'
        )
