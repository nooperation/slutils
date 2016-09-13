from django.test import TransactionTestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from .models import *
import json
import gzip

# Create your tests here.

class ServerTypeTests(TransactionTestCase):
    def test_normal_creation(self):
        """
        Normal creation of server types
        """
        valid_names = [
            'Test',
            'Another Test'
        ]
        server_types = []
        for name in valid_names:
            server_type = ServerType.objects.create(name=name)
            server_type.full_clean()
            server_types.append(server_type)
        self.assertSequenceEqual(ServerType.objects.all(), server_types)

    def test_duplicate_creation(self):
        """
        Creation of duplicate server types must fail.
        """
        server_type = ServerType.objects.create(name='Test')
        with self.assertRaises(IntegrityError):
            ServerType.objects.create(name='Test').full_clean()
        self.assertSequenceEqual(ServerType.objects.all(), [server_type])

    def test_invalid_creation(self):
        """
        Creation of invalid server types must fail.
        """
        invalid_names = [
            None,
            '',
            'x' * 65
        ]
        for invalid_name in invalid_names:
            with self.assertRaises(ValidationError):
                ServerType(name=invalid_name).full_clean()
        self.assertEqual(ServerType.objects.count(), 0)


class ShardTests(TransactionTestCase):
    def test_normal_creation(self):
        """
        Normal creation of shards
        """
        valid_names = [
            'Test',
            'Another Test'
        ]
        server_types = []
        for name in valid_names:
            server_type = Shard.objects.create(name=name)
            server_type.full_clean()
            server_types.append(server_type)
        self.assertSequenceEqual(Shard.objects.all(), server_types)

    def test_duplicate_creation(self):
        """
        Creation of duplicate shard must fail.
        """
        shard = Shard.objects.create(name='Test')
        with self.assertRaises(IntegrityError):
            Shard.objects.create(name='Test').full_clean()
        self.assertSequenceEqual(Shard.objects.all(), [shard])

    def test_invalid_creation(self):
        """
        Creation of invalid shard must fail.
        """
        invalid_names = [
            None,
            '',
            'x' * 256
        ]
        for invalid_name in invalid_names:
            with self.assertRaises(ValidationError):
                Shard(name=invalid_name).full_clean()
        self.assertEqual(Shard.objects.count(), 0)

class RegionTests(TransactionTestCase):
    def setUp(self):
        self.first_shard = Shard.objects.create(name='Shard A')
        self.second_shard = Shard.objects.create(name='Shard B')

    def test_normal_creation(self):
        """
        Normal creation of regions. Regions must be unique based off of shard AND region name. Multiple regions with differing shards may exist.
        """
        valid_regions = [
            {'name': 'First Region', 'shard': self.first_shard},
            {'name': 'First Region', 'shard': self.second_shard},
            {'name': 'Second Region', 'shard': self.first_shard},
        ]

        regions = []
        for region in valid_regions:
            region = Region.objects.create(name=region['name'], shard=region['shard'])
            region.full_clean()
            regions.append(region)

        self.assertSequenceEqual(Region.objects.all(), regions)

    def test_duplicate_creation(self):
        """
        Duplicate regions must not exist. Regions must be unique based off of shard AND region name.
        """
        Region.objects.create(name='First Region', shard=self.first_shard)
        Region.objects.create(name='First Region', shard=self.second_shard)
        Region.objects.create(name='Second Region', shard=self.first_shard)

        valid_regions = [
            {'name': 'First Region', 'shard': self.first_shard},
            {'name': 'First Region', 'shard': self.second_shard},
            {'name': 'Second Region', 'shard': self.first_shard},
        ]

        regions = []
        for region in valid_regions:
            regions.append(Region.objects.create(name=region['name'], shard=region['shard']))

        for region in valid_regions:
            with self.assertRaises(ValidationError):
                Region.objects.create(name=region['name'], shard=region['shard'])

        self.assertSequenceEqual(Region.objects.all(), regions)

    def test_invalid(self):
        """
        Regions must have a non-empty name and a valid shard.
        """
        invalid_regions = [
            {'name': None, 'shard': self.first_shard},
            {'name': None, 'shard': None},
        ]

        for invalid_region in invalid_regions:
            with self.assertRaises(IntegrityError):
                Region.objects.create(name=invalid_region['name'], shard=invalid_region['shard'])

        invalid_regions = [
            {'name': '', 'shard': self.first_shard},
            {'name': 'x'*256, 'shard': self.first_shard},
        ]

        for invalid_region in invalid_regions:
            with self.assertRaises(ValidationError):
                Region(name=invalid_region['name'], shard=invalid_region['shard']).full_clean()

        self.assertEqual(Region.objects.count(), 0)

class AgentTests(TransactionTestCase):
    def setUp(self):
        self.first_shard = Shard.objects.create(name='Shard A')
        self.second_shard = Shard.objects.create(name='Shard B')

    def test_normal_creation(self):
        """
        Normal creation of agents. Agents must be unique based off of name AND shard AND uuid.
        """
        valid_agents = [
            {'name': 'First Agent', 'uuid': '41f94400-2a3e-408a-9b80-1774724f62af', 'shard': self.first_shard, 'auth_token': None, 'auth_token_date': None},
            {'name': 'First Agent', 'uuid': '41f94400-2a3e-408a-9b80-1774724f62af', 'shard': self.second_shard, 'auth_token': None, 'auth_token_date': None},
            {'name': 'Second Agent', 'uuid': 'a7488bf2-fef3-4846-a898-fc60dea73dbb', 'shard': self.first_shard, 'auth_token': None, 'auth_token_date': None},
        ]

        agents = []
        for agent in valid_agents:
            agent = Agent.objects.create(name=agent['name'], uuid=agent['uuid'], shard=agent['shard'])
            agent.full_clean()
            agent.append(region)

        self.assertSequenceEqual(Agent.objects.all(), agents)
