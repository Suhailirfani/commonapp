from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import SubscriptionPlan, SubscriptionApplication, Institution, InstitutionSubscription, AddOn, GrantedAddOn
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
        is_demo = request.POST.get('is_demo') == '1'

        plan = SubscriptionPlan.objects.filter(id=plan_id).first() if plan_id else None

        # Check if username or slug already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' is already taken. Please choose another username.")
            return render(request, 'tenants/apply.html', {'plans': plans})

        if Institution.objects.filter(slug=slug).exists():
            messages.error(request, f"Institution Code / Slug '{slug}' is already taken. Please choose another code.")
            return render(request, 'tenants/apply.html', {'plans': plans})

        if is_demo:
            from datetime import timedelta
            from django.utils import timezone
            from django.contrib.auth import login

            demo_expires_at = timezone.now() + timedelta(days=5)

            # Create Institution in APPROVED status for 5-Day Demo
            institution = Institution.objects.create(
                name=name,
                slug=slug,
                email=email,
                phone=phone,
                status='APPROVED',
                is_demo=True,
                demo_expires_at=demo_expires_at
            )

            # Create Admin User (Auto-Approved)
            admin_user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role='INSTITUTION_ADMIN',
                institution=institution,
                is_approved=True,
                designation='Institution Administrator'
            )

            # Provision default subscription record
            if plan:
                InstitutionSubscription.objects.create(
                    institution=institution,
                    plan=plan,
                    additional_work_description="5-Day Free Demo Trial Workspace",
                    additional_work_charge=0.00,
                    is_active=True
                )

            # Record Application
            SubscriptionApplication.objects.create(
                institution_name=name,
                institution_slug=slug,
                contact_name=contact,
                email=email,
                phone=phone,
                desired_plan=plan,
                additional_requirements=additional_requirements,
                desired_admin_username=username,
                desired_admin_email=email,
                is_demo=True,
                status='APPROVED'
            )

            # Log in user immediately
            login(request, admin_user)

            messages.success(request, f"🎉 Welcome to '{institution.name}'! Your 5-Day Free Demo workspace has been activated. Demo expires in 5 days.")
            return redirect('core:dashboard', institution_slug=institution.slug)

        else:
            # Standard paid flow
            institution = Institution.objects.create(
                name=name,
                slug=slug,
                email=email,
                phone=phone,
                status='PENDING'
            )

            admin_user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role='INSTITUTION_ADMIN',
                institution=institution,
                is_approved=False,
                designation='Institution Administrator'
            )

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
def demo_pay_now_view(request, institution_slug):
    institution = get_object_or_404(Institution, slug=institution_slug)
    if not (request.user.is_institution_admin or request.user.is_developer):
        messages.error(request, "Access Denied.")
        return redirect('core:dashboard', institution_slug=institution.slug)

    sub = getattr(institution, 'subscription', None)
    plan = sub.plan if sub else SubscriptionPlan.objects.first()

    if request.method == 'POST':
        payment_utr = request.POST.get('payment_utr', '').strip()
        app_req = SubscriptionApplication.objects.filter(institution_slug=institution.slug).first()
        if not app_req:
            app_req = SubscriptionApplication.objects.create(
                institution_name=institution.name,
                institution_slug=institution.slug,
                contact_name=request.user.get_full_name() or request.user.username,
                email=request.user.email,
                phone=institution.phone or '',
                desired_plan=plan,
                desired_admin_username=request.user.username,
                desired_admin_email=request.user.email,
                status='PENDING',
                is_demo=True
            )
        
        app_req.payment_utr = payment_utr
        app_req.status = 'PENDING'
        app_req.save()

        messages.success(request, f"Payment UTR reference '{payment_utr}' submitted successfully! Developer will verify your payment and convert your demo workspace into a permanent active subscription.")
        return redirect('core:dashboard', institution_slug=institution.slug)

    return render(request, 'tenants/demo_pay_now.html', {
        'institution': institution,
        'plan': plan,
        'upi_id': '313suhi313@oksbi'
    })


@login_required
def developer_dashboard_view(request):
    if not request.user.is_developer:
        messages.error(request, "Access Denied: Developer Super Admin clearance required.")
        return redirect('landing_page')

    pending_apps = SubscriptionApplication.objects.filter(status__in=['PENDING', 'DRAFT']).order_by('-submitted_at')
    institutions = Institution.objects.all().prefetch_related('granted_add_ons__add_on').order_by('-created_at')
    plans = SubscriptionPlan.objects.all().order_by('-id')
    add_ons = AddOn.objects.all().order_by('-id')
    granted_add_ons = GrantedAddOn.objects.select_related('institution', 'add_on').order_by('-granted_at')

    # Map applications and admin users for instant contact info resolution
    app_map = {app.institution_slug: app for app in SubscriptionApplication.objects.all()}
    from apps.users.models import User
    admin_user_map = {u.institution_id: u for u in User.objects.filter(role='INSTITUTION_ADMIN')}

    for inst in institutions:
        app = app_map.get(inst.slug)
        if app and app.contact_name:
            inst.contact_name_val = app.contact_name
        else:
            admin_u = admin_user_map.get(inst.id)
            inst.contact_name_val = admin_u.get_full_name() if (admin_u and admin_u.get_full_name()) else (admin_u.username if admin_u else "N/A")
        
        inst.contact_phone_val = inst.phone or (app.phone if app else "N/A")
        admin_u = admin_user_map.get(inst.id)
        inst.admin_username_val = app.desired_admin_username if app else (admin_u.username if admin_u else "admin")

    return render(request, 'tenants/developer_dashboard.html', {
        'pending_apps': pending_apps,
        'institutions': institutions,
        'plans': plans,
        'add_ons': add_ons,
        'granted_add_ons': granted_add_ons,
    })


@login_required
def add_on_manage_view(request):
    if not request.user.is_developer:
        messages.error(request, "Access Denied.")
        return redirect('landing_page')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create_addon':
            name = request.POST.get('name', '').strip()
            code = request.POST.get('code', '').strip()
            price_raw = request.POST.get('price', '0').strip()
            desc = request.POST.get('description', '').strip()
            from decimal import Decimal
            price = Decimal(price_raw) if price_raw else Decimal('0.00')

            if name:
                from django.utils.text import slugify
                addon_code = code if code else slugify(name)
                addon, created = AddOn.objects.get_or_create(
                    code=addon_code,
                    defaults={'name': name, 'price': price, 'description': desc, 'is_active': True}
                )
                if not created:
                    addon.name = name
                    addon.price = price
                    addon.description = desc
                    addon.is_active = True
                    addon.save()
                messages.success(request, f"Add-On feature '{name}' saved with price ₹{price}!")
        
        elif action == 'grant_addon':
            inst_id = request.POST.get('institution_id')
            addon_id = request.POST.get('addon_id')
            notes = request.POST.get('notes', '').strip()

            inst = Institution.objects.filter(id=inst_id).first()
            addon = AddOn.objects.filter(id=addon_id).first()

            if inst and addon:
                grant, created = GrantedAddOn.objects.get_or_create(
                    institution=inst,
                    add_on=addon,
                    defaults={'notes': notes, 'is_active': True}
                )
                if not created:
                    grant.is_active = True
                    grant.notes = notes
                    grant.save()
                messages.success(request, f"Add-On feature '{addon.name}' granted to '{inst.name}' successfully!")

        elif action == 'toggle_grant':
            grant_id = request.POST.get('grant_id')
            grant = GrantedAddOn.objects.filter(id=grant_id).first()
            if grant:
                grant.is_active = not grant.is_active
                grant.save()
                status_str = "activated" if grant.is_active else "revoked"
                messages.success(request, f"Add-On feature '{grant.add_on.name}' has been {status_str} for '{grant.institution.name}'.")

    return redirect('tenants:developer_dashboard')


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
        institution.is_demo = False  # Clear Demo mode on full approval!
        institution.demo_expires_at = None
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
