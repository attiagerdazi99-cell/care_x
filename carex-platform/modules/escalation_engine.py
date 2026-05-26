def determine_escalation(df, uncertainty):

    level = uncertainty['level']

    if level == 'LOW':

        return {
            'pathway': 'Observation',
            'actions': [
                'Repeat vitals',
                'Continue monitoring',
                'Repeat lactate'
            ]
        }

    elif level == 'MODERATE':

        return {
            'pathway': 'Senior Review',
            'actions': [
                'Urgent physician review',
                'Reduce reassessment interval',
                'Consider ICU discussion'
            ]
        }

    elif level == 'HIGH':

        return {
            'pathway': 'ICU Escalation',
            'actions': [
                'Initiate ICU consultation',
                'Prepare vasopressor support',
                'Consider invasive monitoring'
            ]
        }

    else:

        return {
            'pathway': 'Emergency Escalation',
            'actions': [
                'Immediate ICU transfer',
                'Start vasopressor support',
                'Activate critical care team'
            ]
        }
