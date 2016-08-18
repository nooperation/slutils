from django.test import TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from .models import Sound
import json


def create_test_sounds():
    valid_uuids = [
        '41f94400-2a3e-408a-9b80-1774724f62af',
        'a7488bf2-fef3-4846-a898-fc60dea73dbb',
        '73671ba8-71a4-463a-a836-eb79ecf50386',
        'ac3c7513-f88c-48d8-8e04-58f75cde1351',
        'be973d5f-f254-439f-8e6b-fd962734ec9c',
        '6d660da5-8240-43ac-b08e-83650f5f5a66',
        '6f24a740-49b2-4bdf-b0a8-6d5843de1e05',
        '4d16a7af-fe41-4d42-bd9f-87e66b7eddf2',
        '66052737-fe66-4a80-abdf-011fae301d81',
        'd23efdad-5f6b-48db-8b1d-cf0d50cc0070',
    ]

    sounds = []
    duration = 1
    for valid_uuid in valid_uuids:
        sounds.append(Sound.objects.create(uuid=valid_uuid, duration=duration, created_on='2016-08-17 20:49:53.123456+08:00'))
        duration <<= 1
    return sounds


def assert_sound_queryset_equal(test, sound_queryset, expected_sounds):
    expected_values = []
    for item in expected_sounds:
        expected_values.append("<Sound: {0}>".format(item))
    return test.assertQuerysetEqual(qs=sound_queryset, values=expected_values, ordered=False)


# Create your tests here.
class SoundModelTests(TestCase):
    def test_normal_creation(self):
        """
        Normal creation of multiple unique sounds
        """
        sounds = create_test_sounds()
        assert_sound_queryset_equal(self, Sound.objects.all(), sounds)
        for sound in sounds:
            sound.full_clean()

    def test_duplicate_sounds(self):
        """
        The UUID field must be unique
        """
        new_sound = Sound.objects.create(uuid='41f94400-2a3e-408a-9b80-1774724f62af', duration=123, created_on='2016-08-17 20:49:53.123456+08:00')
        with self.assertRaises(IntegrityError):
            Sound.objects.create(uuid=new_sound.uuid, duration=123).full_clean()

    def test_missing_uuid(self):
        """
        The UUID field must exist
        """
        with self.assertRaises(ValidationError):
            Sound(duration=123, created_on='2016-08-17 20:49:53.123456+08:00').full_clean()

    def test_bad_uuid(self):
        """
        The UUID field must be valid
        """
        invalid_uuids = [
            '',
            '41f94400-2a3e-408a-9b80-1774724f62a',
            '41f94400-2a3e-408a-9b80-1774724f62aaa',
            'zz488bf2-zzzz-zzzz-zzzz-zzzzzzzzzzaf',
            'ac3c75131f88c148d818e04158f75cde1351',
        ]
        for invalid_uuid in invalid_uuids:
            with self.assertRaises(ValidationError):
                Sound(uuid=invalid_uuid, duration=123, created_on='2016-08-17 20:49:53.123456+08:00').full_clean()

    def test_missing_duration(self):
        """
        The duration must exist
        """
        with self.assertRaises(ValidationError):
            Sound(uuid='41f94400-2a3e-408a-9b80-1774724f62af', created_on='2016-08-17 20:49:53.123456+08:00').full_clean()

    def test_missing_date(self):
        """
        created_on date must exist.
        """
        with self.assertRaises(ValidationError):
            Sound(uuid='41f94400-2a3e-408a-9b80-1774724f62af', duration=123).full_clean()


class IndexViewTests(TestCase):
    def test_index_view_no_sounds(self):
        """
        An index view with no sounds must have an empty sound_list
        """
        response = self.client.get(reverse('sounds:index'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context)
        self.assertQuerysetEqual(response.context['sound_list'], [])

    def test_index_view_multiple_sounds(self):
        """
        An index view with sounds must have a populated sound_list
        """
        sounds = create_test_sounds()
        response = self.client.get(reverse('sounds:index'))

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context)
        assert_sound_queryset_equal(self, response.context['sound_list'], sounds)


class AllViewTests(TestCase):

    def test_all_view_with_no_sounds(self):
        """
        All view must 404 when no sounds are present.
        """
        response = self.client.get(reverse('sounds:all_json'))
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertDictEqual(json_data, {'sounds': []})

    def test_all_view_with_multiple_sounds(self):
        """
        All view must 404 when no sounds are present.
        """
        sounds = create_test_sounds()
        json_sounds = []

        for sound in sounds:
            json_sounds.append(sound.uuid)
        expected_json = {'sounds': json_sounds}

        response = self.client.get(reverse('sounds:all_json'))
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertDictEqual(json_data, expected_json)


class RandomViewTests(TestCase):

    def test_random_view_with_no_sounds(self):
        """
        Random view must 404 when no sounds are present.
        """
        response = self.client.get(reverse('sounds:random_json'))
        self.assertEqual(response.status_code, 404)

    def test_random_view_with_single_sound(self):
        """
        Random JSON must return a single random sound via JSON response
        """
        new_sound = Sound.objects.create(uuid='41f94400-2a3e-408a-9b80-1774724f62af', duration=123, created_on='2016-08-17 20:49:53.123456+08:00')
        response = self.client.get(reverse('sounds:random_json'))
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertDictEqual(json_data, {'uuid': new_sound.uuid, 'duration': new_sound.duration})

    def test_random_view_min_duration(self):
        """
        Random view must 404 when no sounds are present or a random sound with the minimum specified duration
        """
        new_sound = Sound.objects.create(uuid='a7488bf2-fef3-4846-a898-fc60dea73dbb', duration=10, created_on='2016-08-17 20:49:53.123456+08:00')

        response = self.client.get(reverse('sounds:random_json'), {'min_duration': 11})
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse('sounds:random_json'), {'min_duration': 10})
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertDictEqual(json_data, {'uuid': new_sound.uuid, 'duration': new_sound.duration})

    def test_random_view_max_duration(self):
        """
        Random view must 404 when no sounds are present or a random sound with the maximum specified duration
        """
        new_sound = Sound.objects.create(uuid='a7488bf2-fef3-4846-a898-fc60dea73dbb', duration=10, created_on='2016-08-17 20:49:53.123456+08:00')

        response = self.client.get(reverse('sounds:random_json'), {'max_duration': 9})
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse('sounds:random_json'), {'max_duration': 10})
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertDictEqual(json_data, {'uuid': new_sound.uuid, 'duration': new_sound.duration})

    def test_random_view_min_max_duration(self):
        """
        Random view must 404 when no sounds are present in the specified range or return a random sound in the specified range
        """
        new_sound = Sound.objects.create(uuid='a7488bf2-fef3-4846-a898-fc60dea73dbb', duration=10, created_on='2016-08-17 20:49:53.123456+08:00')

        response = self.client.get(reverse('sounds:random_json'), {'min_duration': 11, 'max_duration': 12})
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse('sounds:random_json'), {'min_duration': 8, 'max_duration': 9})
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse('sounds:random_json'), {'min_duration': 10, 'max_duration': 10})
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertDictEqual(json_data, {'uuid': new_sound.uuid, 'duration': new_sound.duration})

        response = self.client.get(reverse('sounds:random_json'), {'min_duration': 9, 'max_duration': 11})
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertDictEqual(json_data, {'uuid': new_sound.uuid, 'duration': new_sound.duration})

    def test_random_view_bad_duration(self):
        """
        Random view must 404 on invalid input
        """
        bad_post_data = [
            {},
            {'min_duration': None, 'max_duration': None},
            {'min_duration': None},
            {'max_duration': None},
            {'min_duration': 'foobar', 'max_duration': 'baz'},
            {'min_duration': 'foobar'},
            {'max_duration': 'baz'}
        ]

        for post_data in bad_post_data:
            response = self.client.get(reverse('sounds:random_json'), post_data)
            self.assertEqual(response.status_code, 404)


class ImportViewTests(TestCase):

    def test_import_normal(self):
        """
        Normal importing of sounds (and duplicate sounds) must succeed. Duplicate sounds must be ignored.
        """
        post_data = {
            'sounds': [
                {'uuid': '41f94400-2a3e-408a-9b80-1774724f62af', 'duration': 123, 'created_on': '2016-08-17 20:49:53.123456+08:00'},
                {'uuid': 'a7488bf2-fef3-4846-a898-fc60dea73dbb', 'duration': 234, 'created_on': '2016-08-17 20:49:53.234567+08:00'},
                {'uuid': '73671ba8-71a4-463a-a836-eb79ecf50386', 'duration': 345, 'created_on': '2016-08-17 20:49:53.345678+08:00'},
                {'uuid': '73671ba8-71a4-463a-a836-eb79ecf50386', 'duration': 345, 'created_on': '2016-08-17 20:49:53.345678+08:00'},
            ]
        }
        num_duplicates = 1
        num_expected = len(post_data['sounds']) - num_duplicates

        response = self.client.post(reverse('sounds:import_json'), json.dumps(post_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Sound.objects.count(), num_expected)

        json_response = response.json()
        self.assertDictEqual(json_response, {'num_imported': num_expected})

        for sound in post_data['sounds']:
            found_sound = Sound.objects.filter(uuid=sound['uuid']).filter(duration=sound['duration']).filter(created_on=sound['created_on']).count()
            self.assertEqual(found_sound, 1)

    def test_import_empty(self):
        """
        Importing an empty list of sounds must succeed and not add any sounds.
        """
        post_data = {
            'sounds': []
        }
        num_expected = len(post_data['sounds'])

        response = self.client.post(reverse('sounds:import_json'), json.dumps(post_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Sound.objects.count(), num_expected)

    def test_import_invalid(self):
        """
        Importing invalid sounds must 404 and not add any sounds.
        """
        bad_post_data = [
            {},
            {'sounds': 'bananas'},
            {'sounds': [
                {},
                {'uuid': '41f94400-2a3e-408a-9b80-1774724f62af', 'duration': 123},
                {'uuid': '41f94400-2a3e-408a-9b80-1774724f62af', 'created_on': '2016-08-17 20:49:53.123456+08:00'},
                {'duration': 123, 'created_on': '2016-08-17 20:49:53.123456+08:00'},
            ]},
        ]

        for post_data in bad_post_data:
            response = self.client.post(reverse('sounds:import_json'), json.dumps(post_data), content_type="application/json")
            self.assertEqual(response.status_code, 404)
            self.assertEqual(Sound.objects.count(), 0)
