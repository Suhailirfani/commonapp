from django.core.management.base import BaseCommand
from apps.tenants.models import Institution, SubscriptionPlan, InstitutionSubscription
from apps.users.models import User
from apps.core.models import (
    Competition, Category, Program, Team, Contestant, 
    Participation, PointsConfig
)
from apps.core.services import calculate_program_results

class Command(BaseCommand):
    help = 'Seeds a fully configured demo tenant institution (Mueeniyya Campus) with sample data'

    def handle(self, *args, **kwargs):
        # 1. Create or Get Institution
        inst, created = Institution.objects.get_or_create(
            slug='mueeniyya',
            defaults={
                'name': 'Mueeniyya Arts & Islamic Campus',
                'email': 'contact@mueeniyya.edu',
                'phone': '+91 9876543210',
                'status': 'APPROVED'
            }
        )

        # 2. Attach Subscription Plan
        plan = SubscriptionPlan.objects.filter(code='pro').first()
        InstitutionSubscription.objects.get_or_create(
            institution=inst,
            defaults={'plan': plan, 'is_active': True}
        )

        # 3. Create Institution Admin User
        admin_user, u_created = User.objects.get_or_create(
            username='admin_mueeniyya',
            defaults={
                'email': 'admin@mueeniyya.edu',
                'role': 'INSTITUTION_ADMIN',
                'institution': inst,
                'is_approved': True,
                'designation': 'Fest Convener'
            }
        )
        if u_created:
            admin_user.set_password('mueeniyya123')
            admin_user.save()

        # 4. Points Config
        PointsConfig.objects.get_or_create(
            institution=inst,
            defaults={
                'rank_1_points': 10,
                'rank_2_points': 6,
                'rank_3_points': 3,
                'grade_a_points': 10,
                'grade_b_points': 6,
                'grade_c_points': 3,
                'grade_a_threshold': 80,
                'grade_b_threshold': 70,
                'grade_c_threshold': 60
            }
        )

        # 5. Create Competition
        comp, _ = Competition.objects.get_or_create(
            institution=inst,
            name='Mueeniyya Grand Fest 2026',
            defaults={'type': 'ON', 'year': 2026, 'is_active': True}
        )

        # 6. Create Categories
        cat_jr, _ = Category.objects.get_or_create(institution=inst, competition=comp, name='Junior Category')
        cat_sr, _ = Category.objects.get_or_create(institution=inst, competition=comp, name='Senior Category')

        # 7. Create Teams
        t_red, _ = Team.objects.get_or_create(institution=inst, competition=comp, name='Red House Alpha', defaults={'code_letter': 'A'})
        t_blue, _ = Team.objects.get_or_create(institution=inst, competition=comp, name='Blue House Titans', defaults={'code_letter': 'B'})
        t_green, _ = Team.objects.get_or_create(institution=inst, competition=comp, name='Green Gladiators', defaults={'code_letter': 'C'})

        # 8. Create Contestants
        c1, _ = Contestant.objects.get_or_create(institution=inst, competition=comp, chest_no=1001, defaults={'name': 'Ahmad Bilal', 'team': t_red, 'category': cat_jr})
        c2, _ = Contestant.objects.get_or_create(institution=inst, competition=comp, chest_no=1002, defaults={'name': 'Zayd Haris', 'team': t_blue, 'category': cat_jr})
        c3, _ = Contestant.objects.get_or_create(institution=inst, competition=comp, chest_no=1003, defaults={'name': 'Umar Farooq', 'team': t_green, 'category': cat_jr})
        c4, _ = Contestant.objects.get_or_create(institution=inst, competition=comp, chest_no=1004, defaults={'name': 'Hamza Ali', 'team': t_red, 'category': cat_sr})

        # 9. Create Programs
        p_quran, _ = Program.objects.get_or_create(
            institution=inst, competition=comp, category=cat_jr, name='Quran Recitation',
            defaults={'is_group': False, 'program_type': 'STAGE', 'is_announced': True}
        )
        p_speech, _ = Program.objects.get_or_create(
            institution=inst, competition=comp, category=cat_jr, name='Elocution (English)',
            defaults={'is_group': False, 'program_type': 'STAGE', 'is_announced': True}
        )

        # 10. Participations & Marks
        p1, _ = Participation.objects.get_or_create(institution=inst, program=p_quran, contestant=c1, defaults={'code_letter': 'X1', 'marks': 92})
        p2, _ = Participation.objects.get_or_create(institution=inst, program=p_quran, contestant=c2, defaults={'code_letter': 'X2', 'marks': 85})
        p3, _ = Participation.objects.get_or_create(institution=inst, program=p_quran, contestant=c3, defaults={'code_letter': 'X3', 'marks': 74})

        calculate_program_results(p_quran)

        self.stdout.write(self.style.SUCCESS("Demo Institution 'Mueeniyya' seeded successfully!"))
        self.stdout.write(self.style.SUCCESS("Admin Credentials -> username: 'admin_mueeniyya', password: 'mueeniyya123'"))
        self.stdout.write(self.style.SUCCESS("Public Portal URL -> /public/mueeniyya/"))
