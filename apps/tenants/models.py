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
        return f"{self.name} (₹{self.price} - Regular ₹{self.original_price})"

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
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='DRAFT')
    rejection_reason = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Application for {self.institution_name} ({self.get_status_display()})"

    @property
    def total_charge(self):
        plan_price = self.desired_plan.price if self.desired_plan else 0
        return plan_price + self.additional_work_charge

