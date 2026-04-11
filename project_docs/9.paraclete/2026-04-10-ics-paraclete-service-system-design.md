**ICS PLATFORM**

System Design Document

**Task 6.1 --- Paraclete Service**

Version 1.0 · 2026-04-10

Data Contract Reference: v9

Phase 6 of 8 --- Entry requirement: Phase 3 complete (Activity Engine)

**Integrated Community System**

**1. Overview**

Paraclete is the intelligence layer of the ICS platform. Its purpose is to answer one question for each user, every day: What should I be paying attention to right now? It does this by reading the full state of the user\'s data across engines and surfacing a curated, role-aware digest.

The name Paraclete --- Helper, Advocate, Counsellor --- is theologically intentional. It should feel like a wise steward who has read everything and is presenting what matters, not a notification feed or a to-do list.

**1.1 Architecture Position**

Paraclete sits between the Activity Engine (Phase 3) and the Dashboard (Phase 7). It is a read-only Python orchestration module --- it reads from the Django ORM directly and never writes to any table in MVP.

  ----------------------- --- ----------------------------------------------------------------------------
  **Layer**                   **Detail**

  **KGS Framework**       ↓   Defines formation pathways, pillars, competence levels

  **Activity Engine**     ↓   Produces Activity, ActivityLog records --- primary Paraclete data source

  **Records Engine**      ↓   Produces Record objects --- Learn progress, DAR entries

  **Paraclete Service**   ↓   paraclete/service.py --- reads ORM, applies rules, returns ParacleteDigest

  **Paraclete API**       ↓   DRF endpoints --- serialise digest to JSON, enforce auth

  **Dashboard**               Phase 7 --- consumes digest, renders role-aware widgets
  ----------------------- --- ----------------------------------------------------------------------------

**1.2 Locked Decisions**

The following architectural decisions are locked and must not be re-opened during implementation:

-   Paraclete is rule-based in MVP. paraclete/service.py is pure Python --- reads Django ORM directly, applies logic, returns a ParacleteDigest. No LLM calls in MVP.

-   Paraclete reads only. It never writes to any table. The single exception is the respond/ endpoint stub, which returns 200 OK without writing.

-   Data sources: Activity, ActivityLog, Record (learn family + DAR lookup), UserProfile/UserPermission. The Relationship table is out of scope in MVP.

-   suggest/{record_id}/ is a stub returning {\"suggestions\": \[\], \"method\": \"deferred\"} in MVP.

-   respond/ is a stub returning 200 OK with no DB write in MVP.

-   Caching: Django cache framework, 5-minute TTL per user, filesystem backend. No Redis dependency.

-   DAR entries are identified by record_type: \"note\" + metadata.dar: true. No new record_type required; no v10 data contract amendment.

**2. Data Contract --- ParacleteDigest**

The ParacleteDigest is a Python dataclass defined in paraclete/service.py and serialised to JSON at the DRF boundary. All fields are present on every response. Array fields return an empty list when no data exists. Optional fields return null.

**2.1 ParacleteDigest Dataclass**

  --------------------------------- -------------------- -----------------------------------------------------------------------------------
  **Field**                         **Type**             **Description**

  generated_at                      datetime             UTC timestamp of digest generation

  user_id                           UUID                 Requesting user

  competence_level                  int                  User\'s competence_level (0--5); controls widget rendering

  **Activity Surface**                                   

  pending_count                     int                  Total personal activities with status=pending

  overdue_count                     int                  Activities past due_at, not completed

  due_today                         Activity\[\]         Up to 5 activities due today (status: pending or in_progress)

  overdue_items                     Activity\[\]         Up to 5 overdue items, oldest first

  habit_streaks                     HabitStreak\[\]      Active daily habits with current streak count

  **Reminders**                                          

  pending_reminders                 Activity\[\]         activity_type=reminder, due within 24 hours, up to 5

  **Learn Surface**                                      

  active_enrolments                 ProgrammeCard\[\]    In-progress Learn programmes with title and progress %

  next_lesson                       LessonCard \| null   Most recent incomplete lesson across active enrolments

  **Discipline Prompt**                                  

  discipline_prompt                 str                  Selected from ParacletePrompt model by least-active pathway rule

  prompt_pathway                    str                  KGS pathway the prompt relates to (e.g. \"mission\")

  **Daily Analysis Record**                              

  dar_today                         DARCard \| null      Today\'s DAR Record (record_type=note, metadata.dar=true) if written; null if not

  **Suggestions (MVP stub)**                             

  suggestions                       Suggestion\[\]       Empty list in MVP. method: \"deferred\" flag always present

  **Team Counts (Level 3+ only)**                        

  team_pending_count                int \| null          Team tasks pending in steward\'s primary tenant; null for Level 0--2

  team_overdue_count                int \| null          Team tasks overdue in steward\'s primary tenant; null for Level 0--2
  --------------------------------- -------------------- -----------------------------------------------------------------------------------

**2.2 Nested Object Schemas**

**ActivityCard (used in due_today, overdue_items, pending_reminders)**

  ------------------ ------------------ ----------------------------------------
  **Field**          **Type**           **Source**

  id                 UUID               Activity.id

  title              str                Activity.title

  activity_type      str                Activity.activity_type

  status             str                Activity.status

  due_at             datetime \| null   Activity.due_at

  kgs_pathway        str \| null        Activity.kgs_pathway
  ------------------ ------------------ ----------------------------------------

**HabitStreak**

  ------------------ -------------- -------------------------------------------------------
  **Field**          **Type**       **Detail**

  activity_id        UUID           Activity.id of the habit

  title              str            Activity.title

  streak             int            Consecutive days completed (daily habits only in MVP)

  last_completed     date \| null   Date of most recent completed ActivityLog entry
  ------------------ -------------- -------------------------------------------------------

**ProgrammeCard**

  ------------------ ------------ ----------------------------------------
  **Field**          **Type**     **Detail**

  record_id          UUID         Record.id of the programme

  title              str          Record.title

  progress           int          Linked Activity.progress (0--100)
  ------------------ ------------ ----------------------------------------

**LessonCard**

  ------------------ ------------ ----------------------------------------
  **Field**          **Type**     **Detail**

  record_id          UUID         Record.id of the lesson

  title              str          Record.title

  programme_title    str          Parent programme title

  url                str          /learn/lesson/{record_id}/
  ------------------ ------------ ----------------------------------------

**DARCard**

  ------------------ ------------ --------------------------------------------------
  **Field**          **Type**     **Detail**

  record_id          UUID         Record.id of today\'s DAR note

  title              str          Record.title (usually the date)

  created_at         datetime     When it was written

  url                str          /records/{record_id}/ --- link to full DAR entry
  ------------------ ------------ --------------------------------------------------

> ***Note:** DARCard is null if no record_type=note + metadata.dar=true Record exists with created_at\_\_date=today for this user.*

**3. Service Layer --- paraclete/service.py**

The service module is the intelligence core. It is a pure Python module --- no DRF, no HTTP calls, no writes. It imports Django ORM models directly and returns a ParacleteDigest dataclass instance.

**3.1 Module Structure**

> paraclete/
>
> \_\_init\_\_.py
>
> apps.py
>
> service.py ← orchestration + rules
>
> models.py ← ParacletePrompt model only
>
> serializers.py ← ParacleteDigestSerializer
>
> views.py ← DRF endpoints
>
> urls.py
>
> fixtures/
>
> paraclete_prompts.json ← initial prompt bank
>
> migrations/

**3.2 ParacleteDigest Dataclass**

> \# paraclete/service.py
>
> from dataclasses import dataclass, field
>
> from typing import Optional
>
> import datetime
>
> \@dataclass
>
> class ActivityCard:
>
> id: str
>
> title: str
>
> activity_type: str
>
> status: str
>
> due_at: Optional\[str\]
>
> kgs_pathway: Optional\[str\]
>
> \@dataclass
>
> class HabitStreak:
>
> activity_id: str
>
> title: str
>
> streak: int
>
> last_completed: Optional\[str\]
>
> \@dataclass
>
> class ProgrammeCard:
>
> record_id: str
>
> title: str
>
> progress: int
>
> \@dataclass
>
> class LessonCard:
>
> record_id: str
>
> title: str
>
> programme_title: str
>
> url: str
>
> \@dataclass
>
> class DARCard:
>
> record_id: str
>
> title: str
>
> created_at: str
>
> url: str
>
> \@dataclass
>
> class ParacleteDigest:
>
> generated_at: str
>
> user_id: str
>
> competence_level: int
>
> \# Activity surface
>
> pending_count: int = 0
>
> overdue_count: int = 0
>
> due_today: list = field(default_factory=list)
>
> overdue_items: list = field(default_factory=list)
>
> habit_streaks: list = field(default_factory=list)
>
> \# Reminders
>
> pending_reminders: list = field(default_factory=list)
>
> \# Learn
>
> active_enrolments: list = field(default_factory=list)
>
> next_lesson: Optional\[object\] = None
>
> \# Prompt
>
> discipline_prompt: str = \'\'
>
> prompt_pathway: str = \'\'
>
> \# DAR
>
> dar_today: Optional\[object\] = None
>
> \# Suggestions (stub)
>
> suggestions: list = field(default_factory=list)
>
> suggestion_method: str = \'deferred\'
>
> \# Team (Level 3+)
>
> team_pending_count: Optional\[int\] = None
>
> team_overdue_count: Optional\[int\] = None

**3.3 Main Orchestration Function**

> def build_digest(user) -\> ParacleteDigest:
>
> \"\"\"
>
> Entry point. Called by DRF view after cache miss.
>
> Reads ORM, applies rules, returns ParacleteDigest.
>
> Never writes to any table.
>
> \"\"\"
>
> level = getattr(getattr(user, \'userprofile\', None),
>
> \'competence_level\', 0)
>
> now = timezone.now()
>
> today = now.date()
>
> digest = ParacleteDigest(
>
> generated_at=now.isoformat(),
>
> user_id=str(user.id),
>
> competence_level=level,
>
> )
>
> \# Level 0 (seeker) --- prompt only
>
> prompt, pathway = \_select_prompt(user, level)
>
> digest.discipline_prompt = prompt
>
> digest.prompt_pathway = pathway
>
> if level \< 1:
>
> return digest
>
> \# Level 1+ --- full personal digest
>
> \_populate_activity_surface(digest, user, now, today)
>
> \_populate_reminders(digest, user, now)
>
> \_populate_learn(digest, user)
>
> digest.dar_today = \_get_dar_today(user, today)
>
> \# Level 3+ --- team counts
>
> if level \>= 3:
>
> \_populate_team_counts(digest, user, now, today)
>
> return digest

**3.4 Activity Surface Rules**

> def \_populate_activity_surface(digest, user, now, today):
>
> from activity.models import Activity
>
> \# All user tenants
>
> tenant_ids = user.userpermission_set.filter(
>
> is_active=True).values_list(\'tenant_id\', flat=True)
>
> qs = Activity.objects.filter(
>
> deleted_at\_\_isnull=True
>
> ).filter(
>
> models.Q(created_by=user, tenant\_\_isnull=True) \|
>
> models.Q(assigned_to=user, tenant_id\_\_in=tenant_ids)
>
> )
>
> active = qs.filter(status\_\_in=\[\'pending\', \'in_progress\'\])
>
> digest.pending_count = active.count()
>
> overdue_qs = active.filter(
>
> due_at\_\_isnull=False, due_at\_\_lt=now
>
> ).exclude(activity_type=\'reminder\')
>
> digest.overdue_count = overdue_qs.count()
>
> digest.overdue_items = \[
>
> \_to_activity_card(a) for a in
>
> overdue_qs.order_by(\'due_at\')\[:5\]
>
> \]
>
> due_today_qs = active.filter(
>
> due_at\_\_date=today
>
> ).exclude(activity_type=\'reminder\')
>
> digest.due_today = \[
>
> \_to_activity_card(a) for a in
>
> due_today_qs.order_by(\'due_at\')\[:5\]
>
> \]
>
> habits = qs.filter(
>
> activity_type=\'habit\',
>
> recurrence=\'daily\',
>
> status\_\_in=\[\'pending\', \'in_progress\'\]
>
> )
>
> digest.habit_streaks = \[
>
> \_calculate_streak(h) for h in habits
>
> \]

**3.5 Habit Streak Calculation**

Daily habits only in MVP. A streak is the number of consecutive calendar days ending yesterday (or today) on which an ActivityLog entry with event_type=status_changed and new_value=completed exists for this habit.

> def \_calculate_streak(activity) -\> HabitStreak:
>
> from activity.models import ActivityLog
>
> logs = ActivityLog.objects.filter(
>
> activity=activity,
>
> event_type=\'status_changed\',
>
> new_value=\'completed\'
>
> ).order_by(\'-created_at\').values_list(
>
> \'created_at\', flat=True
>
> )
>
> completed_dates = {l.date() for l in logs}
>
> streak = 0
>
> check_date = timezone.now().date()
>
> while check_date in completed_dates:
>
> streak += 1
>
> check_date -= datetime.timedelta(days=1)
>
> last = logs.first()
>
> return HabitStreak(
>
> activity_id=str(activity.id),
>
> title=activity.title,
>
> streak=streak,
>
> last_completed=last.date().isoformat() if last else None
>
> )

**3.6 Learn Surface Rules**

> def \_populate_learn(digest, user):
>
> from records.models import Record
>
> from activity.models import Activity
>
> \# Active learn enrolment activities
>
> enrolments = Activity.objects.filter(
>
> deleted_at\_\_isnull=True,
>
> created_by=user,
>
> metadata\_\_source_app=\'learn\',
>
> status=\'in_progress\'
>
> ).select_related()
>
> cards = \[\]
>
> for enr in enrolments:
>
> prog_id = enr.metadata.get(\'programme_record_id\')
>
> if not prog_id:
>
> continue
>
> try:
>
> rec = Record.objects.get(id=prog_id)
>
> cards.append(ProgrammeCard(
>
> record_id=str(rec.id),
>
> title=rec.title,
>
> progress=enr.progress
>
> ))
>
> except Record.DoesNotExist:
>
> pass
>
> digest.active_enrolments = cards
>
> \# Next lesson: most recently accessed incomplete lesson
>
> \# Identified by task-level Activity under an enrolment
>
> \# with status != completed, ordered by updated_at desc
>
> next_task = Activity.objects.filter(
>
> deleted_at\_\_isnull=True,
>
> created_by=user,
>
> metadata\_\_source_app=\'learn\',
>
> activity_type=\'task\',
>
> status\_\_in=\[\'pending\', \'in_progress\'\]
>
> ).order_by(\'-updated_at\').first()
>
> if next_task:
>
> lesson_id = next_task.metadata.get(\'lesson_record_id\')
>
> prog_title = next_task.metadata.get(\'programme_title\', \'\')
>
> if lesson_id:
>
> try:
>
> lesson = Record.objects.get(id=lesson_id)
>
> digest.next_lesson = LessonCard(
>
> record_id=str(lesson.id),
>
> title=lesson.title,
>
> programme_title=prog_title,
>
> url=f\'/learn/lesson/{lesson.id}/\'
>
> )
>
> except Record.DoesNotExist:
>
> pass

**3.7 DAR Lookup**

> def \_get_dar_today(user, today) -\> Optional\[DARCard\]:
>
> from records.models import Record
>
> dar = Record.objects.filter(
>
> created_by=user,
>
> record_type=\'note\',
>
> created_at\_\_date=today
>
> ).filter(
>
> \# metadata\_\_dar=True --- JSONField lookup
>
> metadata\_\_dar=True
>
> ).first()
>
> if not dar:
>
> return None
>
> return DARCard(
>
> record_id=str(dar.id),
>
> title=dar.title,
>
> created_at=dar.created_at.isoformat(),
>
> url=f\'/records/{dar.id}/\'
>
> )

**3.8 Team Counts (Level 3+)**

> def \_populate_team_counts(digest, user, now, today):
>
> from activity.models import Activity
>
> \# Primary steward tenant: highest-level tenant permission
>
> perm = user.userpermission_set.filter(
>
> is_active=True
>
> ).order_by(\'-competence_level\').first()
>
> if not perm:
>
> return
>
> tenant = perm.tenant
>
> team_qs = Activity.objects.filter(
>
> deleted_at\_\_isnull=True,
>
> tenant=tenant,
>
> status\_\_in=\[\'pending\', \'in_progress\'\]
>
> )
>
> digest.team_pending_count = team_qs.count()
>
> digest.team_overdue_count = team_qs.filter(
>
> due_at\_\_isnull=False, due_at\_\_lt=now
>
> ).count()

**4. ParacletePrompt Model**

The only new model introduced by the Paraclete app. Stores a curated bank of discipline prompts, tagged by KGS pathway and minimum competence level. Admin-editable. Fixture-loaded on first deploy.

**4.1 Model Definition**

> \# paraclete/models.py
>
> from django.db import models
>
> class ParacletePrompt(models.Model):
>
> KGS_PATHWAYS = \[
>
> (\'new_life\', \'New Life\'),
>
> (\'spiritual_formation\', \'Spiritual Formation\'),
>
> (\'community_life\', \'Community Life\'),
>
> (\'service\', \'Service\'),
>
> (\'leadership\', \'Leadership\'),
>
> (\'learning\', \'Learning\'),
>
> (\'mission\', \'Mission\'),
>
> (\'apostolic_stewardship\', \'Apostolic Stewardship\'),
>
> \]
>
> text = models.TextField(
>
> help_text=\'The prompt text shown to the user\'
>
> )
>
> pathway = models.CharField(
>
> max_length=30, choices=KGS_PATHWAYS,
>
> help_text=\'KGS pathway this prompt relates to\'
>
> )
>
> min_level = models.IntegerField(
>
> default=0,
>
> help_text=\'Minimum competence level to receive this prompt\'
>
> )
>
> is_active = models.BooleanField(default=True)
>
> created_at = models.DateTimeField(auto_now_add=True)
>
> class Meta:
>
> ordering = \[\'pathway\', \'min_level\'\]
>
> def \_\_str\_\_(self):
>
> return f\'{self.pathway} (L{self.min_level}): {self.text\[:60\]}\'

**4.2 Prompt Selection Rule**

The rule: identify the KGS pathway with the fewest completed Activity entries for this user in the last 14 days. Select a random active prompt for that pathway at or below the user\'s competence level. If no completed activities exist for any pathway, select a random prompt at or below the user\'s level.

> def \_select_prompt(user, level):
>
> from activity.models import Activity
>
> from .models import ParacletePrompt
>
> import random
>
> from django.utils import timezone
>
> import datetime
>
> cutoff = timezone.now() - datetime.timedelta(days=14)
>
> pathway_counts = (
>
> Activity.objects
>
> .filter(
>
> created_by=user,
>
> status=\'completed\',
>
> updated_at\_\_gte=cutoff,
>
> kgs_pathway\_\_isnull=False
>
> )
>
> .values(\'kgs_pathway\')
>
> .annotate(n=models.Count(\'id\'))
>
> .order_by(\'n\')
>
> )
>
> \# Least-active pathway
>
> least_pathway = (
>
> pathway_counts.first()\[\'kgs_pathway\'\]
>
> if pathway_counts.exists() else None
>
> )
>
> qs = ParacletePrompt.objects.filter(
>
> is_active=True, min_level\_\_lte=level
>
> )
>
> if least_pathway:
>
> qs = qs.filter(pathway=least_pathway)
>
> prompt = random.choice(list(qs)) if qs.exists() else None
>
> if prompt:
>
> return prompt.text, prompt.pathway
>
> return (\'Press into the Lord today.\', \'spiritual_formation\')

**4.3 Initial Fixture --- Prompt Bank**

A minimum of 24 prompts (3 per pathway) should be loaded on first deploy. These are authored prompts grounded in KGS language. A sample below; full fixture in fixtures/paraclete_prompts.json.

  ----------------------- --------------- ---------------------------------------------------------------------------------------------------------------------------
  **Pathway**             **Min Level**   **Sample Prompt Text**

  new_life                0               Every day is a new beginning in Christ. What is one thing you can lay down today and pick up afresh?

  spiritual_formation     0               Your spirit needs daily nourishment. Have you made space today to receive from the Lord?

  community_life          1               The Kingdom is built in community. Who in your circle needs a word of encouragement today?

  service                 1               Service is not a role --- it is a posture. What act of service can you offer today, unseen and unrewarded?

  leadership              2               A steward leads by example before instruction. What are you modelling for those who follow you?

  learning                1               The diligent learner makes room in every season. What have you studied this week that has shifted your understanding?

  mission                 2               The mandate is not waiting for perfect conditions. What one step of mission can you take today in the sphere you occupy?

  apostolic_stewardship   3               Apostolic stewardship requires faithfulness in the unglamorous. What governance or administrative duty have you deferred?
  ----------------------- --------------- ---------------------------------------------------------------------------------------------------------------------------

**5. DRF Endpoints**

**5.1 Endpoint Summary**

  ------------ ------------------------------------- ------------------------------------------------------------------
  **Method**   **URL**                               **Purpose**

  GET          /api/paraclete/digest/                Returns full ParacleteDigest for requesting user

  GET          /api/paraclete/reminders/             Returns pending_reminders slice only (convenience endpoint)

  GET          /api/paraclete/suggest/{record_id}/   MVP stub --- returns {suggestions: \[\], method: \'deferred\'}

  GET          /api/paraclete/prompt/                Returns discipline_prompt and prompt_pathway only

  POST         /api/paraclete/respond/               MVP stub --- accepts POST, returns {status: \'ok\'}, no DB write

  GET          /api/paraclete/health/                Health check --- returns {status: \'ok\', app: \'paraclete\'}
  ------------ ------------------------------------- ------------------------------------------------------------------

**5.2 Caching Strategy**

Every call to GET /api/paraclete/digest/ checks the Django cache before calling build_digest(). Cache key: paraclete_digest\_{user.id}. TTL: 300 seconds (5 minutes). Backend: filesystem (default Django cache). No Redis required.

> \# paraclete/views.py --- digest view
>
> from django.core.cache import cache
>
> from .service import build_digest
>
> from .serializers import ParacleteDigestSerializer
>
> class DigestView(APIView):
>
> permission_classes = \[IsAuthenticated\]
>
> def get(self, request):
>
> cache_key = f\'paraclete_digest\_{request.user.id}\'
>
> cached = cache.get(cache_key)
>
> if cached:
>
> return Response(cached)
>
> digest = build_digest(request.user)
>
> serializer = ParacleteDigestSerializer(digest)
>
> data = serializer.data
>
> cache.set(cache_key, data, 300)
>
> return Response(data)

**5.3 Serializers**

The ParacleteDigestSerializer uses DRF\'s Serializer (not ModelSerializer, since ParacleteDigest is a dataclass). Nested objects use their own serializers.

> \# paraclete/serializers.py
>
> from rest_framework import serializers
>
> class ActivityCardSerializer(serializers.Serializer):
>
> id = serializers.CharField()
>
> title = serializers.CharField()
>
> activity_type = serializers.CharField()
>
> status = serializers.CharField()
>
> due_at = serializers.CharField(allow_null=True)
>
> kgs_pathway = serializers.CharField(allow_null=True)
>
> class HabitStreakSerializer(serializers.Serializer):
>
> activity_id = serializers.CharField()
>
> title = serializers.CharField()
>
> streak = serializers.IntegerField()
>
> last_completed = serializers.CharField(allow_null=True)
>
> class ProgrammeCardSerializer(serializers.Serializer):
>
> record_id = serializers.CharField()
>
> title = serializers.CharField()
>
> progress = serializers.IntegerField()
>
> class LessonCardSerializer(serializers.Serializer):
>
> record_id = serializers.CharField()
>
> title = serializers.CharField()
>
> programme_title = serializers.CharField()
>
> url = serializers.CharField()
>
> class DARCardSerializer(serializers.Serializer):
>
> record_id = serializers.CharField()
>
> title = serializers.CharField()
>
> created_at = serializers.CharField()
>
> url = serializers.CharField()
>
> class ParacleteDigestSerializer(serializers.Serializer):
>
> generated_at = serializers.CharField()
>
> user_id = serializers.CharField()
>
> competence_level = serializers.IntegerField()
>
> pending_count = serializers.IntegerField()
>
> overdue_count = serializers.IntegerField()
>
> due_today = ActivityCardSerializer(many=True)
>
> overdue_items = ActivityCardSerializer(many=True)
>
> habit_streaks = HabitStreakSerializer(many=True)
>
> pending_reminders = ActivityCardSerializer(many=True)
>
> active_enrolments = ProgrammeCardSerializer(many=True)
>
> next_lesson = LessonCardSerializer(allow_null=True)
>
> discipline_prompt = serializers.CharField()
>
> prompt_pathway = serializers.CharField()
>
> dar_today = DARCardSerializer(allow_null=True)
>
> suggestions = serializers.ListField()
>
> suggestion_method = serializers.CharField()
>
> team_pending_count = serializers.IntegerField(allow_null=True)
>
> team_overdue_count = serializers.IntegerField(allow_null=True)

**5.4 URL Configuration**

> \# paraclete/urls.py
>
> from django.urls import path
>
> from . import views
>
> urlpatterns = \[
>
> path(\'digest/\', views.DigestView.as_view(), name=\'paraclete-digest\'),
>
> path(\'reminders/\', views.RemindersView.as_view(), name=\'paraclete-reminders\'),
>
> path(\'suggest/\<uuid:record_id\>/\', views.SuggestView.as_view(), name=\'paraclete-suggest\'),
>
> path(\'prompt/\', views.PromptView.as_view(), name=\'paraclete-prompt\'),
>
> path(\'respond/\', views.RespondView.as_view(), name=\'paraclete-respond\'),
>
> path(\'health/\', views.health, name=\'paraclete-health\'),
>
> \]

**6. Dashboard Widget Map**

Phase 7 (Dashboard) consumes ParacleteDigest. The following table locks the mapping between digest fields and Dashboard widgets, including minimum competence level for display.

**6.1 Widget-to-Field Mapping**

  ------------------- ----------------------------------- --------------- ---------------------------------------------------------------------------------
  **Widget**          **Digest field(s)**                 **Min level**   **Notes**

  Today\'s Focus      discipline_prompt, prompt_pathway   0               Visible to all users including seekers

  Write DAR prompt    dar_today                           1               Shows \'DAR written ✓\' or \'Write today\'s DAR\' CTA linking to Records create

  Due Today           due_today, pending_count            1               Up to 5 cards; count badge

  Overdue             overdue_items, overdue_count        1               Highlighted in warning colour; oldest first

  Pending Reminders   pending_reminders                   1               Due within 24h; collapse if empty

  Habit Streaks       habit_streaks                       1               Each habit shows streak count; collapse if no habits

  Active Enrolments   active_enrolments                   1               Progress bar per programme; links to Learn app

  Continue Learning   next_lesson                         1               Single card; null = widget hidden

  Team Pending        team_pending_count                  3               Count only; links to Activity App ministry surface

  Team Overdue        team_overdue_count                  3               Warning badge; links to Activity App overdue filter
  ------------------- ----------------------------------- --------------- ---------------------------------------------------------------------------------

**6.2 Level-Gated Dashboard Behaviour**

The Dashboard template gates widget rendering by competence_level from the digest. No separate permission check is needed at the template level --- the digest itself gates the data.

> \<!\-- Example: team counts widget \--\>
>
> {% if digest.competence_level \>= 3 and digest.team_pending_count is not None %}
>
> \<div class=\'widget team-pending\'\>
>
> \<span\>{{ digest.team_pending_count }} team tasks pending\</span\>
>
> \</div\>
>
> {% endif %}

**7. Build Phases**

**Phase A --- Django App Scaffold + Model**

Entry requirement: Phases 0--3 complete. Activity Engine working.

-   Create paraclete/ Django app: django-admin startapp paraclete

-   Add \'paraclete\' to INSTALLED_APPS

-   Create paraclete/models.py with ParacletePrompt model

-   Create and run migration

-   Register ParacletePrompt in admin

-   Create fixtures/paraclete_prompts.json with minimum 24 prompts (3 per pathway)

-   Load fixture: python manage.py loaddata paraclete_prompts

-   Wire paraclete/urls.py into ics_project/urls.py under /api/paraclete/

-   Implement health endpoint --- GET /api/paraclete/health/ → {status: ok}

Exit criteria: GET /api/paraclete/health/ returns 200. ParacletePrompt fixture loaded (24+ rows in admin).

> git commit -m \"feat: paraclete app scaffold, ParacletePrompt model, fixture\"

**Phase B --- Service Core + Digest Endpoint**

Entry requirement: Phase A complete.

-   Implement ParacleteDigest dataclass and all sub-dataclasses in service.py

-   Implement build_digest() orchestration function

-   Implement \_populate_activity_surface() with all ORM queries

-   Implement \_calculate_streak() for daily habits

-   Implement \_select_prompt() with least-active pathway rule

-   Implement \_get_dar_today() DAR lookup

-   Implement \_populate_learn() enrolment and next_lesson logic

-   Implement \_populate_team_counts() for Level 3+

-   Create ParacleteDigestSerializer and all nested serializers

-   Implement DigestView with 5-minute filesystem cache

-   Configure Django CACHES in settings/base.py for filesystem backend

Exit criteria: GET /api/paraclete/digest/ returns valid JSON ParacleteDigest for a Level 1 test user. All fields present. Cache header confirms second call served from cache.

> git commit -m \"feat: paraclete service.py, digest endpoint, caching\"

**Phase C --- Remaining Endpoints**

Entry requirement: Phase B complete.

-   Implement RemindersView --- returns pending_reminders slice from build_digest()

-   Implement PromptView --- returns discipline_prompt + prompt_pathway from build_digest()

-   Implement SuggestView stub --- returns {suggestions: \[\], method: \'deferred\'}

-   Implement RespondView stub --- returns {status: \'ok\'}, no DB write

Exit criteria: All five endpoints return expected responses for authenticated requests. Unauthenticated requests return 401.

> git commit -m \"feat: paraclete remaining endpoints --- reminders, prompt, suggest stub, respond stub\"

**Phase D --- Smoke Test**

Entry requirement: Phase C complete.

-   Test with Level 0 user: digest returns prompt only; all other fields empty/null

-   Test with Level 1 user: all personal activity fields populated correctly

-   Test with Level 3 user: team_pending_count and team_overdue_count are integers, not null

-   Create a DAR note (record_type=note, metadata.dar=true) for today: confirm dar_today is populated

-   Create a daily habit and mark it completed for 3 consecutive days via ActivityLog: confirm streak=3

-   Confirm 5-minute cache: two rapid digest requests return identical generated_at

-   Confirm suggest/ returns {suggestions: \[\], method: \'deferred\'} regardless of record_id

-   Confirm respond/ returns {status: \'ok\'} for POST with any body

Exit criteria: All checklist items pass. GET /api/paraclete/digest/ returns correct data for each competence level.

> git commit -m \"feat: paraclete smoke test pass --- all phases complete\"

**8. File Map**

  ------------------------------------------- ------------ -------------------------------------------------------------------------
  **File**                                    **Status**   **Purpose**

  paraclete/\_\_init\_\_.py                   NEW          App init

  paraclete/apps.py                           NEW          AppConfig

  paraclete/models.py                         NEW          ParacletePrompt model

  paraclete/service.py                        NEW          ParacleteDigest dataclass + build_digest() + all private methods

  paraclete/serializers.py                    NEW          All DRF serializers for digest and nested objects

  paraclete/views.py                          NEW          DigestView, RemindersView, PromptView, SuggestView, RespondView, health

  paraclete/urls.py                           NEW          URL routing for all six endpoints

  paraclete/migrations/0001_initial.py        NEW          ParacletePrompt table migration

  paraclete/fixtures/paraclete_prompts.json   NEW          Initial prompt bank (24+ prompts, 3 per pathway)

  ics_project/settings/base.py                MODIFY       Add paraclete to INSTALLED_APPS; add CACHES filesystem config

  ics_project/urls.py                         MODIFY       Include paraclete.urls under /api/paraclete/
  ------------------------------------------- ------------ -------------------------------------------------------------------------

**8.1 Settings --- Cache Configuration**

> \# ics_project/settings/base.py --- add CACHES block
>
> CACHES = {
>
> \'default\': {
>
> \'BACKEND\': \'django.core.cache.backends.filebased.FileBasedCache\',
>
> \'LOCATION\': BASE_DIR / \'cache\',
>
> }
>
> }
>
> ***Note:** The cache/ directory must exist on the VPS and be writable by the Gunicorn process user. Add cache/ to .gitignore.*

**9. Deferred to Phase 2**

  ------------------------------------- -------------------------------------------------------------------------------
  **Feature**                           **Detail**

  AI-assisted pattern detection         Requires LLM integration; no AI calls in MVP

  Link suggestion engine                suggest/ returns stub in MVP; Phase 2 adds Relationship graph proximity logic

  ParacleteResponse model               respond/ is a stub; response tracking table added in Phase 2

  Weekly habit streaks                  Only daily streak calculation in MVP; weekly added in Phase 2

  Governance digest                     Mandate alignment suggestions deferred per v9 contract deferred list

  Prophetic prompt generation           LLM-generated prompts based on dream journal + key library; Phase 2

  Redis / Memcached cache               Filesystem cache sufficient for MVP scale; upgrade path is clear

  Paraclete digest push notifications   Wired to Notifications app; Phase 7+
  ------------------------------------- -------------------------------------------------------------------------------

**10. Phase Summary**

  ----------- ------------------------------------------------------------------ ----------------------- ----------------------------------------------------------
  **Phase**   **What it builds**                                                 **Entry requirement**   **Exit criteria**

  A           Django app, ParacletePrompt model, fixture, health endpoint        Phases 0--3 done        health/ returns 200; 24+ prompts loaded

  B           service.py, build_digest(), DigestView with caching, serializers   Phase A done            digest/ returns correct ParacleteDigest for Level 1 user

  C           reminders/, prompt/, suggest/ stub, respond/ stub                  Phase B done            All endpoints return expected responses; 401 for unauth

  D           Smoke test --- all levels, DAR, habit streak, cache, stubs         Phase C done            Full checklist passes
  ----------- ------------------------------------------------------------------ ----------------------- ----------------------------------------------------------

Commit per phase as specified. Phase D completion commit closes Task 6.1.

Task 6.2 (paraclete.service.js --- frontend consumption layer) begins after Phase D exit criteria pass.

ICS Platform · Task 6.1 Paraclete Service · System Design v1.0 · 2026-04-10
