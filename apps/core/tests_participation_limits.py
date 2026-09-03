from django.test import TestCase, Client
from django.urls import reverse
from apps.tenants.models import Institution
from apps.users.models import User
from apps.core.models import Competition, Category, Team, Program, Contestant, Participation, GroupParticipation

class ParticipationLimitsTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(
            name="Test Academy",
            slug="test-academy",
            email="test@academy.com",
            status="APPROVED",
            allow_developer_access=True
        )
        self.user = User.objects.create_user(
            email="admin@test.com",
            username="admin",
            password="password123",
            role="INSTITUTION_ADMIN",
            is_approved=True,
            institution=self.institution
        )
        self.client = Client()
        self.client.force_login(self.user)

        self.competition = Competition.objects.create(
            institution=self.institution,
            name="Grand Fest 2026",
            year=2026,
            max_single_programs_per_contestant=0,
            max_group_programs_per_contestant=0,
            max_total_programs_per_contestant=0
        )
        self.category = Category.objects.create(
            institution=self.institution,
            competition=self.competition,
            name="Senior"
        )
        self.team = Team.objects.create(
            institution=self.institution,
            competition=self.competition,
            name="Red Team"
        )
        self.contestant = Contestant.objects.create(
            institution=self.institution,
            competition=self.competition,
            team=self.team,
            category=self.category,
            name="Ahmad Ali",
            chest_no=1001
        )
        # Create 5 single programs and 5 group programs
        self.single_programs = []
        for i in range(1, 6):
            prog = Program.objects.create(
                institution=self.institution,
                competition=self.competition,
                category=self.category,
                name=f"Single Program {i}",
                is_group=False
            )
            self.single_programs.append(prog)

        self.group_programs = []
        for i in range(1, 6):
            prog = Program.objects.create(
                institution=self.institution,
                competition=self.competition,
                category=self.category,
                name=f"Group Program {i}",
                is_group=True
            )
            self.group_programs.append(prog)

    def test_default_unlimited(self):
        self.assertEqual(self.competition.max_single_programs_per_contestant, 0)
        self.assertEqual(self.competition.max_group_programs_per_contestant, 0)
        self.assertEqual(self.competition.max_total_programs_per_contestant, 0)
        self.assertFalse(self.competition.has_single_limit)
        self.assertFalse(self.competition.has_group_limit)
        self.assertFalse(self.competition.has_total_limit)

        can_single, _ = self.contestant.can_enroll_single(10)
        self.assertTrue(can_single)
        can_group, _ = self.contestant.can_enroll_group(10)
        self.assertTrue(can_group)

    def test_settings_update_participation_limits(self):
        url = reverse('core:settings', kwargs={'institution_slug': self.institution.slug})
        response = self.client.post(url, {
            'action': 'update_participation_limits',
            'competition_id': self.competition.id,
            'max_single_programs_per_contestant': 4,
            'max_group_programs_per_contestant': 4,
            'max_total_programs_per_contestant': 6,
            'max_team_participants_per_single_program': 4,
            'max_team_entries_per_group_program': 1,
        })
        self.assertEqual(response.status_code, 302)
        self.competition.refresh_from_db()
        self.assertEqual(self.competition.max_single_programs_per_contestant, 4)
        self.assertEqual(self.competition.max_group_programs_per_contestant, 4)
        self.assertEqual(self.competition.max_total_programs_per_contestant, 6)
        self.assertEqual(self.competition.max_team_participants_per_single_program, 4)
        self.assertEqual(self.competition.max_team_entries_per_group_program, 1)
        self.assertTrue(self.competition.has_single_limit)
        self.assertTrue(self.competition.has_group_limit)
        self.assertTrue(self.competition.has_total_limit)
        self.assertTrue(self.competition.has_team_single_limit)
        self.assertTrue(self.competition.has_team_group_limit)

    def test_single_program_limit_enforcement(self):
        self.competition.max_single_programs_per_contestant = 4
        self.competition.save()

        url = reverse('core:contestant_assign_programs', kwargs={
            'institution_slug': self.institution.slug,
            'contestant_id': self.contestant.id
        })

        # Try to assign 5 single programs -> Should fail
        prog_ids_5 = [p.id for p in self.single_programs[:5]]
        res = self.client.post(url, {'selected_program_ids[]': prog_ids_5})
        self.assertEqual(res.status_code, 302)
        # Should have 0 participations
        self.assertEqual(Participation.objects.filter(contestant=self.contestant).count(), 0)

        # Try to assign 4 single programs -> Should succeed
        prog_ids_4 = [p.id for p in self.single_programs[:4]]
        res = self.client.post(url, {'selected_program_ids[]': prog_ids_4})
        self.assertEqual(res.status_code, 302)
        self.assertEqual(Participation.objects.filter(contestant=self.contestant).count(), 4)

    def test_group_program_limit_enforcement(self):
        self.competition.max_group_programs_per_contestant = 4
        self.competition.save()

        url = reverse('core:group_assign', kwargs={'institution_slug': self.institution.slug})

        # Assign 4 group programs successfully
        for i in range(4):
            prog = self.group_programs[i]
            res = self.client.post(url, {
                'action': 'save_group',
                'program_id': prog.id,
                'team_id': self.team.id,
                'group_name': f"Group {i+1}",
                'captain_id': self.contestant.id,
                'member_ids[]': [self.contestant.id]
            })
            self.assertEqual(res.status_code, 302)

        self.assertEqual(self.contestant.group_programs_count, 4)

        # 5th group assignment should be rejected
        prog_5 = self.group_programs[4]
        res = self.client.post(url, {
            'action': 'save_group',
            'program_id': prog_5.id,
            'team_id': self.team.id,
            'group_name': "Group 5",
            'captain_id': self.contestant.id,
            'member_ids[]': [self.contestant.id]
        })
        self.assertEqual(res.status_code, 302)
        self.assertEqual(self.contestant.group_programs_count, 4)
        self.assertFalse(GroupParticipation.objects.filter(program=prog_5).exists())

    def test_program_assign_contestants_limit_enforcement(self):
        self.competition.max_single_programs_per_contestant = 3
        self.competition.save()

        # Enroll contestant in 3 single programs
        for i in range(3):
            Participation.objects.create(
                institution=self.institution,
                program=self.single_programs[i],
                contestant=self.contestant
            )
        self.assertEqual(self.contestant.single_programs_count, 3)

        # Try to assign contestant to 4th single program via program_assign_contestants_view
        url = reverse('core:program_assign_contestants', kwargs={
            'institution_slug': self.institution.slug,
            'program_id': self.single_programs[3].id
        })
        res = self.client.post(url, {'selected_ids[]': [self.contestant.id]})
        self.assertEqual(res.status_code, 302)
        # Should NOT be assigned to the 4th program
        self.assertFalse(Participation.objects.filter(program=self.single_programs[3], contestant=self.contestant).exists())
        self.assertEqual(self.contestant.single_programs_count, 3)

    def test_team_single_participation_limit_enforcement(self):
        # Set fest default max team participants per single program = 4
        self.competition.max_team_participants_per_single_program = 4
        self.competition.save()

        # Create 4 more contestants in the same team
        team_members = [self.contestant]
        for i in range(2, 6):
            c = Contestant.objects.create(
                institution=self.institution,
                competition=self.competition,
                team=self.team,
                category=self.category,
                name=f"Member {i}",
                chest_no=1000 + i
            )
            team_members.append(c)

        prog = self.single_programs[0]

        # Assign 4 team members to prog -> Should succeed
        for i in range(4):
            Participation.objects.create(
                institution=self.institution,
                program=prog,
                contestant=team_members[i]
            )

        self.assertEqual(prog.get_team_participants_count(self.team), 4)

        # 5th contestant tries to enroll in prog via contestant_assign_programs -> Should fail
        c5 = team_members[4]
        url = reverse('core:contestant_assign_programs', kwargs={
            'institution_slug': self.institution.slug,
            'contestant_id': c5.id
        })
        res = self.client.post(url, {'selected_program_ids[]': [prog.id]})
        self.assertEqual(res.status_code, 302)
        # Should not be enrolled
        self.assertFalse(Participation.objects.filter(program=prog, contestant=c5).exists())

    def test_team_group_entries_limit_enforcement(self):
        # Set fest default max team group entries = 1
        self.competition.max_team_entries_per_group_program = 1
        self.competition.save()

        prog = self.group_programs[0]
        url = reverse('core:group_assign', kwargs={'institution_slug': self.institution.slug})

        # 1st group entry for Red Team -> Should succeed
        res = self.client.post(url, {
            'action': 'save_group',
            'program_id': prog.id,
            'team_id': self.team.id,
            'group_name': "Red Team Group A",
            'captain_id': self.contestant.id,
            'member_ids[]': [self.contestant.id]
        })
        self.assertEqual(res.status_code, 302)
        self.assertEqual(GroupParticipation.objects.filter(program=prog, team=self.team).count(), 1)

        # 2nd group entry for Red Team -> Should fail (limit is 1)
        res = self.client.post(url, {
            'action': 'save_group',
            'program_id': prog.id,
            'team_id': self.team.id,
            'group_name': "Red Team Group B",
            'captain_id': self.contestant.id,
            'member_ids[]': [self.contestant.id]
        })
        self.assertEqual(res.status_code, 302)
        self.assertEqual(GroupParticipation.objects.filter(program=prog, team=self.team).count(), 1)

    def test_team_limit_program_override(self):
        # Fest default single is 4, but program limit is 2
        self.competition.max_team_participants_per_single_program = 4
        self.competition.save()

        prog = self.single_programs[1]
        prog.max_participants_per_team = 2
        prog.save()

        self.assertEqual(prog.effective_max_participants_per_team, 2)

        c2 = Contestant.objects.create(
            institution=self.institution,
            competition=self.competition,
            team=self.team,
            category=self.category,
            name="Member Two",
            chest_no=1002
        )
        c3 = Contestant.objects.create(
            institution=self.institution,
            competition=self.competition,
            team=self.team,
            category=self.category,
            name="Member Three",
            chest_no=1003
        )

        # Batch assign 3 members to program with limit 2 -> Should fail
        url = reverse('core:program_assign_contestants', kwargs={
            'institution_slug': self.institution.slug,
            'program_id': prog.id
        })
        res = self.client.post(url, {'selected_ids[]': [self.contestant.id, c2.id, c3.id]})
        self.assertEqual(res.status_code, 302)
        self.assertEqual(Participation.objects.filter(program=prog).count(), 0)

        # Batch assign 2 members -> Should succeed
        res = self.client.post(url, {'selected_ids[]': [self.contestant.id, c2.id]})
        self.assertEqual(res.status_code, 302)
        self.assertEqual(Participation.objects.filter(program=prog).count(), 2)

    def test_ranks_only_mode_and_grade_points(self):
        from apps.core.models import PointsConfig
        config, _ = PointsConfig.objects.get_or_create(
            institution=self.institution,
            defaults={
                'single_rank_1_points': 5,
                'single_grade_aplus_points': 6,
                'enable_grades': True
            }
        )
        config.single_rank_1_points = 5
        config.single_grade_aplus_points = 6
        config.enable_grades = True
        config.save()

        p = Participation.objects.create(
            institution=self.institution,
            program=self.single_programs[0],
            contestant=self.contestant,
            rank=1,
            grade='A+'
        )

        # In standard mode: 5 rank pts + 6 grade pts = 11 pts
        self.assertEqual(p.total_points, 11)
        self.assertTrue(self.institution.has_grades)

        # Switch to Ranks Only mode: enable_grades = False
        config.enable_grades = False
        config.save()

        # In Ranks Only mode: 5 rank pts + 0 grade pts = 5 pts
        self.assertEqual(p.total_points, 5)
        self.assertFalse(self.institution.has_grades)

    def test_operational_locks_actions_and_enforcement(self):
        # 1. Test Operations Settings View - Lock All
        ops_url = reverse('core:settings_operations', kwargs={'institution_slug': self.institution.slug})
        res = self.client.post(ops_url, {'action': 'lock_all'})
        self.assertEqual(res.status_code, 302)
        
        self.competition.refresh_from_db()
        self.assertFalse(self.competition.allow_team_management)
        self.assertFalse(self.competition.allow_category_management)
        self.assertFalse(self.competition.allow_program_management)
        self.assertFalse(self.competition.allow_contestant_registration)
        self.assertFalse(self.competition.allow_program_assignment)

        self.assertFalse(self.institution.allows_team_management)
        self.assertFalse(self.institution.allows_category_management)
        self.assertFalse(self.institution.allows_program_management)
        self.assertFalse(self.institution.allows_contestant_registration)
        self.assertFalse(self.institution.allows_program_assignment)

        # 2. Test Backend Enforcement when locked
        # Attempt to create Team
        team_url = reverse('core:team_list', kwargs={'institution_slug': self.institution.slug})
        res = self.client.post(team_url, {'competition_id': self.competition.id, 'name': 'Blocked Team'})
        self.assertEqual(res.status_code, 302)
        self.assertFalse(Team.objects.filter(name='Blocked Team').exists())

        # Attempt to create Category
        cat_url = reverse('core:category_list', kwargs={'institution_slug': self.institution.slug})
        res = self.client.post(cat_url, {'competition_id': self.competition.id, 'name': 'Blocked Category'})
        self.assertEqual(res.status_code, 302)
        self.assertFalse(Category.objects.filter(name='Blocked Category').exists())

        # Attempt to create Program
        prog_url = reverse('core:program_create', kwargs={'institution_slug': self.institution.slug})
        res = self.client.post(prog_url, {
            'competition_id': self.competition.id,
            'category_id': self.category.id,
            'name': 'Blocked Program'
        })
        self.assertEqual(res.status_code, 302)
        self.assertFalse(Program.objects.filter(name='Blocked Program').exists())

        # Attempt to create Contestant
        c_url = reverse('core:contestant_create', kwargs={'institution_slug': self.institution.slug})
        res = self.client.post(c_url, {
            'competition_id': self.competition.id,
            'category_id': self.category.id,
            'team_id': self.team.id,
            'name': 'Blocked Contestant'
        })
        self.assertEqual(res.status_code, 302)
        self.assertFalse(Contestant.objects.filter(name='Blocked Contestant').exists())

        # 3. Test Unlock All
        res = self.client.post(ops_url, {'action': 'unlock_all'})
        self.assertEqual(res.status_code, 302)
        self.competition.refresh_from_db()
        self.assertTrue(self.competition.allow_team_management)
        self.assertTrue(self.competition.allow_category_management)
        self.assertTrue(self.competition.allow_program_management)
        self.assertTrue(self.competition.allow_contestant_registration)
        self.assertTrue(self.competition.allow_program_assignment)

        # Attempt to create Team after unlocking -> Should succeed
        res = self.client.post(team_url, {'competition_id': self.competition.id, 'name': 'Allowed Team'})
        self.assertEqual(res.status_code, 302)
        self.assertTrue(Team.objects.filter(name='Allowed Team').exists())

    def test_bulk_reports_data_fetching(self):
        # Create single and group participations
        prog_single = self.single_programs[0]
        p_single = Participation.objects.create(
            institution=self.institution,
            program=prog_single,
            contestant=self.contestant,
            code_letter='A1'
        )

        prog_group = self.group_programs[0]
        gp = GroupParticipation.objects.create(
            institution=self.institution,
            program=prog_group,
            team=self.team,
            captain=self.contestant,
            code_letter='G1'
        )

        # 1. Bulk Green Room PDF
        url = reverse('core:download_bulk_green_room_pdf', kwargs={'institution_slug': self.institution.slug})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'application/pdf')

        # 2. Bulk Call List PDF
        url = reverse('core:download_bulk_call_list_pdf', kwargs={'institution_slug': self.institution.slug})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'application/pdf')

        # 3. Bulk Valuation Form PDF
        url = reverse('core:download_bulk_valuation_form_pdf', kwargs={'institution_slug': self.institution.slug})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'application/pdf')

        # 4. Contestants Teamwise PDF
        url = reverse('core:download_contestants_teamwise_pdf', kwargs={'institution_slug': self.institution.slug})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'application/pdf')

        # 5. Assigned Programs Teamwise PDF
        url = reverse('core:download_assigned_programs_teamwise_pdf', kwargs={'institution_slug': self.institution.slug})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'application/pdf')


