from django.db import models
from django.utils import timezone
from apps.tenants.models import Institution
from apps.users.models import User

# ----------------- Tenant Model Base -----------------
class TenantBaseModel(models.Model):
    institution = models.ForeignKey(
        Institution, 
        on_delete=models.CASCADE, 
        db_index=True,
        help_text="Tenant institution scoping"
    )

    class Meta:
        abstract = True


# ----------------- Competition -----------------
class Competition(TenantBaseModel):
    COMPETITION_TYPES = [
        ("ON", "On-Campus"),
        ("OFF", "Off-Campus"),
        ("BOTH", "Combined On & Off-Campus"),
    ]
    name = models.CharField(max_length=150)
    logo = models.ImageField(upload_to='fest_logos/', null=True, blank=True, help_text="Optional Fest / Competition Logo")
    name_image = models.ImageField(upload_to='fest_name_images/', null=True, blank=True, help_text="Optional custom typography PNG image for the Fest Name")
    custom_result_template = models.ImageField(upload_to='result_templates/', null=True, blank=True, help_text="Optional custom poster template for Winner Cards Studio")
    type = models.CharField(max_length=10, choices=COMPETITION_TYPES, default="ON")
    year = models.PositiveIntegerField(default=2026)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_type_display()}) - {self.institution.name}"


# ----------------- Category -----------------
class Category(TenantBaseModel):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)
    is_common = models.BooleanField(default=False, help_text="True if this is a combined/common category containing multiple base categories")
    included_categories = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='parent_common_categories',
        help_text="Included base categories for this common category"
    )
    start_chest_no = models.PositiveIntegerField(default=1001, help_text="Starting chest number sequence for contestants in this category")

    class Meta:
        ordering = ['name']

    def __str__(self):
        if self.is_common:
            inc_list = ", ".join([c.name for c in self.included_categories.all()])
            return f"{self.name} [Common: {inc_list or 'All'}]"
        return f"{self.name} ({self.competition.name})"

    def get_eligible_categories(self):
        """Returns list of Category objects eligible for this category (included base categories for combined categories)."""
        if self.is_common:
            cats = set(self.included_categories.all())
            cats.add(self)
            if not self.included_categories.exists():
                cats.update(Category.objects.filter(institution=self.institution, is_common=False))
            return list(cats)
        return [self]


# ----------------- Team -----------------
class Team(TenantBaseModel):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='teams')
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_team')
    name = models.CharField(max_length=100)
    code_letter = models.CharField(max_length=10, blank=True)
    logo = models.ImageField(upload_to='team_logos/', null=True, blank=True)
    total_points = models.IntegerField(default=0)

    class Meta:
        ordering = ['-total_points', 'name']

    def __str__(self):
        return f"{self.name} ({self.competition.name})"


# ----------------- Stage / Venue -----------------
class Stage(TenantBaseModel):
    STAGE_TYPES = (
        ('STAGE', 'Stage Venue'),
        ('OFF_STAGE', 'Off-Stage Venue'),
    )
    name = models.CharField(max_length=100)
    stage_type = models.CharField(max_length=15, choices=STAGE_TYPES, default='STAGE')
    location_details = models.CharField(max_length=200, blank=True)
    reserved_days = models.ManyToManyField(
        'FestDay',
        blank=True,
        related_name='reserved_stages',
        help_text="Fest days this stage is active/reserved for"
    )

    class Meta:
        ordering = ['stage_type', 'name']

    def __str__(self):
        return f"{self.name} [{self.get_stage_type_display()}]"

    def get_reserved_days_list(self):
        """Returns list of reserved FestDays or all institution FestDays if none explicitly selected."""
        if self.reserved_days.exists():
            return list(self.reserved_days.all().order_by('day_number'))
        return list(FestDay.objects.filter(institution=self.institution).order_by('day_number'))


# ----------------- Fest Days & Schedule -----------------
class FestDay(TenantBaseModel):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='fest_days')
    day_number = models.PositiveIntegerField()
    date = models.DateField(null=True, blank=True)
    name = models.CharField(max_length=100, blank=True)
    start_time = models.TimeField(default='09:00', help_text="Operating start time")
    end_time = models.TimeField(default='21:00', help_text="Operating end time")

    class Meta:
        ordering = ['day_number']
        unique_together = ('competition', 'day_number')

    def __str__(self):
        return f"Day {self.day_number} ({self.name or self.date})"


# ----------------- Program (Event) -----------------
class Program(TenantBaseModel):
    PROGRAM_TYPES = (
        ('STAGE', 'Stage Program'),
        ('OFF_STAGE', 'Off-Stage Program'),
    )
    PRESENTATION_MODES = (
        ('SEQUENTIAL', 'Per Participant (Sequential)'),
        ('SIMULTANEOUS', 'All-at-Once (Simultaneous/Written)'),
    )
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='programs')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='programs')
    name = models.CharField(max_length=150)
    is_group = models.BooleanField(default=False)
    min_members = models.PositiveIntegerField(default=1)
    max_members = models.PositiveIntegerField(default=1)
    program_type = models.CharField(max_length=15, choices=PROGRAM_TYPES, default='STAGE')
    presentation_mode = models.CharField(max_length=15, choices=PRESENTATION_MODES, default='SEQUENTIAL')
    duration_per_participant = models.PositiveIntegerField(default=5, help_text="Duration in minutes")
    buffer_margin_minutes = models.PositiveIntegerField(default=0, help_text="Extra buffer time in minutes")
    preferred_stage = models.ForeignKey(Stage, on_delete=models.SET_NULL, null=True, blank=True, related_name='preferred_programs')
    is_announced = models.BooleanField(default=False)
    announced_at = models.DateTimeField(null=True, blank=True)
    MARK_ENTRY_MODES = (
        ('OFFICIALS', 'By Officials (Default)'),
        ('JUDGES', 'Directly by Judges'),
    )
    judge_count = models.PositiveIntegerField(default=1, help_text="Number of judges evaluating this program")
    max_marks_per_judge = models.PositiveIntegerField(default=100, help_text="Maximum marks allowed per judge")
    mark_entry_mode = models.CharField(
        max_length=15,
        choices=MARK_ENTRY_MODES,
        default='OFFICIALS',
        help_text="Who inputs marks for this program: Officials or Judges"
    )

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        group_str = "Group" if self.is_group else "Single"
        return f"{self.name} ({self.category.name}) [{group_str}]"

    @property
    def judge_slots(self):
        jc = self.judge_count if self.judge_count else 1
        assigned = list(self.assigned_judges.all())
        slots = []
        for i in range(jc):
            j_obj = assigned[i] if i < len(assigned) else None
            slots.append({
                'slot_num': i + 1,
                'selected_judge_id': j_obj.id if j_obj else None,
            })
        return slots


# ----------------- Program Schedule -----------------
class ProgramSchedule(TenantBaseModel):
    program = models.OneToOneField(Program, on_delete=models.CASCADE, related_name='schedule')
    fest_day = models.ForeignKey(FestDay, on_delete=models.CASCADE, related_name='schedules')
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, related_name='schedules')
    start_time = models.TimeField()
    end_time = models.TimeField()
    total_duration_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['fest_day__day_number', 'start_time']

    def __str__(self):
        return f"{self.program.name} ({self.fest_day} @ {self.stage.name})"


# ----------------- Contestant -----------------
class Contestant(TenantBaseModel):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='contestants')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='contestants')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='contestants')
    chest_no = models.PositiveIntegerField(db_index=True)
    name = models.CharField(max_length=120)
    whatsapp_number = models.CharField(max_length=20, blank=True, null=True, help_text="Optional WhatsApp contact number")
    total_points = models.IntegerField(default=0)

    class Meta:
        ordering = ['chest_no']
        unique_together = ('institution', 'competition', 'chest_no')

    @property
    def calculated_total_points(self):
        """
        Dynamically calculates total individual points earned by this contestant across 
        single participations (announced items). Group items award points to the Team, not the individual.
        """
        pts = 0
        for p in self.participations.filter(marks__isnull=False, program__is_announced=True):
            if p.rank or p.grade:
                pts += p.total_points
        return pts

    def __str__(self):
        return f"#{self.chest_no} {self.name} ({self.team.name})"

    def save(self, *args, **kwargs):
        if not self.chest_no and self.category:
            from apps.core.services import get_next_chest_number
            self.chest_no = get_next_chest_number(self.category)
        elif not self.chest_no:
            last = Contestant.objects.filter(
                institution=self.institution, 
                competition=self.competition
            ).order_by('-chest_no').first()
            self.chest_no = 1001 if not last else last.chest_no + 1
        super().save(*args, **kwargs)


# ----------------- Single Participation -----------------
class Participation(TenantBaseModel):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='single_participations')
    contestant = models.ForeignKey(Contestant, on_delete=models.CASCADE, related_name='participations')
    code_letter = models.CharField(max_length=5, blank=True, null=True)
    marks = models.IntegerField(null=True, blank=True)
    judge_marks = models.JSONField(default=dict, blank=True, null=True, help_text="Individual marks per judge e.g. {'1': 85, '2': 90}")
    rank = models.PositiveIntegerField(null=True, blank=True)
    grade = models.CharField(max_length=2, null=True, blank=True)
    points_awarded = models.BooleanField(default=False)
    marks_added_at = models.DateTimeField(default=timezone.now, null=True, blank=True)

    class Meta:
        unique_together = ('program', 'contestant')
        ordering = ['program', 'rank', '-marks']

    def __str__(self):
        return f"{self.contestant.name} - {self.program.name}"

    def get_judge_mark(self, judge_num):
        if not self.judge_marks or not isinstance(self.judge_marks, dict):
            return None
        return self.judge_marks.get(str(judge_num))

    @property
    def judge_marks_list(self):
        jc = self.program.judge_count if self.program and self.program.judge_count else 1
        res = []
        jm = self.judge_marks or {}
        for j in range(1, jc + 1):
            val = jm.get(str(j))
            if val is None and j == 1 and self.marks is not None and not jm:
                val = self.marks
            res.append({'judge_num': j, 'score': val if val is not None else ''})
        return res

    @property
    def total_points(self):
        config = PointsConfig.objects.filter(institution=self.institution).first()
        r1 = config.single_rank_1_points if config else 5
        r2 = config.single_rank_2_points if config else 3
        r3 = config.single_rank_3_points if config else 1
        gap = config.single_grade_aplus_points if config else 6
        ga = config.single_grade_a_points if config else 5
        gb = config.single_grade_b_points if config else 3
        gc = config.single_grade_c_points if config else 1

        pts = 0
        if self.rank == 1: pts += r1
        elif self.rank == 2: pts += r2
        elif self.rank == 3: pts += r3

        if self.grade == 'A+': pts += gap
        elif self.grade == 'A': pts += ga
        elif self.grade == 'B': pts += gb
        elif self.grade == 'C': pts += gc
        return pts


# ----------------- Group Participation -----------------
class GroupParticipation(TenantBaseModel):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='group_participations')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='group_participations')
    group_name = models.CharField(max_length=150, blank=True)
    captain = models.ForeignKey(Contestant, on_delete=models.SET_NULL, null=True, blank=True, related_name='captain_groups')
    contestants = models.ManyToManyField(Contestant, related_name='group_entries')
    code_letter = models.CharField(max_length=5, blank=True, null=True)
    marks = models.IntegerField(null=True, blank=True)
    judge_marks = models.JSONField(default=dict, blank=True, null=True, help_text="Individual marks per judge e.g. {'1': 85, '2': 90}")
    rank = models.PositiveIntegerField(null=True, blank=True)
    grade = models.CharField(max_length=2, null=True, blank=True)
    points_awarded = models.BooleanField(default=False)
    marks_added_at = models.DateTimeField(default=timezone.now, null=True, blank=True)

    class Meta:
        ordering = ['program', 'rank', '-marks']

    def __str__(self):
        return f"{self.display_name} - {self.program.name}"

    def get_judge_mark(self, judge_num):
        if not self.judge_marks or not isinstance(self.judge_marks, dict):
            return None
        return self.judge_marks.get(str(judge_num))

    @property
    def judge_marks_list(self):
        jc = self.program.judge_count if self.program and self.program.judge_count else 1
        res = []
        jm = self.judge_marks or {}
        for j in range(1, jc + 1):
            val = jm.get(str(j))
            if val is None and j == 1 and self.marks is not None and not jm:
                val = self.marks
            res.append({'judge_num': j, 'score': val if val is not None else ''})
        return res

    @property
    def display_name(self):
        if self.captain:
            if self.group_name:
                return f"{self.captain.name} & Team ({self.group_name})"
            return f"{self.captain.name} & Team"
        elif self.group_name:
            return self.group_name
        return f"{self.team.name} Group"

    @property
    def total_points(self):
        config = PointsConfig.objects.filter(institution=self.institution).first()
        r1 = config.group_rank_1_points if config else 10
        r2 = config.group_rank_2_points if config else 6
        r3 = config.group_rank_3_points if config else 3
        gap = config.group_grade_aplus_points if config else 6
        ga = config.group_grade_a_points if config else 5
        gb = config.group_grade_b_points if config else 3
        gc = config.group_grade_c_points if config else 1

        pts = 0
        if self.rank == 1: pts += r1
        elif self.rank == 2: pts += r2
        elif self.rank == 3: pts += r3

        if self.grade == 'A+': pts += gap
        elif self.grade == 'A': pts += ga
        elif self.grade == 'B': pts += gb
        elif self.grade == 'C': pts += gc
        return pts


# ----------------- Points Configuration -----------------
class PointsConfig(TenantBaseModel):
    # Single Event Rank Points
    single_rank_1_points = models.IntegerField(default=5)
    single_rank_2_points = models.IntegerField(default=3)
    single_rank_3_points = models.IntegerField(default=1)

    # Single Event Grade Points
    single_grade_aplus_points = models.IntegerField(default=6)
    single_grade_a_points = models.IntegerField(default=5)
    single_grade_b_points = models.IntegerField(default=3)
    single_grade_c_points = models.IntegerField(default=1)

    # Group Event Rank Points
    group_rank_1_points = models.IntegerField(default=10)
    group_rank_2_points = models.IntegerField(default=6)
    group_rank_3_points = models.IntegerField(default=3)

    # Group Event Grade Points
    group_grade_aplus_points = models.IntegerField(default=6)
    group_grade_a_points = models.IntegerField(default=5)
    group_grade_b_points = models.IntegerField(default=3)
    group_grade_c_points = models.IntegerField(default=1)

    # Grade Thresholds
    grade_aplus_threshold = models.IntegerField(default=90)
    grade_a_threshold = models.IntegerField(default=80)
    grade_b_threshold = models.IntegerField(default=70)
    grade_c_threshold = models.IntegerField(default=60)

    class Meta:
        unique_together = ('institution',)

    def __str__(self):
        return f"Points Config - {self.institution.name}"

    @property
    def rank_1_points(self): return self.group_rank_1_points
    @property
    def rank_2_points(self): return self.group_rank_2_points
    @property
    def rank_3_points(self): return self.group_rank_3_points
    @property
    def grade_a_points(self): return self.group_grade_a_points
    @property
    def grade_b_points(self): return self.group_grade_b_points
    @property
    def grade_c_points(self): return self.group_grade_c_points


# ----------------- Announcement -----------------
class Announcement(TenantBaseModel):
    PRIORITY_CHOICES = (
        ('LOW', 'Info'),
        ('MEDIUM', 'Important'),
        ('HIGH', 'Urgent'),
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='LOW')
    is_public = models.BooleanField(default=True, help_text="Show on public result page")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.institution.name})"
