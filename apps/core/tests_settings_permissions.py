from django.test import TestCase, Client
from django.urls import reverse
from apps.tenants.models import Institution
from apps.users.models import User
from apps.core.models import Competition, Category, Program, Team

class SettingsPermissionsTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(
            name="Permissions Fest Academy",
            slug="permissions-fest",
            email="permissions@fest.com",
            status="APPROVED",
            allow_developer_access=True
        )

        self.competition = Competition.objects.create(
            institution=self.institution,
            name="Fest 2026",
            year=2026,
            is_active=True
        )

        self.team = Team.objects.create(
            institution=self.institution,
            competition=self.competition,
            name="Emerald Warriors"
        )

        self.category = Category.objects.create(
            institution=self.institution,
            competition=self.competition,
            name="General"
        )

        self.program = Program.objects.create(
            institution=self.institution,
            competition=self.competition,
            category=self.category,
            name="Elocution"
        )

        # Users
        self.superuser = User.objects.create_superuser(
            username="superadmin",
            password="password123",
            institution=self.institution
        )

        self.admin_user = User.objects.create_user(
            username="inst_admin",
            password="password123",
            role="INSTITUTION_ADMIN",
            is_approved=True,
            institution=self.institution
        )

        self.sub_admin_user = User.objects.create_user(
            username="sub_admin",
            password="password123",
            role="SUB_ADMIN",
            is_approved=True,
            institution=self.institution
        )

        self.team_leader = User.objects.create_user(
            username="team_leader",
            password="password123",
            role="TEAM_LEADER",
            is_approved=True,
            institution=self.institution
        )
        self.team.team_leader = self.team_leader
        self.team.save()

        self.tabulator = User.objects.create_user(
            username="tabulator_user",
            password="password123",
            role="TABULATOR",
            is_approved=True,
            institution=self.institution
        )

        self.client = Client()

    def test_team_leader_cannot_access_settings_pages(self):
        self.client.force_login(self.team_leader)

        settings_urls = [
            reverse('core:settings', kwargs={'institution_slug': self.institution.slug}),
            reverse('core:settings_operations', kwargs={'institution_slug': self.institution.slug}),
            reverse('core:settings_fests', kwargs={'institution_slug': self.institution.slug}),
            reverse('core:settings_participation_limits', kwargs={'institution_slug': self.institution.slug}),
            reverse('core:settings_chest_numbers', kwargs={'institution_slug': self.institution.slug}),
            reverse('core:settings_public_portal', kwargs={'institution_slug': self.institution.slug}),
            reverse('core:settings_support_access', kwargs={'institution_slug': self.institution.slug}),
            reverse('core:settings_addons', kwargs={'institution_slug': self.institution.slug}),
            reverse('core:points_config', kwargs={'institution_slug': self.institution.slug}),
            reverse('core:stage_list', kwargs={'institution_slug': self.institution.slug}),
        ]

        expected_redirect = reverse('core:dashboard', kwargs={'institution_slug': self.institution.slug})

        for url in settings_urls:
            response = self.client.get(url, follow=False)
            self.assertEqual(
                response.status_code, 302,
                f"Team Leader was not redirected when accessing: {url}"
            )
            self.assertIn(expected_redirect, response.url)

    def test_team_leader_cannot_perform_settings_operations(self):
        self.client.force_login(self.team_leader)

        # 1. Attempt to lock operations via POST
        ops_url = reverse('core:settings_operations', kwargs={'institution_slug': self.institution.slug})
        resp = self.client.post(ops_url, {'action': 'lock_all'})
        self.assertEqual(resp.status_code, 302)
        self.competition.refresh_from_db()
        self.assertTrue(self.competition.allow_contestant_registration)

        # 2. Attempt to update participation limits via POST
        limits_url = reverse('core:settings_participation_limits', kwargs={'institution_slug': self.institution.slug})
        resp = self.client.post(limits_url, {
            'competition_id': self.competition.id,
            'max_single_programs_per_contestant': 99
        })
        self.assertEqual(resp.status_code, 302)
        self.competition.refresh_from_db()
        self.assertEqual(self.competition.max_single_programs_per_contestant, 0)

        # 3. Attempt to modify points via API
        api_url = reverse('core:program_points_config_api', kwargs={
            'institution_slug': self.institution.slug,
            'program_id': self.program.id
        })
        resp = self.client.post(api_url, {
            'is_custom': 'true',
            'rank_1_points': 50
        })
        self.assertEqual(resp.status_code, 403)

    def test_tabulator_cannot_access_settings(self):
        self.client.force_login(self.tabulator)
        url = reverse('core:settings', kwargs={'institution_slug': self.institution.slug})
        response = self.client.get(url, follow=False)
        self.assertEqual(response.status_code, 302)
        expected_redirect = reverse('core:dashboard', kwargs={'institution_slug': self.institution.slug})
        self.assertIn(expected_redirect, response.url)

    def test_sub_admin_can_access_and_operate_settings(self):
        self.client.force_login(self.sub_admin_user)

        settings_url = reverse('core:settings', kwargs={'institution_slug': self.institution.slug})
        resp = self.client.get(settings_url)
        self.assertEqual(resp.status_code, 200)

        ops_url = reverse('core:settings_operations', kwargs={'institution_slug': self.institution.slug})
        resp = self.client.get(ops_url)
        self.assertEqual(resp.status_code, 200)

        # Sub-admin can update limits
        limits_url = reverse('core:settings_participation_limits', kwargs={'institution_slug': self.institution.slug})
        resp = self.client.post(limits_url, {
            'competition_id': self.competition.id,
            'max_single_programs_per_contestant': 5,
            'max_group_programs_per_contestant': 3,
            'max_total_programs_per_contestant': 8
        })
        self.assertEqual(resp.status_code, 302)
        self.competition.refresh_from_db()
        self.assertEqual(self.competition.max_single_programs_per_contestant, 5)

    def test_institution_admin_can_access_and_operate_settings(self):
        self.client.force_login(self.admin_user)

        settings_url = reverse('core:settings', kwargs={'institution_slug': self.institution.slug})
        resp = self.client.get(settings_url)
        self.assertEqual(resp.status_code, 200)

    def test_superuser_can_access_settings(self):
        self.client.force_login(self.superuser)

        settings_url = reverse('core:settings', kwargs={'institution_slug': self.institution.slug})
        resp = self.client.get(settings_url)
        self.assertEqual(resp.status_code, 200)
