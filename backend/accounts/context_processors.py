LEVEL_COLOURS = {
    0: 'level-grey',
    1: 'level-green',
    2: 'level-blue',
    3: 'level-purple',
    4: 'level-orange',
    5: 'level-red',
}

LEVEL_NAMES = {
    0: 'Seeker',
    1: 'Beginner',
    2: 'Disciple',
    3: 'Steward',
    4: 'Senior Steward',
    5: 'Architect',
}

APP_LEVEL_REQUIREMENTS = {
    'bible':      0,
    'learn':      0,
    'community':  0,  # Level 0 sees induction community only
    'records':    0,  # Level 0 can see records (induction-scoped)
    'activity':   0,  # Level 0 can track induction tasks
    'ministry':   1,
    'calendar':   1,
    'governance': 3,
    'paraclete':  1,
}


def formation(request):
    if not request.user.is_authenticated:
        return {
            'user_level': 0,
            'user_level_name': 'Guest',
            'user_level_colour': 'level-grey',
            'app_level_requirements': APP_LEVEL_REQUIREMENTS,
        }
    level = getattr(request.user, 'competence_level', 0)
    return {
        'user_level': level,
        'user_level_name': LEVEL_NAMES.get(level, f'Level {level}'),
        'user_level_colour': LEVEL_COLOURS.get(level, 'level-grey'),
        'app_level_requirements': APP_LEVEL_REQUIREMENTS,
    }
