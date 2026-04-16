# community/constants.py — KGS service orders, participation stages, competence labels

KGS_SERVICE_ORDERS = [
    # A — Apostolic & Spiritual Ministry
    ("Order of Apostolic Service",       "Apostolic & Spiritual Ministry"),
    ("Order of Prophetic Ministry",      "Apostolic & Spiritual Ministry"),
    ("Order of Teaching and Doctrine",   "Apostolic & Spiritual Ministry"),
    ("Order of Prayer and Intercession", "Apostolic & Spiritual Ministry"),
    # B — Leadership & Governance Support
    ("Order of Governance Support",          "Leadership & Governance Support"),
    ("Order of Strategic Coordination",      "Leadership & Governance Support"),
    ("Order of Leadership Assistance",       "Leadership & Governance Support"),
    ("Order of Communication and Alignment", "Leadership & Governance Support"),
    # C — Formation & Teaching
    ("Order of Discipleship Facilitation", "Formation & Teaching"),
    ("Order of Training and Instruction",  "Formation & Teaching"),
    ("Order of Mentorship and Coaching",   "Formation & Teaching"),
    ("Order of Curriculum Development",    "Formation & Teaching"),
    # D — Mission & Outreach
    ("Order of Evangelism",             "Mission & Outreach"),
    ("Order of Mission Teams",          "Mission & Outreach"),
    ("Order of Community Outreach",     "Mission & Outreach"),
    ("Order of Expansion and Planting", "Mission & Outreach"),
    # E — Community Life & Care
    ("Order of Pastoral Care",          "Community Life & Care"),
    ("Order of Community Building",     "Community Life & Care"),
    ("Order of Hospitality and Welcome","Community Life & Care"),
    ("Order of Welfare and Support",    "Community Life & Care"),
    # F — Operations & Stewardship
    ("Order of Administration",         "Operations & Stewardship"),
    ("Order of Resource Management",    "Operations & Stewardship"),
    ("Order of Logistics and Events",   "Operations & Stewardship"),
    ("Order of Media and Communication","Operations & Stewardship"),
]

KGS_SERVICE_ORDER_CHOICES = [(o[0], o[0]) for o in KGS_SERVICE_ORDERS]

KGS_PARTICIPATION_STAGES = {
    0: ("Seeker",          "Connection"),
    1: ("Beginner",        "Formation"),
    2: ("Disciple",        "Alignment"),
    3: ("Steward",         "Service"),
    4: ("Senior Steward",  "Leadership"),
    5: ("Architect",       "Apostolic Stewardship"),
}

KGS_COMPETENCE_LABELS = {
    0: "Seeker",
    1: "Beginner",
    2: "Disciple",
    3: "Steward",
    4: "Senior Steward",
    5: "Architect",
}
