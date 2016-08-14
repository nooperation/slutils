from django.test import TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from .models import Sound
    
# Create your tests here.
class SoundTests(TestCase):
    def create_sound(self, uuid, duration):
        Sound.objects.create(uuid=uuid, duration=duration)

    def test_normal_creation(self):
        Sound.objects.create(uuid='01234567-89ab-cdef-0123-456789abcdef', duration=1234)

    def test_duplicate_sounds(self):
        duplicate_uuid = '01234567-89ab-cdef-0123-456789abcdef'
        
        Sound.objects.create(uuid=duplicate_uuid, duration=1234)
        with self.assertRaises(IntegrityError):
            Sound.objects.create(uuid=duplicate_uuid, duration=1234)
            
    def test_missing_uuid(self):
        with self.assertRaises(ValidationError):
            Sound(duration=1234).full_clean()

    def test_bad_uuid(self):
        with self.assertRaises(ValidationError):
            Sound(duration=1234, uuid='01234567-ZZZZ-ZZZZ-0123-456789abcdeZ').full_clean()
