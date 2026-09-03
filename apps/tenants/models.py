from django.db import models
from django.utils import timezone
from django.utils.text import slugify

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    code = models.SlugField(unique=True)
    max_competitions = models.PositiveIntegerField(default=5, help_text="Maximum allowed active competitions")
    max_contestants = models.PositiveIntegerField(default=1000, help_text="Maximum total contestants across all competitions")
    original_price = models.DecimalField(max_digits=10, decimal_places=2, default=3000.00, help_text="Original regular plan price before discount")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=999.00, help_text="Offer plan price")
    description = models.TextField(blank=True)
    description_ml = models.TextField(blank=True, help_text="Malayalam description for the plan")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} (Rs. {self.price} - Regular Rs. {self.original_price})"

class Institution(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved & Active'),
        ('REJECTED', 'Rejected'),
        ('SUSPENDED', 'Suspended'),
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    logo = models.ImageField(upload_to='institution_logos/', null=True, blank=True)
    primary_color = models.CharField(max_length=20, default='#4f46e5')
    secondary_color = models.CharField(max_length=20, default='#06b6d4')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    is_demo = models.BooleanField(default=False, help_text="Is this institution in 5-Day Demo/Trial mode?")
    demo_expires_at = models.DateTimeField(null=True, blank=True, help_text="Expiration date for Demo Trial")
    allow_developer_access = models.BooleanField(default=False, help_text="Allow Developer/Superadmin support access to this institution's workspace")
    is_public_suspended = models.BooleanField(default=False, help_text="Suspend public live portal link for this institution")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} [{self.get_status_display()}]"

    @property
    def is_active(self):
        return self.status == 'APPROVED'

    @property
    def is_demo_active(self):
        if not self.is_demo or not self.demo_expires_at:
            return False
        return timezone.now() < self.demo_expires_at

    @property
    def is_demo_expired(self):
        if not self.is_demo or not self.demo_expires_at:
            return False
        return timezone.now() >= self.demo_expires_at

    @property
    def demo_time_remaining(self):
        if not self.is_demo or not self.demo_expires_at:
            return None
        now = timezone.now()
        diff = self.demo_expires_at - now
        total_seconds = int(diff.total_seconds())

        if total_seconds <= 0:
            return {
                'is_expired': True,
                'text': 'Demo Trial Expired',
                'days': 0,
                'hours': 0,
                'minutes': 0,
                'seconds': 0,
                'is_days': False
            }

        days = diff.days
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if total_seconds > 86400:
            formatted = f"{days} Day{'s' if days > 1 else ''} {hours} Hr{'s' if hours != 1 else ''} Left"
            return {
                'is_expired': False,
                'text': formatted,
                'days': days,
                'hours': hours,
                'minutes': minutes,
                'seconds': seconds,
                'is_days': True
            }
        else:
            formatted = f"{hours} Hour{'s' if hours != 1 else ''} {minutes} Min{'s' if minutes != 1 else ''} Left"
            return {
                'is_expired': False,
                'text': formatted,
                'days': 0,
                'hours': hours,
                'minutes': minutes,
                'seconds': seconds,
                'is_days': False
            }

    def has_add_on(self, code):
        return self.granted_add_ons.filter(add_on__code=code, is_active=True, add_on__is_active=True).exists()

    def active_add_ons(self):
        return self.granted_add_ons.filter(is_active=True, add_on__is_active=True).select_related('add_on')

    @property
    def points_config(self):
        from apps.core.models import PointsConfig
        config, _ = PointsConfig.objects.get_or_create(institution=self)
        return config

    @property
    def has_grades(self):
        return self.points_config.enable_grades

    @property
    def allows_team_management(self):
        from apps.core.models import Competition
        comp = Competition.objects.filter(institution=self, is_active=True).first() or Competition.objects.filter(institution=self).first()
        return comp.allow_team_management if comp else True

    @property
    def allows_category_management(self):
        from apps.core.models import Competition
        comp = Competition.objects.filter(institution=self, is_active=True).first() or Competition.objects.filter(institution=self).first()
        return comp.allow_category_management if comp else True

    @property
    def allows_program_management(self):
        from apps.core.models import Competition
        comp = Competition.objects.filter(institution=self, is_active=True).first() or Competition.objects.filter(institution=self).first()
        return comp.allow_program_management if comp else True

    @property
    def allows_contestant_registration(self):
        from apps.core.models import Competition
        comp = Competition.objects.filter(institution=self, is_active=True).first() or Competition.objects.filter(institution=self).first()
        return comp.allow_contestant_registration if comp else True

    @property
    def allows_program_assignment(self):
        from apps.core.models import Competition
        comp = Competition.objects.filter(institution=self, is_active=True).first() or Competition.objects.filter(institution=self).first()
        return comp.allow_program_assignment if comp else True


class AddOn(models.Model):
    name = models.CharField(max_length=150, help_text="Add-on Name (e.g. Contestant User Creation)")
    code = models.SlugField(max_length=100, unique=True, help_text="Unique Identifier Code (e.g. contestant-user-creation)")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Price for this add-on")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.code}) - Rs. {self.price}"


class GrantedAddOn(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='granted_add_ons')
    add_on = models.ForeignKey(AddOn, on_delete=models.CASCADE, related_name='grants')
    granted_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    notes = models.CharField(max_length=255, blank=True, help_text="Optional developer note or custom pricing info")

    class Meta:
        unique_together = ('institution', 'add_on')

    def __str__(self):
        return f"{self.institution.name} -> {self.add_on.name}"


class AddOnRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('approved', 'Approved / Granted'),
        ('rejected', 'Rejected'),
    )
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='addon_requests')
    add_on = models.ForeignKey(AddOn, on_delete=models.CASCADE, related_name='requests')
    requested_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    contact_person = models.CharField(max_length=150, blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        return f"Request: {self.institution.name} -> {self.add_on.name} ({self.status})"



class InstitutionSubscription(models.Model):
    institution = models.OneToOneField(Institution, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, related_name='subscriptions')
    additional_work_description = models.TextField(blank=True)
    additional_work_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.institution.name} - {self.plan.name if self.plan else 'Custom Plan'} (Total: ₹{self.total_subscription_cost})"

    @property
    def total_subscription_cost(self):
        plan_price = self.plan.price if self.plan else 0
        return plan_price + self.additional_work_charge


class SubscriptionApplication(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Payment Pending (Step 1 Complete)'),
        ('PENDING', 'Pending Developer Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    institution_name = models.CharField(max_length=200)
    institution_slug = models.SlugField(max_length=100)
    contact_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    desired_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    additional_requirements = models.TextField(blank=True, help_text="Custom feature requests or additional needs")
    additional_work_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Developer custom charge for additional work")
    payment_utr = models.CharField(max_length=100, blank=True, help_text="UPI Payment UTR / Transaction Reference ID")
    desired_admin_username = models.CharField(max_length=150)
    desired_admin_email = models.EmailField()
    is_demo = models.BooleanField(default=False, help_text="Application requested 5-Day Free Demo mode")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='DRAFT')
    rejection_reason = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Application for {self.institution_name} ({self.get_status_display()})"

    @property
    def total_charge(self):
        plan_price = self.desired_plan.price if self.desired_plan else 0
        return plan_price + self.additional_work_charge

