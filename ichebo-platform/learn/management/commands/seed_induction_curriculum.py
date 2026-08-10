"""
Seed the full induction curriculum into InductionStep, InductionQuestion,
and InductionAnswer.

Structure:
  Module 1 — Keys to the Kingdom          (pathway: all)
    Lesson 1, Quiz 1, Lesson 2, Quiz 2, Lesson 3, Quiz 3, Lesson 4, Quiz 4
    Module 1 Test

  Module 2 — Repentance / Reformation     (pathway: split)
    [beginners]      Lessons 5–8 + Quizzes 5–8
    [reconditioning] Lessons 9–11 + Quizzes 9–11
    Module 2 Test (pathway: all — same test, both groups)

  Module 3 — Secret to a Fulfilled Life   (pathway: all)
    Lessons 12–15 + Quizzes 12–15
    Module 3 Test

  Module 4 — The Sceptre Community        (pathway: all)
    Lessons 16–19 + Quizzes 16–19
    Final Test

Quizzes have 3 placeholder questions each (2 correct answers shown, 2 wrong).
Pass threshold: 70% throughout.

Usage:
    python manage.py seed_induction_curriculum
    python manage.py seed_induction_curriculum --force
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from learn.models import InductionStep, InductionQuestion, InductionAnswer

PASS_SCORE = 70
PLACEHOLDER_CONTENT = "Lesson content coming soon."

# ---------------------------------------------------------------------------
# Curriculum definition
# Each entry is a dict describing a step. Quizzes carry a 'questions' list.
# sequence_order is assigned automatically below.
# ---------------------------------------------------------------------------

CURRICULUM = [

    # ── Module 1: Keys to the Kingdom ──────────────────────────────────────
    {
        'module': 1, 'step_type': 'lesson', 'pathway': 'all',
        'title': 'Lesson 1: What is the Kingdom?',
    },
    {
        'module': 1, 'step_type': 'quiz', 'pathway': 'all',
        'title': 'Knowledge Check Quiz 1',
        'questions': [
            {
                'text': 'What does the Kingdom of God primarily refer to?',
                'answers': [
                    ('God\'s reign and rule over all creation', True),
                    ('A physical territory on earth', False),
                    ('A political nation state', False),
                    ('A religious building or institution', False),
                ],
            },
            {
                'text': 'Which of the following best describes the Kingdom of God?',
                'answers': [
                    ('God\'s active rule breaking into the present world', True),
                    ('A reward reserved only for the afterlife', False),
                    ('An abstract philosophical concept', False),
                    ('A membership organisation', False),
                ],
            },
            {
                'text': 'According to the lesson, the Kingdom of God is:',
                'answers': [
                    ('Both present now and fully coming in the future', True),
                    ('Entirely future — not yet arrived', False),
                    ('Entirely present — already fully here', False),
                    ('Only accessible to clergy', False),
                ],
            },
        ],
    },
    {
        'module': 1, 'step_type': 'lesson', 'pathway': 'all',
        'title': 'Lesson 2: How Do You Enter the Kingdom?',
    },
    {
        'module': 1, 'step_type': 'quiz', 'pathway': 'all',
        'title': 'Knowledge Check Quiz 2',
        'questions': [
            {
                'text': 'Entering the Kingdom of God requires:',
                'answers': [
                    ('Repentance and faith in Jesus Christ', True),
                    ('Being born into a Christian family', False),
                    ('Performing enough good works', False),
                    ('Attending church for a set number of years', False),
                ],
            },
            {
                'text': 'Jesus said "You must be born again" — this refers to:',
                'answers': [
                    ('A spiritual rebirth by the Spirit of God', True),
                    ('A physical second birth', False),
                    ('Reincarnation', False),
                    ('Baptism by water only', False),
                ],
            },
            {
                'text': 'Which of the following is the correct entry point into the Kingdom?',
                'answers': [
                    ('Receiving Jesus as Lord and turning from sin', True),
                    ('Being a morally good person', False),
                    ('Following all religious laws perfectly', False),
                    ('Being baptised as an infant', False),
                ],
            },
        ],
    },
    {
        'module': 1, 'step_type': 'lesson', 'pathway': 'all',
        'title': 'Lesson 3: How to Participate in the Kingdom?',
    },
    {
        'module': 1, 'step_type': 'quiz', 'pathway': 'all',
        'title': 'Knowledge Check Quiz 3',
        'questions': [
            {
                'text': 'Active participation in the Kingdom primarily involves:',
                'answers': [
                    ('Living under God\'s rule and representing His values', True),
                    ('Attending as many church services as possible', False),
                    ('Donating money to religious organisations', False),
                    ('Memorising scripture only', False),
                ],
            },
            {
                'text': 'Kingdom participation is best described as:',
                'answers': [
                    ('An active, daily alignment of life with God\'s purposes', True),
                    ('A passive state received at conversion', False),
                    ('Reserved for ordained ministers only', False),
                    ('Only relevant on Sundays', False),
                ],
            },
            {
                'text': 'Which of the following is a marker of Kingdom participation?',
                'answers': [
                    ('Bearing fruit that reflects God\'s character', True),
                    ('Social media activity about faith', False),
                    ('Knowledge of theology alone', False),
                    ('Number of years as a Christian', False),
                ],
            },
        ],
    },
    {
        'module': 1, 'step_type': 'lesson', 'pathway': 'all',
        'title': 'Lesson 4: How to Be a Part of the Kingdom Community?',
    },
    {
        'module': 1, 'step_type': 'quiz', 'pathway': 'all',
        'title': 'Knowledge Check Quiz 4',
        'questions': [
            {
                'text': 'The Kingdom community is centred around:',
                'answers': [
                    ('Covenant relationships and shared Kingdom purpose', True),
                    ('Common nationality or ethnicity', False),
                    ('Shared social activities', False),
                    ('Agreement on all theological details', False),
                ],
            },
            {
                'text': 'What makes a Kingdom community distinct from a social club?',
                'answers': [
                    ('Its foundation in the lordship of Christ and mutual formation', True),
                    ('It meets in a church building', False),
                    ('Members pay a subscription fee', False),
                    ('It is led by a professional minister', False),
                ],
            },
            {
                'text': 'Your role within the Kingdom community is best described as:',
                'answers': [
                    ('An active member contributing gifts and receiving formation', True),
                    ('A passive observer of other people\'s faith', False),
                    ('A consumer of spiritual content', False),
                    ('An independent believer with no obligation to others', False),
                ],
            },
        ],
    },
    {
        'module': 1, 'step_type': 'module_test', 'pathway': 'all',
        'title': 'Module 1 Test — Keys to the Kingdom',
        'questions': [
            {
                'text': 'The Kingdom of God refers to:',
                'answers': [
                    ('God\'s active reign over creation, present and coming', True),
                    ('A future place only accessible after death', False),
                    ('A human political organisation', False),
                    ('A set of rules to follow', False),
                ],
            },
            {
                'text': 'The primary entry point into the Kingdom is:',
                'answers': [
                    ('Repentance and faith in Jesus Christ', True),
                    ('Being a good person', False),
                    ('Religious heritage', False),
                    ('Intellectual agreement with Christian doctrine', False),
                ],
            },
            {
                'text': 'Kingdom participation involves:',
                'answers': [
                    ('Daily alignment of life with God\'s purposes and character', True),
                    ('Weekly church attendance only', False),
                    ('Financial giving to Christian causes', False),
                    ('Knowledge of the Bible without application', False),
                ],
            },
            {
                'text': 'Kingdom community is built on:',
                'answers': [
                    ('Covenant relationship and shared Kingdom purpose', True),
                    ('Shared cultural background', False),
                    ('Geographic proximity', False),
                    ('Agreement on every theological position', False),
                ],
            },
            {
                'text': 'Being "born again" as Jesus described means:',
                'answers': [
                    ('A spiritual rebirth enabling entry into the Kingdom', True),
                    ('A physical second birth', False),
                    ('A symbolic ritual with no inner change', False),
                    ('Reincarnation into a new body', False),
                ],
            },
        ],
    },

    # ── Module 2: Repentance / Reformation — Beginners track ───────────────
    {
        'module': 2, 'step_type': 'lesson', 'pathway': 'beginners',
        'title': 'Lesson 5: What is Grace?',
    },
    {
        'module': 2, 'step_type': 'quiz', 'pathway': 'beginners',
        'title': 'Knowledge Check Quiz 5',
        'questions': [
            {
                'text': 'Grace is best defined as:',
                'answers': [
                    ('God\'s unmerited favour given freely to humanity', True),
                    ('A reward for good behaviour', False),
                    ('A feeling of peace during prayer', False),
                    ('The effort a person makes to please God', False),
                ],
            },
            {
                'text': 'Grace is described as "unmerited" because:',
                'answers': [
                    ('It cannot be earned — it is a gift from God', True),
                    ('Only special people qualify for it', False),
                    ('It must be repaid through service', False),
                    ('It is given based on a person\'s religious effort', False),
                ],
            },
            {
                'text': 'According to scripture, salvation comes through:',
                'answers': [
                    ('Grace through faith — not by works', True),
                    ('Following all the commandments', False),
                    ('Being baptised in a specific church', False),
                    ('A combination of effort and God\'s help', False),
                ],
            },
        ],
    },
    {
        'module': 2, 'step_type': 'lesson', 'pathway': 'beginners',
        'title': 'Lesson 6: How to Accept Grace and How to Let Go?',
    },
    {
        'module': 2, 'step_type': 'quiz', 'pathway': 'beginners',
        'title': 'Knowledge Check Quiz 6',
        'questions': [
            {
                'text': 'Accepting grace requires:',
                'answers': [
                    ('Humility and willingness to receive what God freely gives', True),
                    ('Completing a set number of religious tasks', False),
                    ('Proving worthiness to God first', False),
                    ('Waiting until you have stopped sinning', False),
                ],
            },
            {
                'text': '"Letting go" in the context of grace means:',
                'answers': [
                    ('Releasing guilt, shame, and self-effort as the basis of acceptance', True),
                    ('Abandoning all personal responsibility', False),
                    ('Ignoring past mistakes entirely', False),
                    ('Stopping all spiritual practices', False),
                ],
            },
            {
                'text': 'The obstacle most people face in receiving grace is:',
                'answers': [
                    ('The belief that they must first deserve it', True),
                    ('Not knowing the right prayer formula', False),
                    ('Being in the wrong church', False),
                    ('Not having read the Bible enough', False),
                ],
            },
        ],
    },
    {
        'module': 2, 'step_type': 'lesson', 'pathway': 'beginners',
        'title': 'Lesson 7: How to Change Your Mind?',
    },
    {
        'module': 2, 'step_type': 'quiz', 'pathway': 'beginners',
        'title': 'Knowledge Check Quiz 7',
        'questions': [
            {
                'text': 'The biblical word for "repentance" (metanoia) literally means:',
                'answers': [
                    ('A change of mind — a new way of thinking', True),
                    ('Feeling sorry for sins', False),
                    ('Doing penance or self-punishment', False),
                    ('Making a public confession', False),
                ],
            },
            {
                'text': 'Genuine mind-change (repentance) results in:',
                'answers': [
                    ('A new direction and different choices over time', True),
                    ('Instant perfection', False),
                    ('Freedom from all temptation permanently', False),
                    ('No further need for God\'s grace', False),
                ],
            },
            {
                'text': 'The mind is renewed according to scripture through:',
                'answers': [
                    ('Engagement with God\'s word and the work of the Holy Spirit', True),
                    ('Willpower and self-discipline alone', False),
                    ('Religious rituals performed regularly', False),
                    ('Memorising theological statements', False),
                ],
            },
        ],
    },
    {
        'module': 2, 'step_type': 'lesson', 'pathway': 'beginners',
        'title': 'Lesson 8: The Narrow Road and Taking Up the Cross',
    },
    {
        'module': 2, 'step_type': 'quiz', 'pathway': 'beginners',
        'title': 'Knowledge Check Quiz 8',
        'questions': [
            {
                'text': 'Jesus described the path to life as:',
                'answers': [
                    ('Narrow — few find it', True),
                    ('Wide — open to everyone without conditions', False),
                    ('Only available to the religiously trained', False),
                    ('A gradual escalator requiring no choices', False),
                ],
            },
            {
                'text': '"Taking up the cross" means:',
                'answers': [
                    ('Daily choosing God\'s will over self-interest', True),
                    ('Wearing a cross as jewellery', False),
                    ('Only relevant to ordained ministers', False),
                    ('Suffering without purpose or meaning', False),
                ],
            },
            {
                'text': 'The narrow road requires:',
                'answers': [
                    ('Daily intentional commitment, not passive drifting', True),
                    ('Perfection before walking it', False),
                    ('Abandoning all enjoyment in life', False),
                    ('Isolation from non-Christians', False),
                ],
            },
        ],
    },

    # ── Module 2: Reconditioning track ─────────────────────────────────────
    {
        'module': 2, 'step_type': 'lesson', 'pathway': 'reconditioning',
        'title': 'Lesson 9: Wedding in Cana Framework',
    },
    {
        'module': 2, 'step_type': 'quiz', 'pathway': 'reconditioning',
        'title': 'Knowledge Check Quiz 9',
        'questions': [
            {
                'text': 'The Wedding at Cana (John 2) is used in this framework to illustrate:',
                'answers': [
                    ('Transformation — old things replaced by something new and better', True),
                    ('The importance of celebration', False),
                    ('Jesus\' first miracle as proof of divinity only', False),
                    ('The role of Mary in salvation', False),
                ],
            },
            {
                'text': 'In the Cana framework, the "water pots" represent:',
                'answers': [
                    ('Old religious forms ready to be filled with new Kingdom life', True),
                    ('Physical baptism', False),
                    ('Jewish law as permanently binding', False),
                    ('Empty religious practice with no hope of renewal', False),
                ],
            },
            {
                'text': 'For a reconditioning believer, the Cana framework calls for:',
                'answers': [
                    ('Openness to transformation of existing faith patterns', True),
                    ('Rejecting everything learned before', False),
                    ('Starting a completely new religion', False),
                    ('Passive waiting for God to act without personal response', False),
                ],
            },
        ],
    },
    {
        'module': 2, 'step_type': 'lesson', 'pathway': 'reconditioning',
        'title': 'Lesson 10: Ideological Relativism — Josiah\'s Framework',
    },
    {
        'module': 2, 'step_type': 'quiz', 'pathway': 'reconditioning',
        'title': 'Knowledge Check Quiz 10',
        'questions': [
            {
                'text': 'King Josiah\'s reformation is significant because he:',
                'answers': [
                    ('Rediscovered God\'s word and acted decisively to realign his nation', True),
                    ('Built the largest temple in Israel\'s history', False),
                    ('Conquered surrounding nations', False),
                    ('Was born into a godly family and maintained that heritage', False),
                ],
            },
            {
                'text': 'Ideological relativism in a Christian context refers to:',
                'answers': [
                    ('Blending cultural or personal preferences with Kingdom truth without discernment', True),
                    ('The belief that all religions lead to the same destination', False),
                    ('Rejecting all doctrine', False),
                    ('A theological position about biblical interpretation', False),
                ],
            },
            {
                'text': 'Josiah\'s framework challenges the reconditioning believer to:',
                'answers': [
                    ('Audit existing beliefs honestly against Kingdom truth', True),
                    ('Accept all previously held beliefs as valid', False),
                    ('Reject their entire spiritual history', False),
                    ('Adopt a new theological label', False),
                ],
            },
        ],
    },
    {
        'module': 2, 'step_type': 'lesson', 'pathway': 'reconditioning',
        'title': 'Lesson 11: Jonah\'s Manifesto',
    },
    {
        'module': 2, 'step_type': 'quiz', 'pathway': 'reconditioning',
        'title': 'Knowledge Check Quiz 11',
        'questions': [
            {
                'text': 'Jonah\'s story is relevant to reconditioning believers because it illustrates:',
                'answers': [
                    ('Resistance to God\'s call and the cost of running from transformation', True),
                    ('The importance of missionary work to foreign nations', False),
                    ('God\'s power over nature', False),
                    ('The superiority of Old Testament prophecy', False),
                ],
            },
            {
                'text': 'The key lesson of Jonah for the reconditioning journey is:',
                'answers': [
                    ('God\'s call cannot be permanently avoided — surrender leads to fruitfulness', True),
                    ('That reluctant obedience is unacceptable to God', False),
                    ('That God only uses willing people', False),
                    ('That spiritual failure disqualifies a person permanently', False),
                ],
            },
            {
                'text': 'Jonah\'s manifesto calls the reforming believer to:',
                'answers': [
                    ('Accept God\'s agenda even when it disrupts personal comfort', True),
                    ('Perform a specific religious act', False),
                    ('Become a cross-cultural missionary', False),
                    ('Study the book of Jonah in academic depth', False),
                ],
            },
        ],
    },

    # ── Module 2 Test (shared — both pathways sit here) ────────────────────
    {
        'module': 2, 'step_type': 'module_test', 'pathway': 'all',
        'title': 'Module 2 Test — Repentance / Reformation',
        'questions': [
            {
                'text': 'The biblical word "metanoia" (repentance) means:',
                'answers': [
                    ('A genuine change of mind and direction', True),
                    ('Feeling regret and guilt', False),
                    ('Performing acts of penance', False),
                    ('Making a public apology', False),
                ],
            },
            {
                'text': 'Grace is:',
                'answers': [
                    ('God\'s unmerited favour — freely given, not earned', True),
                    ('A reward for religious effort', False),
                    ('A feeling that accompanies prayer', False),
                    ('Only available to particularly holy people', False),
                ],
            },
            {
                'text': 'Taking up the cross daily means:',
                'answers': [
                    ('Consistently choosing God\'s will above self-interest', True),
                    ('Carrying a physical symbol of faith', False),
                    ('Suffering without hope or purpose', False),
                    ('Abandoning all personal ambition', False),
                ],
            },
            {
                'text': 'The reconditioning approach (Cana / Josiah / Jonah frameworks) is aimed at:',
                'answers': [
                    ('Existing Christians realigning their faith with Kingdom truth', True),
                    ('People with no prior faith background', False),
                    ('Ordained ministers only', False),
                    ('People who have left Christianity entirely', False),
                ],
            },
            {
                'text': 'Mind renewal according to scripture comes through:',
                'answers': [
                    ('Engaging with God\'s word and the work of the Holy Spirit', True),
                    ('Willpower and positive thinking alone', False),
                    ('Attending enough church services', False),
                    ('A one-time decision at conversion', False),
                ],
            },
        ],
    },

    # ── Module 3: Secret to a Fulfilled Life ───────────────────────────────
    {
        'module': 3, 'step_type': 'lesson', 'pathway': 'all',
        'title': 'Lesson 12: What is Purpose?',
    },
    {
        'module': 3, 'step_type': 'quiz', 'pathway': 'all',
        'title': 'Knowledge Check Quiz 12',
        'questions': [
            {
                'text': 'Purpose in a Kingdom context is best defined as:',
                'answers': [
                    ('God\'s specific design for a person\'s life and contribution', True),
                    ('A career goal chosen by the individual', False),
                    ('Happiness and personal fulfilment', False),
                    ('The accumulation of achievements and recognition', False),
                ],
            },
            {
                'text': 'According to the lesson, purpose is:',
                'answers': [
                    ('Discovered, not invented — it is given by God', True),
                    ('Created by each person for themselves', False),
                    ('Only relevant to full-time Christian workers', False),
                    ('The same for all Christians', False),
                ],
            },
            {
                'text': 'Living without purpose leads to:',
                'answers': [
                    ('Drift, frustration, and unfulfilled potential', True),
                    ('Freedom and flexibility', False),
                    ('Greater spiritual depth', False),
                    ('No significant consequences', False),
                ],
            },
        ],
    },
    {
        'module': 3, 'step_type': 'lesson', 'pathway': 'all',
        'title': 'Lesson 13: Pillars of Purpose',
    },
    {
        'module': 3, 'step_type': 'quiz', 'pathway': 'all',
        'title': 'Knowledge Check Quiz 13',
        'questions': [
            {
                'text': 'The pillars of purpose include:',
                'answers': [
                    ('Gifts, calling, character, and community contribution', True),
                    ('Income, status, education, and influence', False),
                    ('Age, nationality, denomination, and church role', False),
                    ('Personality type, career, and family background', False),
                ],
            },
            {
                'text': 'Which pillar connects personal gifts to Kingdom impact?',
                'answers': [
                    ('Calling — the specific application of gifts to God\'s purposes', True),
                    ('Personality type alone', False),
                    ('Educational qualifications', False),
                    ('Social network size', False),
                ],
            },
            {
                'text': 'Character is identified as a pillar of purpose because:',
                'answers': [
                    ('Gifts without character create harmful impact, not Kingdom fruit', True),
                    ('Character is the same as talent', False),
                    ('God only uses people of perfect character', False),
                    ('Character is irrelevant to ministry effectiveness', False),
                ],
            },
        ],
    },
    {
        'module': 3, 'step_type': 'lesson', 'pathway': 'all',
        'title': 'Lesson 14: Purpose in the Bible',
    },
    {
        'module': 3, 'step_type': 'quiz', 'pathway': 'all',
        'title': 'Knowledge Check Quiz 14',
        'questions': [
            {
                'text': 'Which biblical figure is most used in this lesson to illustrate purpose?',
                'answers': [
                    ('Lesson content coming soon — answer will be updated with content', True),
                    ('Placeholder A', False),
                    ('Placeholder B', False),
                    ('Placeholder C', False),
                ],
            },
            {
                'text': 'The Bible presents purpose as:',
                'answers': [
                    ('Central to every human life — not reserved for a spiritual elite', True),
                    ('Only applicable to prophets and apostles', False),
                    ('A New Testament concept only', False),
                    ('Something achieved by effort rather than received from God', False),
                ],
            },
            {
                'text': 'Scripture teaches that we are:',
                'answers': [
                    ('Created in Christ Jesus for good works prepared in advance', True),
                    ('Responsible for designing our own purpose from scratch', False),
                    ('Given purpose only after years of faithful service', False),
                    ('Purposeless until we discover a specific career', False),
                ],
            },
        ],
    },
    {
        'module': 3, 'step_type': 'lesson', 'pathway': 'all',
        'title': 'Lesson 15: Personal Development Fundamentals (HAF)',
    },
    {
        'module': 3, 'step_type': 'quiz', 'pathway': 'all',
        'title': 'Knowledge Check Quiz 15',
        'questions': [
            {
                'text': 'The Holistic Ability Framework (HAF) addresses:',
                'answers': [
                    ('Whole-person development — spirit, mind, body, and relationships', True),
                    ('Academic and professional achievement only', False),
                    ('Physical fitness as the primary goal', False),
                    ('Financial planning for Christians', False),
                ],
            },
            {
                'text': 'Holistic development means:',
                'answers': [
                    ('Growing in every dimension of life — not just one area', True),
                    ('Prioritising spiritual activities above all else', False),
                    ('Becoming an expert in a single field', False),
                    ('Ignoring the physical in favour of the spiritual', False),
                ],
            },
            {
                'text': 'Personal development in the Kingdom context is:',
                'answers': [
                    ('Stewardship of the life God has given for Kingdom purposes', True),
                    ('Self-improvement for personal success', False),
                    ('Optional for committed Christians', False),
                    ('Separate from spiritual formation', False),
                ],
            },
        ],
    },
    {
        'module': 3, 'step_type': 'module_test', 'pathway': 'all',
        'title': 'Module 3 Test — Secret to a Fulfilled Life',
        'questions': [
            {
                'text': 'Purpose in a Kingdom context is:',
                'answers': [
                    ('God\'s specific design for a person — discovered, not invented', True),
                    ('A career plan chosen by the individual', False),
                    ('The same for all Christians', False),
                    ('Only relevant to full-time ministry workers', False),
                ],
            },
            {
                'text': 'The pillars of purpose include:',
                'answers': [
                    ('Gifts, calling, character, and community contribution', True),
                    ('Income, education, and social status', False),
                    ('Church attendance and denominational membership', False),
                    ('Personality type and nationality', False),
                ],
            },
            {
                'text': 'The Holistic Ability Framework (HAF) focuses on:',
                'answers': [
                    ('Whole-person development across every dimension of life', True),
                    ('Physical fitness above all else', False),
                    ('Academic achievement only', False),
                    ('Financial prosperity', False),
                ],
            },
            {
                'text': 'Scripture says we are created for:',
                'answers': [
                    ('Good works prepared in advance by God', True),
                    ('Passive enjoyment of salvation', False),
                    ('Independence from community', False),
                    ('Self-determined goals', False),
                ],
            },
            {
                'text': 'Living without purpose leads to:',
                'answers': [
                    ('Drift, frustration, and unfulfilled potential', True),
                    ('Greater freedom and flexibility', False),
                    ('Deeper spirituality', False),
                    ('No significant long-term consequences', False),
                ],
            },
        ],
    },

    # ── Module 4: The Sceptre Community ────────────────────────────────────
    {
        'module': 4, 'step_type': 'lesson', 'pathway': 'all',
        'title': 'Lesson 16: Kingdom Mandate',
    },
    {
        'module': 4, 'step_type': 'quiz', 'pathway': 'all',
        'title': 'Knowledge Check Quiz 16',
        'questions': [
            {
                'text': 'The Kingdom Mandate refers to:',
                'answers': [
                    ('God\'s commission to humanity to represent and extend His rule', True),
                    ('A political campaign by Christian organisations', False),
                    ('A set of rules for church governance', False),
                    ('A financial giving commitment', False),
                ],
            },
            {
                'text': 'The mandate given to believers includes:',
                'answers': [
                    ('To disciple nations and demonstrate Kingdom values in all spheres', True),
                    ('To retreat from society and focus on personal holiness', False),
                    ('To build as many church buildings as possible', False),
                    ('To argue against other worldviews online', False),
                ],
            },
            {
                'text': 'The Kingdom Mandate is:',
                'answers': [
                    ('Collective — carried out by the whole community, not individuals alone', True),
                    ('Only for apostles and prophets', False),
                    ('Optional for ordinary believers', False),
                    ('Completed when a person gets baptised', False),
                ],
            },
        ],
    },
    {
        'module': 4, 'step_type': 'lesson', 'pathway': 'all',
        'title': 'Lesson 17: Occupy and Influence',
    },
    {
        'module': 4, 'step_type': 'quiz', 'pathway': 'all',
        'title': 'Knowledge Check Quiz 17',
        'questions': [
            {
                'text': '"Occupy" in a Kingdom context means:',
                'answers': [
                    ('Maintaining a Kingdom presence and influence in every sphere of society', True),
                    ('Taking over political institutions by force', False),
                    ('Only attending Christian gatherings', False),
                    ('Physically moving to a different country for mission', False),
                ],
            },
            {
                'text': 'Kingdom influence operates through:',
                'answers': [
                    ('Character, excellence, and Kingdom values demonstrated in daily life', True),
                    ('Loudly proclaiming Christian views on social media', False),
                    ('Withdrawing from mainstream society', False),
                    ('Converting workplaces into churches', False),
                ],
            },
            {
                'text': 'The spheres of society that Kingdom citizens are called to influence include:',
                'answers': [
                    ('All spheres — work, family, arts, government, education, and more', True),
                    ('Only the religious and charitable sector', False),
                    ('Only politics', False),
                    ('Only personal relationships', False),
                ],
            },
        ],
    },
    {
        'module': 4, 'step_type': 'lesson', 'pathway': 'all',
        'title': 'Lesson 18: Introduction to Sceptre Community',
    },
    {
        'module': 4, 'step_type': 'quiz', 'pathway': 'all',
        'title': 'Knowledge Check Quiz 18',
        'questions': [
            {
                'text': 'The Sceptre Community exists to:',
                'answers': [
                    ('Form, connect, and deploy Kingdom citizens in their sphere', True),
                    ('Provide a social network for Christians', False),
                    ('Replace the local church entirely', False),
                    ('Offer an online course platform', False),
                ],
            },
            {
                'text': 'Membership in the Sceptre Community involves:',
                'answers': [
                    ('Covenant commitment to formation, contribution, and Kingdom purposes', True),
                    ('Paying a subscription fee', False),
                    ('Being born into a Christian family', False),
                    ('Completing an academic course', False),
                ],
            },
            {
                'text': 'The Sceptre Community is structured around:',
                'answers': [
                    ('The Kingdom Governance System (KGS) and formation pathway', True),
                    ('A traditional denominational hierarchy', False),
                    ('A flat organisation with no leadership', False),
                    ('Geographic neighbourhoods only', False),
                ],
            },
        ],
    },
    {
        'module': 4, 'step_type': 'lesson', 'pathway': 'all',
        'title': 'Lesson 19: Introduction to the Kingdom Governance System (KGS)',
    },
    {
        'module': 4, 'step_type': 'quiz', 'pathway': 'all',
        'title': 'Knowledge Check Quiz 19',
        'questions': [
            {
                'text': 'The Kingdom Governance System (KGS) is:',
                'answers': [
                    ('A formation and leadership structure based on Kingdom principles', True),
                    ('A political lobbying organisation', False),
                    ('A replacement for civil government', False),
                    ('A financial management system', False),
                ],
            },
            {
                'text': 'Within the KGS, progression is based on:',
                'answers': [
                    ('Formation, character development, and demonstrated Kingdom fruitfulness', True),
                    ('Years of membership', False),
                    ('Financial contribution', False),
                    ('Academic qualifications', False),
                ],
            },
            {
                'text': 'The KGS is designed to:',
                'answers': [
                    ('Develop and deploy Kingdom citizens in every sphere of influence', True),
                    ('Create a separate Christian society isolated from the world', False),
                    ('Rank Christians by their holiness', False),
                    ('Manage church finances transparently', False),
                ],
            },
        ],
    },
    {
        'module': 4, 'step_type': 'final_test', 'pathway': 'all',
        'title': 'Final Test — Induction Programme',
        'questions': [
            {
                'text': 'The Kingdom of God refers to:',
                'answers': [
                    ('God\'s active reign — present now and fully coming in the future', True),
                    ('A future physical territory', False),
                    ('A human religious organisation', False),
                    ('A reward for the especially holy', False),
                ],
            },
            {
                'text': 'Entry into the Kingdom requires:',
                'answers': [
                    ('Repentance and faith in Jesus Christ', True),
                    ('Enough good works', False),
                    ('Christian heritage', False),
                    ('Membership of a specific church', False),
                ],
            },
            {
                'text': 'Grace is:',
                'answers': [
                    ('God\'s unmerited favour — freely given, not earned', True),
                    ('A reward for faithful service', False),
                    ('A feeling that accompanies spiritual experiences', False),
                    ('Available only to the repentant after sufficient suffering', False),
                ],
            },
            {
                'text': 'Purpose in a Kingdom context is:',
                'answers': [
                    ('God\'s specific design for a person — discovered, not invented', True),
                    ('A career plan a person creates for themselves', False),
                    ('Identical for all believers', False),
                    ('Only relevant to full-time ministers', False),
                ],
            },
            {
                'text': 'The Holistic Ability Framework (HAF) covers:',
                'answers': [
                    ('Whole-person development — spirit, mind, body, and relationships', True),
                    ('Physical fitness as the primary goal', False),
                    ('Academic achievement only', False),
                    ('Financial management for Christians', False),
                ],
            },
            {
                'text': 'The Kingdom Mandate calls believers to:',
                'answers': [
                    ('Represent and extend God\'s rule in every sphere of society', True),
                    ('Withdraw from society and focus on personal holiness', False),
                    ('Build as many church buildings as possible', False),
                    ('Focus exclusively on evangelism', False),
                ],
            },
            {
                'text': 'The Sceptre Community exists to:',
                'answers': [
                    ('Form, connect, and deploy Kingdom citizens in their sphere', True),
                    ('Provide a social network for Christians', False),
                    ('Replace the local church entirely', False),
                    ('Offer an academic course platform', False),
                ],
            },
            {
                'text': 'The Kingdom Governance System (KGS) develops members based on:',
                'answers': [
                    ('Formation, character, and demonstrated Kingdom fruitfulness', True),
                    ('Years of membership', False),
                    ('Financial contribution', False),
                    ('Educational qualifications', False),
                ],
            },
            {
                'text': '"Taking up the cross" means:',
                'answers': [
                    ('Daily choosing God\'s will above self-interest', True),
                    ('Wearing a religious symbol', False),
                    ('Suffering without hope or purpose', False),
                    ('Abandoning all personal ambition permanently', False),
                ],
            },
            {
                'text': 'Kingdom influence operates through:',
                'answers': [
                    ('Character, excellence, and Kingdom values in daily life', True),
                    ('Loudly proclaiming Christian positions on social media', False),
                    ('Withdrawing from mainstream society', False),
                    ('Converting secular workplaces into churches', False),
                ],
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed the full induction curriculum — steps, questions, and placeholder answers.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Delete all existing induction curriculum data and re-seed.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        force = options['force']

        if InductionStep.objects.exists():
            if not force:
                self.stdout.write(self.style.WARNING(
                    'Induction curriculum already seeded. Use --force to reset.'
                ))
                return
            InductionAnswer.objects.all().delete()
            InductionQuestion.objects.all().delete()
            InductionStep.objects.all().delete()
            self.stdout.write('  cleared existing curriculum')

        sequence = 0
        for entry in CURRICULUM:
            sequence += 1
            step = InductionStep.objects.create(
                module=entry['module'],
                sequence_order=sequence,
                step_type=entry['step_type'],
                pathway=entry['pathway'],
                title=entry['title'],
                content=PLACEHOLDER_CONTENT,
                pass_score=PASS_SCORE,
                is_active=True,
            )
            questions = entry.get('questions', [])
            for q_idx, q in enumerate(questions, start=1):
                question = InductionQuestion.objects.create(
                    step=step,
                    question_text=q['text'],
                    order=q_idx,
                )
                for a_idx, (text, correct) in enumerate(q['answers'], start=1):
                    InductionAnswer.objects.create(
                        question=question,
                        answer_text=text,
                        is_correct=correct,
                        order=a_idx,
                    )

            icon = {'lesson': '📖', 'quiz': '✏️', 'module_test': '📋', 'final_test': '🏁'}.get(
                entry['step_type'], '•'
            )
            self.stdout.write(
                f'  {icon} [{entry["pathway"]:>14}] seq={sequence:>2}  {entry["title"]}'
            )

        total_steps = InductionStep.objects.count()
        total_questions = InductionQuestion.objects.count()
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done. {total_steps} steps, {total_questions} questions seeded.'
        ))
