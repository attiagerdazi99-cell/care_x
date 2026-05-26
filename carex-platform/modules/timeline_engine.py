def reconstruct_timeline(df):

    timeline = []

    for index, row in df.iterrows():

        event = ''

        if row['sbp'] < 100:
            event += 'Borderline hypotension. '

        if row['lactate'] > 2:
            event += 'Lactate rising. '

        if row['hr'] > 110:
            event += 'Persistent tachycardia. '

        timeline.append({
            'time': row['time'],
            'event': event
        })

    return timeline
