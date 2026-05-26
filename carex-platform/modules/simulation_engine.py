def simulate_scenario(sbp, lactate, oxygen, hr):

    messages = []

    if sbp > 95:
        messages.append(
            'Transient blood pressure improvement may not fully resolve concern if lactate continues worsening.'
        )

    if lactate > 3:
        messages.append(
            'Persistent lactate elevation substantially increases concern for worsening hypoperfusion.'
        )

    if oxygen > 4:
        messages.append(
            'Increasing oxygen requirement suggests progressive multisystem deterioration.'
        )

    if hr > 120:
        messages.append(
            'Persistent tachycardia despite intervention may justify earlier escalation.'
        )

    return messages
