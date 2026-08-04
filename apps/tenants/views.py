from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import SubscriptionPlan, SubscriptionApplication, Institution, InstitutionSubscription
from .forms import SubscriptionPlanForm
from apps.users.models import User

def landing_page_view(request):
    plans = SubscriptionPlan.objects.filter(is_active=True)
    return render(request, 'landing.html', {'plans': plans})

def subscription_apply_view(request):
    plans = SubscriptionPlan.objects.filter(is_active=True)
    if request.method == 'POST':
        name = request.POST.get('institution_name')
        slug = request.POST.get('institution_slug')
        contact = request.POST.get('contact_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        plan_id = request.POST.get('plan_id')
        username = request.POST.get('username')
        password = request.POST.get('password')
        additional_requirements = request.POST.get('additional_requirements', '').strip()

        plan = SubscriptionPlan.objects.filter(id=plan_id).first() if plan_id else None

        # Check if username or slug already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' is already taken. Please choose another username.")
            return render(request, 'tenants/apply.html', {'plans': plans})

        if Institution.objects.filter(slug=slug).exists():
            messages.error(request, f"Institution Code / Slug '{slug}' is already taken. Please choose another code.")
            return render(request, 'tenants/apply.html', {'plans': plans})

        # Create Institution (PENDING)
        institution = Institution.objects.create(
            name=name,
            slug=slug,
            email=email,
            phone=phone,
            status='PENDING'
        )

        # Create Admin User (is_approved=False)
        admin_user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role='INSTITUTION_ADMIN',
            institution=institution,
            is_approved=False,
            designation='Institution Administrator'
        )

        # Record Application in DRAFT status (Step 1 Complete)
        app = SubscriptionApplication.objects.create(
            institution_name=name,
            institution_slug=slug,
            contact_name=contact,
            email=email,
            phone=phone,
            desired_plan=plan,
            additional_requirements=additional_requirements,
            desired_admin_username=username,
            desired_admin_email=email,
            status='DRAFT'
        )

        messages.info(request, "Step 1 complete! Your institution details have been saved. Please complete the UPI payment to finalize your workspace request.")
        return redirect('tenants:apply_payment', app_id=app.id)

    return render(request, 'tenants/apply.html', {'plans': plans})


def subscription_payment_view(request, app_id):
    app_req = get_object_or_404(SubscriptionApplication, id=app_id)
    if request.method == 'POST':
        payment_utr = request.POST.get('payment_utr', '').strip()
        app_req.payment_utr = payment_utr
        app_req.status = 'PENDING'
        app_req.save()

        messages.success(request, f"Payment reference '{payment_utr}' submitted successfully! Developer will review and activate your workspace soon.")
        return redirect('landing_page')

    return render(request, 'tenants/apply_payment.html', {'app_req': app_req, 'upi_id': '313suhi313@oksbi'})


@login_required
def developer_dashboard_view(request):
    if not request.user.is_developer:
        messages.error(request, "Access Denied: Developer Super Admin clearance required.")
        return redirect('landing_page')

    pending_apps = SubscriptionApplication.objects.filter(status__in=['PENDING', 'DRAFT']).order_by('-submitted_at')
    institutions = Institution.objects.all().order_by('-created_at')
    plans = SubscriptionPlan.objects.all().order_by('-id')
    return render(request, 'tenants/developer_dashboard.html', {
        'pending_apps': pending_apps,
        'institutions': institutions,
        'plans': plans
    })


@login_required
def approve_application_view(request, app_id):
    if not request.user.is_developer:
        messages.error(request, "Access Denied.")
        return redirect('landing_page')

    app_req = get_object_or_404(SubscriptionApplication, id=app_id)
    institution = Institution.objects.filter(slug=app_req.institution_slug).first()

    # Process additional work charge if provided via POST
    if request.method == 'POST':
        work_charge_raw = request.POST.get('additional_work_charge', '0').strip()
        try:
            from decimal import Decimal
            app_req.additional_work_charge = Decimal(work_charge_raw) if work_charge_raw else Decimal('0.00')
            app_req.save()
        except Exception:
            pass

    if institution:
        institution.status = 'APPROVED'
        institution.save()

        # Approve admin user
        admin_user = User.objects.filter(institution=institution, role='INSTITUTION_ADMIN').first()
        if admin_user:
            admin_user.is_approved = True
            admin_user.save()

        # Provision default subscription with additional work charge
        if app_req.desired_plan:
            InstitutionSubscription.objects.get_or_create(
                institution=institution,
                defaults={
                    'plan': app_req.desired_plan,
                    'additional_work_description': app_req.additional_requirements,
                    'additional_work_charge': app_req.additional_work_charge,
                    'is_active': True
                }
            )

        app_req.status = 'APPROVED'
        app_req.save()
        messages.success(request, f"Institution '{institution.name}' approved and workspace activated successfully (Total Charge: ₹{app_req.total_charge})!")

    return redirect('tenants:developer_dashboard')


@login_required
def reject_application_view(request, app_id):
    if not request.user.is_developer:
        messages.error(request, "Access Denied.")
        return redirect('landing_page')

    app_req = get_object_or_404(SubscriptionApplication, id=app_id)
    institution = Institution.objects.filter(slug=app_req.institution_slug).first()

    if institution:
        institution.status = 'REJECTED'
        institution.save()

    app_req.status = 'REJECTED'
    app_req.rejection_reason = request.POST.get('reason', 'Rejected by developer')
    app_req.save()

    messages.info(request, f"Application for '{app_req.institution_name}' has been rejected.")
    return redirect('tenants:developer_dashboard')


# Subscription Plan Developer Actions

@login_required
def plan_create_view(request):
    if not request.user.is_developer:
        messages.error(request, "Access Denied: Developer clearance required.")
        return redirect('landing_page')

    if request.method == 'POST':
        form = SubscriptionPlanForm(request.POST)
        if form.is_valid():
            plan = form.save()
            messages.success(request, f"Subscription plan '{plan.name}' created successfully!")
            return redirect('tenants:developer_dashboard')
    else:
        form = SubscriptionPlanForm()

    return render(request, 'tenants/plan_form.html', {'form': form, 'title': 'Create New Subscription Plan'})


@login_required
def plan_edit_view(request, plan_id):
    if not request.user.is_developer:
        messages.error(request, "Access Denied: Developer clearance required.")
        return redirect('landing_page')

    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    if request.method == 'POST':
        form = SubscriptionPlanForm(request.POST, instance=plan)
        if form.is_valid():
            plan = form.save()
            messages.success(request, f"Subscription plan '{plan.name}' updated successfully!")
            return redirect('tenants:developer_dashboard')
    else:
        form = SubscriptionPlanForm(instance=plan)

    return render(request, 'tenants/plan_form.html', {'form': form, 'title': f'Edit Plan - {plan.name}', 'plan': plan})


@login_required
def plan_toggle_status_view(request, plan_id):
    if not request.user.is_developer:
        messages.error(request, "Access Denied.")
        return redirect('landing_page')

    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    plan.is_active = not plan.is_active
    plan.save()
    status_str = "activated" if plan.is_active else "deactivated"
    messages.success(request, f"Subscription plan '{plan.name}' has been {status_str}.")
    return redirect('tenants:developer_dashboard')


@login_required
def plan_delete_view(request, plan_id):
    if not request.user.is_developer:
        messages.error(request, "Access Denied.")
        return redirect('landing_page')

    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    if plan.subscriptions.exists():
        messages.error(request, f"Cannot delete plan '{plan.name}' because active institutions are currently subscribed to it. Deactivate it instead.")
    else:
        plan_name = plan.name
        plan.delete()
        messages.success(request, f"Subscription plan '{plan_name}' deleted successfully.")
    return redirect('tenants:developer_dashboard')
