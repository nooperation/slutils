from django.test import TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from .models import Sound


# Create your tests here.
class SoundTests(TestCase):
    VALID_UUID = '01234567-89ab-cdef-0123-456789abcdef'
    INVALID_UUID = '01234567-ZZZZ-ZZZZ-0123-456789abcdeZ'
    VALID_DURATION = 1234
    INVALID_DURATION = -1234

    def test_normal_creation(self):
        """
        Normal creation of a Sound
        """
        Sound.objects.create(uuid=self.VALID_UUID, duration=self.VALID_DURATION)

    def test_duplicate_sounds(self):
        """
        The UUID field must be unique
        """
        Sound.objects.create(uuid=self.VALID_UUID, duration=self.VALID_DURATION)
        with self.assertRaises(IntegrityError):
            Sound.objects.create(uuid=self.VALID_UUID, duration=self.VALID_DURATION)

    def test_missing_uuid(self):
        """
        The UUID field must exist
        """
        with self.assertRaises(ValidationError):
            Sound(duration=self.VALID_DURATION).full_clean()

    def test_bad_uuid(self):
        """
        The UUID field must be valid
        """
        with self.assertRaises(ValidationError):
            Sound(duration=self.VALID_DURATION, uuid=self.INVALID_UUID).full_clean()

    def test_missing_duration(self):
        """
        The duration must exist
        """
        with self.assertRaises(ValidationError):
            Sound(uuid=self.VALID_UUID).full_clean()
