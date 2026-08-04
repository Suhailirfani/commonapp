from django.core.management.base import BaseCommand
from apps.tenants.models import SubscriptionPlan
from apps.users.models import User

class Command(BaseCommand):
    help = 'Seeds default subscription plans and developer user'

    def handle(self, *args, **kwargs):
        # 1. Create Default Plans (Only Plan 1 is active)
        p1, _ = SubscriptionPlan.objects.update_or_create(
            code='basic',
            defaults={
                'name': 'Standard Fest Plan',
                'max_competitions': 5,
                'max_contestants': 500,
                'original_price': 3000.00,
                'price': 999.00,
                'description': 'Complete competition management platform with live result ticker, automated grade & rank calculation, and institution portal access. Regular charge ₹3,000 — Special offer now ₹999!',
                'description_ml': 'ലൈവ് റിസൾട്ട് ടിക്കർ, ഓട്ടോമേറ്റഡ് ഗ്രേഡ് & റാങ്ക് കണക്കുകൂട്ടൽ, ഇൻസ്റ്റിറ്റ്യൂഷൻ പോർട്ടൽ എന്നിവ ഉൾപ്പെടുന്ന സമ്പൂർണ്ണ പ്ലാറ്റ്ഫോം. സാധാരണ ചാർജ് ₹3,000 — പ്രത്യേക ഓഫർ വിലയിൽ ഇപ്പോൾ ₹999!',
                'is_active': True
            }
        )
        p2, _ = SubscriptionPlan.objects.update_or_create(
            code='pro',
            defaults={
                'name': 'Pro Multi-Event Fest',
                'max_competitions': 15,
                'max_contestants': 10000,
                'original_price': 6000.00,
                'price': 1999.00,
                'description': 'Full access for multi-category inter-campus fests with priority processing speed and unlimited programs.',
                'description_ml': 'അൺലിമിറ്റഡ് പ്രോഗ്രാമുകളും വേഗതയേറിയ പ്രൊസസിംഗും ഉള്ള മൾട്ടി-കാറ്റഗറി ഇന്റർ-ക്യാമ്പസ് ഫെസ്റ്റുകൾക്കായുള്ള സമ്പൂർണ്ണ പ്ലാറ്റ്ഫോം.',
                'is_active': False
            }
        )
        p3, _ = SubscriptionPlan.objects.update_or_create(
            code='enterprise',
            defaults={
                'name': 'Enterprise Unlimited',
                'max_competitions': 100,
                'max_contestants': 50000,
                'original_price': 12000.00,
                'price': 4999.00,
                'description': 'Unlimited competitions, dedicated server speed, custom domain mapping & 24/7 dedicated support.',
                'description_ml': 'അൺലിമിറ്റഡ് മത്സരങ്ങൾ, ഡെഡിക്കേറ്റഡ് സെർവർ സ്പീഡ്, കസ്റ്റം ഡൊമെയ്ൻ മാപ്പിംഗ്, 24/7 ഡെഡിക്കേറ്റഡ് സപ്പോർട്ട്.',
                'is_active': False
            }
        )

        # 2. Create Developer Super Admin
        dev_user, created = User.objects.get_or_create(
            username='developer',
            defaults={
                'email': 'support@bytolaws.com',
                'role': 'DEVELOPER',
                'is_staff': True,
                'is_superuser': True,
                'is_approved': True,
                'designation': 'BYTOLA WEBSOLUTIONS Developer'
            }
        )
        if created:
            dev_user.set_password('admin123')
            dev_user.save()
            self.stdout.write(self.style.SUCCESS("Created Developer Super Admin (username: 'developer', password: 'admin123')"))
        else:
            self.stdout.write(self.style.SUCCESS("Developer user already exists."))

        self.stdout.write(self.style.SUCCESS("Default Subscription Plans seeded successfully!"))
