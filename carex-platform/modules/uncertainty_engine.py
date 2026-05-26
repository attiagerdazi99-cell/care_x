
def calculate_uncertainty(df, trends):

    latest_sbp = df['sbp'].iloc[-1]
    latest_lactate = df['lactate'].iloc[-1]
    latest_hr = df['hr'].iloc[-1]

    score = 0

    if latest_sbp < 95:
        score += 2

    if latest_lactate > 2:
        score += 2

    if latest_hr > 110:
        score += 2

    if trends['lactate_rise'] > 1:
        score += 2

    if score <= 2:
        level = 'LOW'
        message = 'Current abnormalities remain clinically reassuring.'

    elif score <= 5:
        level = 'MODERATE'
        message = 'Current findings may represent evolving instability, but overt shock criteria remain incomplete.'

    elif score <= 7:
        level = 'HIGH'
        message = 'Progressive abnormalities increase concern for delayed decompensation despite transient compensation.'

    else:
        level = 'CRITICAL'
        message = 'Persistent deterioration strongly raises concern for impending cardiovascular collapse.'

    return {
        'score': score,
        'level': level,
        'message': message
    }
