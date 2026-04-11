from rest_framework import serializers


class ActivityCardSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
    activity_type = serializers.CharField()
    status = serializers.CharField()
    due_at = serializers.CharField(allow_null=True)
    kgs_pathway = serializers.CharField(allow_null=True)


class HabitStreakSerializer(serializers.Serializer):
    activity_id = serializers.CharField()
    title = serializers.CharField()
    streak = serializers.IntegerField()
    last_completed = serializers.CharField(allow_null=True)


class ProgrammeCardSerializer(serializers.Serializer):
    record_id = serializers.CharField()
    title = serializers.CharField()
    progress = serializers.IntegerField()


class LessonCardSerializer(serializers.Serializer):
    record_id = serializers.CharField()
    title = serializers.CharField()
    programme_title = serializers.CharField()
    url = serializers.CharField()


class DARCardSerializer(serializers.Serializer):
    record_id = serializers.CharField()
    title = serializers.CharField()
    created_at = serializers.CharField()
    url = serializers.CharField()


class ParacleteDigestSerializer(serializers.Serializer):
    generated_at = serializers.CharField()
    user_id = serializers.CharField()
    competence_level = serializers.IntegerField()

    pending_count = serializers.IntegerField()
    overdue_count = serializers.IntegerField()
    due_today = ActivityCardSerializer(many=True)
    overdue_items = ActivityCardSerializer(many=True)
    habit_streaks = HabitStreakSerializer(many=True)
    pending_reminders = ActivityCardSerializer(many=True)

    active_enrolments = ProgrammeCardSerializer(many=True)
    next_lesson = LessonCardSerializer(allow_null=True)

    discipline_prompt = serializers.CharField()
    prompt_pathway = serializers.CharField()

    dar_today = DARCardSerializer(allow_null=True)

    suggestions = serializers.ListField()
    suggestion_method = serializers.CharField()

    team_pending_count = serializers.IntegerField(allow_null=True)
    team_overdue_count = serializers.IntegerField(allow_null=True)
