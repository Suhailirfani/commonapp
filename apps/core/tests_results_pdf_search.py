from django.test import TestCase, Client
from django.urls import reverse
from apps.tenants.models import Institution
from apps.core.models import Category, Program, Participation, Team, Contestant, Competition
from apps.core.services import calculate_program_results
from apps.users.models import User


class ResultsPdfAndSearchTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(
            name="Test Arts Academy",
            slug="test-arts-academy",
            email="test@arts.com",
            status="APPROVED"
        )
        self.user = User.objects.create_user(
            email="admin@test.com",
            username="adminuser",
            password="testpassword",
            role="INSTITUTION_ADMIN",
            is_approved=True,
            institution=self.institution
        )
        self.client = Client()
        self.client.force_login(self.user)

        self.competition = Competition.objects.create(
            institution=self.institution,
            name="Annual Fest 2026",
            year=2026,
            is_active=True
        )

        self.category = Category.objects.create(
            institution=self.institution,
            competition=self.competition,
            name="Senior Category"
        )
        self.team1 = Team.objects.create(
            institution=self.institution,
            competition=self.competition,
            name="Ruby House"
        )
        self.team2 = Team.objects.create(
            institution=self.institution,
            competition=self.competition,
            name="Emerald House"
        )
        self.contestant1 = Contestant.objects.create(
            institution=self.institution,
            competition=self.competition,
            category=self.category,
            team=self.team1,
            name="Ahmad Ali",
            chest_no="101"
        )
        self.contestant2 = Contestant.objects.create(
            institution=self.institution,
            competition=self.competition,
            category=self.category,
            team=self.team2,
            name="Bilal Khan",
            chest_no="102"
        )
        self.program = Program.objects.create(
            institution=self.institution,
            competition=self.competition,
            category=self.category,
            name="English Elocution",
            is_group=False,
            is_announced=True,
            result_number=1
        )
        self.part1 = Participation.objects.create(
            institution=self.institution,
            program=self.program,
            contestant=self.contestant1,
            marks=95,
            rank=1,
            grade="A"
        )
        self.part2 = Participation.objects.create(
            institution=self.institution,
            program=self.program,
            contestant=self.contestant2,
            marks=88,
            rank=2,
            grade="A"
        )

    def test_team_points_cards_page_renders_with_pdf_options(self):
        url = reverse('core:team_points_cards', kwargs={'institution_slug': self.institution.slug})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Download Official Points Sheet (PDF)")
        self.assertContains(res, "Print / Preview Points Sheet")
        self.assertContains(res, "Download Selected Card (JPG)")
        self.assertNotContains(res, "jspdf")
        self.assertNotContains(res, "Download Selected Card (PDF)")

    def test_download_team_standings_pdf(self):
        url = reverse('core:download_team_standings_pdf', kwargs={'institution_slug': self.institution.slug})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'application/pdf')
        self.assertTrue(len(res.content) > 100)

    def test_program_results_page_has_search_bar_and_pdf_download(self):
        url = reverse('core:program_results', kwargs={'institution_slug': self.institution.slug})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "programResultsSearchInput")
        self.assertContains(res, "Hard Copy PDF")
        self.assertContains(res, "Print / Preview")

    def test_program_results_search_filter(self):
        # Querying existing program
        url = reverse('core:program_results', kwargs={'institution_slug': self.institution.slug}) + '?q=Elocution'
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "English Elocution")

        # Querying non-existing program
        url_none = reverse('core:program_results', kwargs={'institution_slug': self.institution.slug}) + '?q=NonExistent'
        res_none = self.client.get(url_none)
        self.assertEqual(res_none.status_code, 200)
        self.assertNotContains(res_none, "English Elocution")

    def test_download_single_program_result_pdf(self):
        url = reverse('core:download_single_result_pdf', kwargs={
            'institution_slug': self.institution.slug,
            'program_id': self.program.id
        })
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'application/pdf')
        self.assertTrue(len(res.content) > 100)

    def test_announcement_balancer_view(self):
        url = reverse('core:announcement_balancer', kwargs={'institution_slug': self.institution.slug})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Score Balancer AI Assistant")
        self.assertContains(res, "Ruby House")

    def test_dense_ranking_on_ties(self):
        # Create contestants 3 and 4
        c3 = Contestant.objects.create(
            institution=self.institution,
            competition=self.competition,
            name="Contestant Three",
            chest_no="103",
            category=self.category,
            team=self.team1
        )
        c4 = Contestant.objects.create(
            institution=self.institution,
            competition=self.competition,
            name="Contestant Four",
            chest_no="104",
            category=self.category,
            team=self.team1
        )
        # Setup marks:
        # part1: 95
        # part2: 95 (tied with part1 -> both rank 1)
        # part3: 90 (next person -> rank 2, dense rank, NOT rank 3!)
        # part4: 85 (next person -> rank 3)
        self.part1.marks = 95
        self.part1.save()
        self.part2.marks = 95
        self.part2.save()

        p3 = Participation.objects.create(
            institution=self.institution,
            program=self.program,
            contestant=c3,
            marks=90
        )
        p4 = Participation.objects.create(
            institution=self.institution,
            program=self.program,
            contestant=c4,
            marks=85
        )

        calculate_program_results(self.program)

        self.part1.refresh_from_db()
        self.part2.refresh_from_db()
        p3.refresh_from_db()
        p4.refresh_from_db()

        self.assertEqual(self.part1.rank, 1)
        self.assertEqual(self.part2.rank, 1)
        self.assertEqual(p3.rank, 2)
        self.assertEqual(p4.rank, 3)
