from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.tenants.models import Institution

class User(AbstractUser):
    ROLE_CHOICES = (
        ('DEVELOPER', 'Developer / Super Admin'),
        ('INSTITUTION_ADMIN', 'Institution Admin'),
        ('SUB_ADMIN', 'Sub-Admin / Coordinator'),
        ('TABULATOR', 'Tabulator / Mark Entry Officer'),
        ('JUDGE', 'Judge / Evaluator'),
        ('TEAM_LEADER', 'Team Leader / Manager'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='TEAM_LEADER')
    institution = models.ForeignKey(
        Institution, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='users',
        help_text="Scoped institution for tenant isolation (null for Developers)"
    )
    assigned_competitions = models.ManyToManyField(
        'core.Competition',
        blank=True,
        related_name='assigned_judges',
        help_text="Competitions fixed/assigned to this judge"
    )
    assigned_programs = models.ManyToManyField(
        'core.Program',
        blank=True,
        related_name='assigned_judges',
        help_text="Specific programs assigned to this judge"
    )
    is_approved = models.BooleanField(
        default=False, 
        help_text="Approved user access state. Developer approves Institution Admin; Admin approves sub-users."
    )
    phone = models.CharField(max_length=20, blank=True)
    designation = models.CharField(max_length=100, blank=True, default='Member')

    def __str__(self):
        inst_name = self.institution.name if self.institution else "Global"
        return f"{self.username} [{self.get_role_display()}] - {inst_name}"

    @property
    def is_developer(self):
        return self.role == 'DEVELOPER' or self.is_superuser

    @property
    def is_institution_admin(self):
        return self.role == 'INSTITUTION_ADMIN'

    @property
    def is_sub_admin(self):
        return self.role in ['INSTITUTION_ADMIN', 'SUB_ADMIN']

    @property
    def is_tabulator(self):
        return self.role == 'TABULATOR'

    @property
    def is_judge(self):
        return self.role == 'JUDGE'

    @property
    def is_team_leader(self):
        return self.role == 'TEAM_LEADER'
