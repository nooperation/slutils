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
        valid_regions = [
            {'name': 'First Region', 'shard': self.first_shard},
            {'name': 'First Region', 'shard': self.second_shard},
            {'name': 'Second Region', 'shard': self.first_shard},
        ]

        regions = []
        for region in valid_regions:
            regions.append(Region.objects.create(name=region['name'], shard=region['shard']))

        for region in valid_regions:
            with self.assertRaises(IntegrityError):
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
        Normal creation of agents. Agents must be unique based off of uuid AND shard.
        """
        valid_agents = [
            {'name': 'First Agent', 'uuid': '41f94400-2a3e-408a-9b80-1774724f62af', 'shard': self.first_shard},
            {'name': 'First Agent', 'uuid': '41f94400-2a3e-408a-9b80-1774724f62af', 'shard': self.second_shard},
            {'name': 'Second Agent', 'uuid': 'a7488bf2-fef3-4846-a898-fc60dea73dbb', 'shard': self.first_shard},
        ]

        agents = []
        for agent in valid_agents:
            agent = Agent.objects.create(name=agent['name'], uuid=agent['uuid'], shard=agent['shard'])
            agent.full_clean()
            agents.append(agent)

        self.assertSequenceEqual(Agent.objects.all(), agents)

    def test_duplicates(self):
        valid_agents = [
            {'name': 'First Agent', 'uuid': '41f94400-2a3e-408a-9b80-1774724f62af', 'shard': self.first_shard},
            {'name': 'First Agent', 'uuid': '41f94400-2a3e-408a-9b80-1774724f62af', 'shard': self.second_shard},
            {'name': 'Second Agent', 'uuid': 'a7488bf2-fef3-4846-a898-fc60dea73dbb', 'shard': self.first_shard},
        ]

        agents = []
        for agent in valid_agents:
            agent = Agent.objects.create(name=agent['name'], uuid=agent['uuid'], shard=agent['shard'])
            agents.append(agent)

        for agent in valid_agents:
            with self.assertRaises(IntegrityError):
                Agent.objects.create(name=agent['name'], uuid=agent['uuid'], shard=agent['shard'])

        self.assertSequenceEqual(Agent.objects.all(), agents)

    def test_invalid(self):
        invalid_agents = [
            {'name': 'First Agent', 'uuid': '41f94400-2a3e-408a-9b80-1774724f62af', 'shard': None},

            {'name': 'First Agent', 'uuid': 'Bad UUID', 'shard': self.first_shard},
            {'name': 'First Agent', 'uuid': None, 'shard': self.first_shard},

            {'name': 'x'*256, 'uuid': '41f94400-2a3e-408a-9b80-1774724f62af', 'shard': self.first_shard},
            {'name': None, 'uuid': '41f94400-2a3e-408a-9b80-1774724f62af', 'shard': self.first_shard},
        ]

        for agent in invalid_agents:
            with self.assertRaises(ValidationError):
                Agent(name=agent['name'], uuid=agent['uuid'], shard=agent['shard']).full_clean()


class ServerTests(TransactionTestCase):
    def setUp(self):
        self.server_type = ServerType.objects.create(name='Test Server')
        self.first_shard = Shard.objects.create(name='Shard A')
        self.first_region = Region.objects.create(name='Region A', shard=self.first_shard)
        self.first_agent = Agent.objects.create(name='First Agent', uuid='41f94400-2a3e-408a-9b80-1774724f62af', shard=self.first_shard)

    def test_normal_creation(self):
        valid_servers = [
            {
                'uuid': '12345678-2a3e-408a-9b80-1234567890ab',
                'type': self.server_type,
                'shard': self.first_shard,
                'region': self.first_region,
                'owner': self.first_agent,
                'name': 'Server A',
                'auth_token': '11111111111111111111111111111111',
                'public_token': '10101010101010101010101010101010',
                'address': 'http://localhost/asdf',
                'position_x': 1.23,
                'position_y': 2.34,
                'position_z': 3.45,
                'enabled': True
            },
            {
                'uuid': '00000000-0000-0000-0000-000000000001',
                'type': self.server_type,
                'shard': self.first_shard,
                'region': self.first_region,
                'owner': self.first_agent,
                'name': 'Server B',
                'auth_token': '22222222222222222222222222222222',
                'public_token': '20202020202020202020202020202020',
                'address': 'http://localhost/foo/bar/baz',
                'position_x': 4.44,
                'position_y': 5.55,
                'position_z': 6.66,
                'enabled': False
            },
        ]

        servers = []
        for valid_server in valid_servers:
            server = Server.objects.create(
                uuid=valid_server['uuid'],
                type=valid_server['type'],
                shard=valid_server['shard'],
                region=valid_server['region'],
                owner=valid_server['owner'],
                name=valid_server['name'],
                address=valid_server['address'],
                auth_token=valid_server['auth_token'],
                public_token=valid_server['public_token'],
                position_x=valid_server['position_x'],
                position_y=valid_server['position_y'],
                position_z=valid_server['position_z'],
                enabled=valid_server['enabled']
            )
            server.full_clean()
            servers.append(server)

        self.assertSequenceEqual(Server.objects.all(), servers)


class RegisterViewTests(TransactionTestCase):
    def setUp(self):
        self.server_data = {
            'shard': 'Test Shard',
            'owner_key': '41f94400-2a3e-408a-9b80-1774724f62af',
            'owner_name': 'example resident',
            'object_key': '00000000-0000-0000-0000-000000000001',
            'object_name': 'Object name goes here',
            'region': 'Test_region',
            'address': 'http://google.com/foo/bar',
            'x': 1.2345,
            'y': 2.3456,
            'z': 3.4567
        }

    def test_new_server(self):
        response = self.client.post(reverse('server:register'), self.server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue('Success' in response.json())
        self.assertEquals(Server.objects.count(), 1)

        first_server = Server.objects.first()
        self.assertEquals(first_server.shard.name, self.server_data['shard'])
        self.assertEquals(first_server.owner.uuid, self.server_data['owner_key'])
        self.assertEquals(first_server.owner.name, self.server_data['owner_name'])
        self.assertEquals(first_server.region.name, self.server_data['region'])
        self.assertEquals(first_server.uuid, self.server_data['object_key'])
        self.assertEquals(first_server.name, self.server_data['object_name'])
        self.assertEquals(first_server.address, self.server_data['address'])
        self.assertEquals(first_server.position_x, self.server_data['x'])
        self.assertEquals(first_server.position_y, self.server_data['y'])
        self.assertEquals(first_server.position_z, self.server_data['z'])

    def test_existing_server(self):
        new_server_response = self.client.post(reverse('server:register'), self.server_data)
        self.assertEquals(new_server_response.status_code, 200)
        self.assertTrue('Success' in new_server_response.json())

        existing_server_response = self.client.post(reverse('server:register'), self.server_data)
        self.assertEquals(existing_server_response.status_code, 200)
        self.assertTrue('Error' in existing_server_response.json())

        self.assertEquals(Server.objects.count(), 1)

    def test_missing_param(self):
        for key in self.server_data:
            partial_server_data= self.server_data.copy()
            del partial_server_data[key]
            response = self.client.post(reverse('server:register'), partial_server_data)
            self.assertTrue('Error' in response.json())

        self.assertEquals(Server.objects.count(), 0)

class UpdateViewTests(TransactionTestCase):
    def setUp(self):
        server_type = ServerType.objects.create(name='Test Server')
        first_shard = Shard.objects.create(name='Shard A')
        first_region = Region.objects.create(name='Region A', shard=first_shard)
        first_agent = Agent.objects.create(name='First Agent', uuid='41f94400-2a3e-408a-9b80-1774724f62af', shard=first_shard)
        self.server_data = {
            'uuid': '00000000-0000-0000-0000-000000000001',
            'type': server_type,
            'shard': first_shard,
            'region': first_region,
            'owner': first_agent,
            'name': 'Server B',
            'auth_token': '11111111111111111111111111111111',
            'public_token': '10101010101010101010101010101010',
            'address': 'http://localhost/foo/bar/baz',
            'position_x': 4.44,
            'position_y': 5.55,
            'position_z': 6.66,
            'enabled': False
        }
        self.test_server = Server.objects.create(
            uuid=self.server_data['uuid'],
            type=self.server_data['type'],
            shard=self.server_data['shard'],
            region=self.server_data['region'],
            owner=self.server_data['owner'],
            name=self.server_data['name'],
            address=self.server_data['address'],
            auth_token=self.server_data['auth_token'],
            public_token=self.server_data['public_token'],
            position_x=self.server_data['position_x'],
            position_y=self.server_data['position_y'],
            position_z=self.server_data['position_z'],
            enabled=self.server_data['enabled']
        )

    def test_normal_update(self):
        new_address = 'http://example.com'
        response = self.client.post(reverse('server:update'), {'auth_token': self.test_server.auth_token, 'address': new_address})
        self.assertEquals(response.status_code, 200)
        self.assertTrue('Success' in response.json())
        self.assertEquals(Server.objects.count(), 1)

        first_server = Server.objects.first()
        self.assertEquals(first_server.address, new_address)

    def test_invalid_auth_token_update(self):
        invalid_auth_tokens = [
            self.test_server.public_token,
            '00000000000000000000000000000000',
            '',
            None
        ]

        new_address = 'http://example.com'

        for invalid_auth_token in invalid_auth_tokens:
            response = self.client.post(reverse('server:update'), {'auth_token': invalid_auth_token, 'address': new_address})
            self.assertTrue('Error' in response.json())
            first_server = Server.objects.first()
            self.assertEquals(first_server.address, self.server_data['address'])
