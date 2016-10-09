from django.test import TransactionTestCase, TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse

from .models import *
from .views import JSON_RESULT_ERROR
from .views import JSON_RESULT_SUCCESS
from .views import JSON_TAG_RESULT 
from .views import JSON_TAG_MESSAGE


def is_json_success(result_json):
    return JSON_TAG_RESULT in result_json and result_json[JSON_TAG_RESULT] == JSON_RESULT_SUCCESS


def is_json_error(result_json):
    return JSON_TAG_RESULT in result_json and result_json[JSON_TAG_RESULT] == JSON_RESULT_ERROR


def post_with_metadata(client, address, server, params):
    return client.post(address,
                       params,
                       HTTP_X_SECONDLIFE_LOCAL_POSITION='({x}, {y}, {z})'.format(x=server.position_x, y=server.position_y, z=server.position_z),
                       HTTP_X_SECONDLIFE_REGION='{region_name} (123, 456)'.format(region_name=server.region.name),
                       HTTP_X_SECONDLIFE_OWNER_NAME='Owner Name',
                       HTTP_X_SECONDLIFE_OBJECT_NAME=server.object_name,
                       HTTP_X_SECONDLIFE_OBJECT_KEY=server.object_key,
                       HTTP_X_SECONDLIFE_OWNER_KEY=server.owner.uuid,
                       HTTP_X_SECONDLIFE_SHARD=server.shard)


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
            {'name': 'region name', 'shard': None},
        ]

        for invalid_region in invalid_regions:
            with self.assertRaises(IntegrityError):
                Region.objects.create(name=invalid_region['name'], shard=invalid_region['shard'])

        invalid_regions = [
            {'name': '', 'shard': self.first_shard},
            {'name': 'x' * 256, 'shard': self.first_shard},
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

            {'name': 'x' * 256, 'uuid': '41f94400-2a3e-408a-9b80-1774724f62af', 'shard': self.first_shard},
            {'name': None, 'uuid': '41f94400-2a3e-408a-9b80-1774724f62af', 'shard': self.first_shard},
        ]

        for agent in invalid_agents:
            with self.assertRaises(ValidationError):
                Agent(name=agent['name'], uuid=agent['uuid'], shard=agent['shard']).full_clean()


class ServerTests(TestCase):
    def setUp(self):
        self.first_shard = Shard.objects.create(name='Shard A')
        self.first_region = Region.objects.create(name='Region A', shard=self.first_shard)
        self.first_agent = Agent.objects.create(name='First Agent', uuid='41f94400-2a3e-408a-9b80-1774724f62af', shard=self.first_shard)

    def test_normal_creation(self):
        valid_servers = [
            {
                'object_key': '12345678-2a3e-408a-9b80-1234567890ab',
                'type': Server.TYPE_UNREGISTERED,
                'shard': self.first_shard,
                'region': self.first_region,
                'owner': self.first_agent,
                'object_name': 'Server A',
                'private_token': '11111111111111111111111111111111',
                'public_token': '10101010101010101010101010101010',
                'address': 'https://dl.dropboxusercontent.com/u/50597639/server/loopback_1_ok?ignore',
                'position_x': 1.23,
                'position_y': 2.34,
                'position_z': 3.45,
                'enabled': True
            },
            {
                'object_key': '00000000-0000-0000-0000-000000000001',
                'type': Server.TYPE_UNREGISTERED,
                'shard': self.first_shard,
                'region': self.first_region,
                'owner': self.first_agent,
                'object_name': 'Server B',
                'private_token': '22222222222222222222222222222222',
                'public_token': '20202020202020202020202020202020',
                'address': 'https://dl.dropboxusercontent.com/u/50597639/server/loopback_2_ok?ignore',
                'position_x': 4.44,
                'position_y': 5.55,
                'position_z': 6.66,
                'enabled': False
            },
        ]

        servers = []
        for valid_server in valid_servers:
            server = Server.objects.create(
                object_key=valid_server['object_key'],
                object_name=valid_server['object_name'],
                type=valid_server['type'],
                shard=valid_server['shard'],
                region=valid_server['region'],
                owner=valid_server['owner'],
                address=valid_server['address'],
                private_token=valid_server['private_token'],
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
    def post_with_metadata(self, address, server):
        params = None
        position = None
        region = None
        owner_name = None
        object_name = None
        object_key = None
        owner_key = None
        shard = None

        if 'address' in server:
            params = {'address': server['address']}
        if 'position_x' in server and 'position_y' in server and 'position_z' in server:
            position = '({x}, {y}, {z})'.format(x=server['position_x'], y=server['position_y'], z=server['position_z'])
        if 'region' in server:
            region = '{region_name} (123, 456)'.format(region_name=server['region'])
        if 'owner_name' in server:
            owner_name = server['owner_name']
        if 'object_name' in server:
            object_name = server['object_name']
        if 'object_key' in server:
            object_key = server['object_key']
        if 'owner_key' in server:
            owner_key = server['owner_key']
        if 'shard' in server:
            shard = server['shard']

        return self.client.post(address,
                                params,
                                HTTP_X_SECONDLIFE_LOCAL_POSITION=position,
                                HTTP_X_SECONDLIFE_REGION=region,
                                HTTP_X_SECONDLIFE_OWNER_NAME=owner_name,
                                HTTP_X_SECONDLIFE_OBJECT_NAME=object_name,
                                HTTP_X_SECONDLIFE_OBJECT_KEY=object_key,
                                HTTP_X_SECONDLIFE_OWNER_KEY=owner_key,
                                HTTP_X_SECONDLIFE_SHARD=shard)

    def setUp(self):
        self.object_key = '00000000-0000-0000-0000-000000000001'
        self.server_data = {
            'shard': 'Test Shard',
            'owner_key': '41f94400-2a3e-408a-9b80-1774724f62af',
            'owner_name': 'example resident',
            'object_key': self.object_key,
            'object_name': 'Object name goes here',
            'region': 'Test_region',
            'address': 'https://dl.dropboxusercontent.com/u/50597639/server/loopback_1_ok?ignore',
            'position_x': 1.2345,
            'position_y': 2.3456,
            'position_z': 3.4567
        }

    def test_new_server(self):
        response = self.post_with_metadata(reverse('server:register'), self.server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_success(response.json()))
        self.assertEquals(Server.objects.count(), 1)

        first_server = Server.objects.first()
        self.assertEquals(first_server.shard.name, self.server_data['shard'])
        self.assertEquals(first_server.owner.uuid, self.server_data['owner_key'])
        self.assertEquals(first_server.owner.name, self.server_data['owner_name'])
        self.assertEquals(first_server.region.name, self.server_data['region'])
        self.assertEquals(first_server.object_key, self.server_data['object_key'])
        self.assertEquals(first_server.object_name, self.server_data['object_name'])
        self.assertEquals(first_server.address, self.server_data['address'])
        self.assertEquals(first_server.position_x, self.server_data['position_x'])
        self.assertEquals(first_server.position_y, self.server_data['position_y'])
        self.assertEquals(first_server.position_z, self.server_data['position_z'])
        self.assertEquals(first_server.type, Server.TYPE_UNREGISTERED)

    def test_existing_unregistered_server(self):
        # Create create our first server
        new_server_response = self.post_with_metadata(reverse('server:register'), self.server_data)
        self.assertEquals(new_server_response.status_code, 200)
        self.assertTrue(is_json_success(new_server_response.json()))

        # Re-register the same server (object_key), but with different data. This should simply update the existing server
        # if the existing server is still not claimed by anyone and generate new private and public tokens.
        new_server_data = {
            'shard': 'Test Shard 2',
            'owner_key': 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
            'owner_name': 'different resident',
            'object_key': self.object_key,
            'object_name': 'New object name',
            'region': 'New_region',
            'address': 'https://dl.dropboxusercontent.com/u/50597639/server/loopback_2_ok?ignore',
            'position_x': 2.3456,
            'position_y': 3.4567,
            'position_z': 4.5678
        }
        existing_server_response = self.post_with_metadata(reverse('server:register'), new_server_data)
        self.assertEquals(existing_server_response.status_code, 200)
        self.assertTrue(is_json_success(existing_server_response.json()))

        # Must not create any new servers
        self.assertEquals(Server.objects.count(), 1)

        # Existing server must be updated with new server data
        first_server = Server.objects.first()
        self.assertEquals(first_server.shard.name, new_server_data['shard'])
        self.assertEquals(first_server.owner.uuid, new_server_data['owner_key'])
        self.assertEquals(first_server.owner.name, new_server_data['owner_name'])
        self.assertEquals(first_server.region.name, new_server_data['region'])
        self.assertEquals(first_server.object_key, new_server_data['object_key'])
        self.assertEquals(first_server.object_name, new_server_data['object_name'])
        self.assertEquals(first_server.address, new_server_data['address'])
        self.assertEquals(first_server.position_x, new_server_data['position_x'])
        self.assertEquals(first_server.position_y, new_server_data['position_y'])
        self.assertEquals(first_server.position_z, new_server_data['position_z'])
        self.assertEquals(first_server.type, Server.TYPE_UNREGISTERED)

    def test_existing_registered_server(self):
        first_shard = Shard.objects.create(name='Shard A')
        first_region = Region.objects.create(name='Region A', shard=first_shard)
        first_agent = Agent.objects.create(name='First Agent', uuid='41f94400-2a3e-408a-9b80-1774724f62af', shard=first_shard)
        existing_server = Server.objects.create(
            object_key=self.server_data['object_key'],
            object_name='Server A',
            type=Server.TYPE_DEFAULT,
            shard=first_shard,
            region=first_region,
            owner=first_agent,
            private_token='11111111111111111111111111111111',
            public_token='10101010101010101010101010101010',
            address='https://dl.dropboxusercontent.com/u/50597639/server/loopback_2_ok?ignore',
            position_x=1.23,
            position_y=2.34,
            position_z=3.45,
            enabled=True)

        response = self.post_with_metadata(reverse('server:register'), self.server_data)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_error(response.json()))
        self.assertEquals(Server.objects.count(), 1)

    def test_missing_param(self):
        for key in self.server_data:
            partial_server_data = self.server_data.copy()
            del partial_server_data[key]
            response = self.post_with_metadata(reverse('server:register'), partial_server_data)
            self.assertTrue(is_json_error(response.json()))

        self.assertEquals(Server.objects.count(), 0)


class UpdateViewTests(TestCase):
    def setUp(self):
        first_shard = Shard.objects.create(name='Shard A')
        first_region = Region.objects.create(name='Region A', shard=first_shard)
        first_agent = Agent.objects.create(name='First Agent', uuid='41f94400-2a3e-408a-9b80-1774724f62af', shard=first_shard)
        self.server_data = {
            'object_key': '00000000-0000-0000-0000-000000000001',
            'object_name': 'Server B',
            'type': Server.TYPE_DEFAULT,
            'shard': first_shard,
            'region': first_region,
            'owner': first_agent,
            'private_token': '11111111111111111111111111111111',
            'public_token': '10101010101010101010101010101010',
            'address': 'https://dl.dropboxusercontent.com/u/50597639/server/loopback_1_ok?ignore',
            'position_x': 4.44,
            'position_y': 5.55,
            'position_z': 6.66,
            'enabled': False
        }
        self.test_server = Server.objects.create(
            object_key=self.server_data['object_key'],
            object_name=self.server_data['object_name'],
            type=self.server_data['type'],
            shard=self.server_data['shard'],
            region=self.server_data['region'],
            owner=self.server_data['owner'],
            address=self.server_data['address'],
            private_token=self.server_data['private_token'],
            public_token=self.server_data['public_token'],
            position_x=self.server_data['position_x'],
            position_y=self.server_data['position_y'],
            position_z=self.server_data['position_z'],
            enabled=self.server_data['enabled']
        )

    def test_normal_update(self):
        new_address = 'https://dl.dropboxusercontent.com/u/50597639/server/loopback_1_ok?ignore'
        response = post_with_metadata(self.client, reverse('server:update'), self.test_server, {'private_token': self.test_server.private_token, 'address': new_address})

        self.assertEquals(response.status_code, 200)
        self.assertTrue(is_json_success(response.json()))
        self.assertEquals(Server.objects.count(), 1)

        first_server = Server.objects.first()
        self.assertEquals(first_server.address, new_address)

    def test_invalid_private_token_update(self):
        invalid_private_tokens = [
            self.test_server.public_token,
            '00000000000000000000000000000000',
            '',
            None
        ]

        new_address = 'https://dl.dropboxusercontent.com/u/50597639/server/loopback_2_ok?ignore'

        for invalid_private_token in invalid_private_tokens:
            response = post_with_metadata(self.client, reverse('server:update'), self.test_server, {'private_token': invalid_private_token, 'address': new_address})
            self.assertTrue(is_json_error(response.json()))
            first_server = Server.objects.first()
            self.assertEquals(first_server.address, self.server_data['address'])


class ConfirmServerView(TestCase):
    def setUp(self):
        self.username = 'test_user'
        self.password = 'asdf'
        self.user = User.objects.create_user(username=self.username, email='jdoe@example.com', password=self.password)
        self.private_token = '11111111111111111111111111111111'
        first_shard = Shard.objects.create(name='Shard A')
        first_region = Region.objects.create(name='Region A', shard=first_shard)
        first_agent = Agent.objects.create(name='First Agent', uuid='41f94400-2a3e-408a-9b80-1774724f62af', shard=first_shard)
        self.test_server = Server.objects.create(
            object_key='00000000-0000-0000-0000-000000000001',
            object_name='Server B',
            type=Server.TYPE_UNREGISTERED,
            shard=first_shard,
            region=first_region,
            owner=first_agent,
            address='https://dl.dropboxusercontent.com/u/50597639/server/loopback_1_ok?ignore',
            private_token=self.private_token,
            public_token='10101010101010101010101010101010',
            position_x=4.44,
            position_y=5.55,
            position_z=6.66,
            enabled=False
        )

    def test_normal_confirmation_loggedin(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('server:confirm', kwargs={'private_token': self.private_token}))
        first_server = Server.objects.first()
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, JSON_RESULT_SUCCESS)
        self.assertEquals(first_server.user, self.user)
        self.assertEquals(first_server.type, Server.TYPE_DEFAULT)

    def test_normal_confirmation_not_loggedin(self):
        requested_url = reverse('server:confirm', kwargs={'private_token': self.private_token})
        response = self.client.get(requested_url)
        self.assertRedirects(response, reverse('login') + '?next=' + requested_url)


class SetEnabledView(TestCase):
    def setUp(self):
        self.username = 'test_user'
        self.password = 'asdf'
        self.user = User.objects.create_user(username=self.username, email='jdoe@example.com', password=self.password)
        self.private_token = '11111111111111111111111111111111'
        self.public_token = '10101010101010101010101010101010'
        first_shard = Shard.objects.create(name='Shard A')
        first_region = Region.objects.create(name='Region A', shard=first_shard)
        first_agent = Agent.objects.create(name='First Agent', uuid='41f94400-2a3e-408a-9b80-1774724f62af', shard=first_shard)
        self.test_server = Server.objects.create(
            object_key='00000000-0000-0000-0000-000000000001',
            object_name='Server B',
            type=Server.TYPE_DEFAULT,
            shard=first_shard,
            region=first_region,
            owner=first_agent,
            user=self.user,
            address='https://dl.dropboxusercontent.com/u/50597639/server/loopback_1_ok?ignore',
            private_token=self.private_token,
            public_token=self.public_token,
            position_x=4.44,
            position_y=5.55,
            position_z=6.66,
            enabled=False
        )

    def test_normal_usage(self):
        self.client.login(username=self.username, password=self.password)
        self.assertFalse(Server.objects.first().enabled)

        # We should be able to successfully enable the server we own.
        response = self.client.get(reverse('server:set_enabled', kwargs={'public_token': self.public_token, 'enabled': True}))
        self.assertTrue(is_json_success(response.json()))
        self.assertTrue(Server.objects.first().enabled)

        # We should be able to successfully disable the server we own.
        response = self.client.get(reverse('server:set_enabled', kwargs={'public_token': self.public_token, 'enabled': False}))
        self.assertTrue(is_json_success(response.json()))
        self.assertFalse(Server.objects.first().enabled)

    def test_invalid_server(self):
        username2 = 'foobar'
        password2 = 'a'
        self.user2 = User.objects.create_user(username=username2, email='example@example.com', password=password2)
        self.client.login(username=username2, password=password2)
        self.assertFalse(Server.objects.first().enabled)

        # Attempting to change a server we don't own should result in error and have no effect on the server.
        response = self.client.get(reverse('server:set_enabled', kwargs={'public_token': self.public_token, 'enabled': True}))
        self.assertTrue(is_json_error(response.json()))
        self.assertFalse(Server.objects.first().enabled)

    def test_not_logged_in(self):
        # Attempting to modify a server when not logged in should result in a redirect to login.
        requested_url = reverse('server:set_enabled', kwargs={'public_token': self.public_token, 'enabled': True})
        response = self.client.get(requested_url)
        self.assertRedirects(response, reverse('login') + '?next=' + requested_url)


class RegenerateTokenViewTests(TestCase):
    def setUp(self):
        self.token_types = ['auth', 'public', 'both']
        self.username = 'test_user'
        self.password = 'asdf'
        self.user = User.objects.create_user(username=self.username, email='jdoe@example.com', password=self.password)
        self.private_token = '11111111111111111111111111111111'
        self.public_token = '10101010101010101010101010101010'
        first_shard = Shard.objects.create(name='Shard A')
        first_region = Region.objects.create(name='Region A', shard=first_shard)
        first_agent = Agent.objects.create(name='First Agent', uuid='41f94400-2a3e-408a-9b80-1774724f62af', shard=first_shard)
        self.test_server = Server.objects.create(
            object_key='00000000-0000-0000-0000-000000000001',
            object_name='Server B',
            type=Server.TYPE_DEFAULT,
            shard=first_shard,
            region=first_region,
            owner=first_agent,
            user=self.user,
            address='https://dl.dropboxusercontent.com/u/50597639/server/loopback_1_ok?ignore',
            private_token=self.private_token,
            public_token=self.public_token,
            position_x=4.44,
            position_y=5.55,
            position_z=6.66,
            enabled=False
        )

    def test_normal_usage(self):
        self.client.login(username=self.username, password=self.password)

        # Regenerate only the public token then restore the server to its original state.
        response = self.client.get(reverse('server:regenerate_tokens', kwargs={'public_token': self.public_token, 'token_type': 'public'}))
        self.assertTrue(is_json_success(response.json()))
        self.assertNotEqual(Server.objects.first().public_token, self.public_token)
        self.assertEqual(Server.objects.first().private_token, self.private_token)
        self.test_server.save()

        # Regenerate only the auth token then restore the server to its original state.
        response = self.client.get(reverse('server:regenerate_tokens', kwargs={'public_token': self.public_token, 'token_type': 'auth'}))
        self.assertTrue(is_json_success(response.json()))
        self.assertEqual(Server.objects.first().public_token, self.public_token)
        self.assertNotEqual(Server.objects.first().private_token, self.private_token)
        self.test_server.save()

        # Regenerate both tokens then restore the server to its original state.
        response = self.client.get(reverse('server:regenerate_tokens', kwargs={'public_token': self.public_token, 'token_type': 'both'}))
        self.assertTrue(is_json_success(response.json()))
        self.assertNotEqual(Server.objects.first().public_token, self.public_token)
        self.assertNotEqual(Server.objects.first().private_token, self.private_token)
        self.test_server.save()

    def test_invalid_server(self):
        username2 = 'foobar'
        password2 = 'a'
        self.user2 = User.objects.create_user(username=username2, email='example@example.com', password=password2)
        self.client.login(username=username2, password=password2)

        # Attempting to change a server we don't own should result in error and have no effect on the server.
        for token_type in self.token_types:
            response = self.client.get(reverse('server:regenerate_tokens', kwargs={'public_token': self.public_token, 'token_type': token_type}))
            self.assertTrue(is_json_error(response.json()))

        # Tokens must not change.
        first_server = Server.objects.first()
        self.assertEquals(first_server.private_token, self.private_token)
        self.assertEquals(first_server.public_token, self.public_token)

    def test_not_logged_in(self):
        # Attempting to modify a server when not logged in should result in a redirect to login.
        for token_type in self.token_types:
            requested_url = reverse('server:regenerate_tokens', kwargs={'public_token': self.public_token, 'token_type': token_type})
            response = self.client.get(requested_url)
            self.assertRedirects(response, reverse('login') + '?next=' + requested_url)

        # Tokens must not change.
        first_server = Server.objects.first()
        self.assertEquals(first_server.private_token, self.private_token)
        self.assertEquals(first_server.public_token, self.public_token)

    def test_server_not_registered(self):
        self.client.login(username=self.username, password=self.password)

        unregistered_server = Server.objects.create(
            object_key='00000000-0000-0000-0000-000000000002',
            object_name='Unregistered server',
            type=Server.TYPE_UNREGISTERED,
            shard=self.test_server.shard,
            region=self.test_server.region,
            owner=self.test_server.owner,
            user=self.test_server.user,
            address='https://dl.dropboxusercontent.com/u/50597639/server/loopback_2_ok?ignore',
            private_token='ffffffffffffffffffffffffffffffff',
            public_token='eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',
            position_x=4.44,
            position_y=5.55,
            position_z=6.66,
            enabled=False
        )

        # Regenerate only the public token then restore the server to its original state.
        response = self.client.get(reverse('server:regenerate_tokens', kwargs={'public_token': unregistered_server.public_token, 'token_type': 'public'}))
        updated_server = Server.objects.filter(object_key=unregistered_server.object_key).first()
        self.assertTrue(is_json_error(response.json()))
        self.assertEqual(updated_server.public_token, unregistered_server.public_token)
        self.assertEqual(updated_server.private_token, unregistered_server.private_token)
        self.test_server.save()


class GetServerStatusViewTests(TestCase):
    def setUp(self):
        self.token_types = ['auth', 'public', 'both']
        self.username = 'test_user'
        self.password = 'asdf'
        self.user = User.objects.create_user(username=self.username, email='jdoe@example.com', password=self.password)
        self.private_token = '11111111111111111111111111111111'
        self.public_token = '10101010101010101010101010101010'
        first_shard = Shard.objects.create(name='Shard A')
        first_region = Region.objects.create(name='Region A', shard=first_shard)
        first_agent = Agent.objects.create(name='First Agent', uuid='41f94400-2a3e-408a-9b80-1774724f62af', shard=first_shard)
        self.test_server = Server.objects.create(
            object_key='00000000-0000-0000-0000-000000000001',
            object_name='Server B',
            type=Server.TYPE_DEFAULT,
            shard=first_shard,
            region=first_region,
            owner=first_agent,
            user=self.user,
            address='https://dl.dropboxusercontent.com/u/50597639/server/loopback_1_ok?ignore',
            private_token=self.private_token,
            public_token=self.public_token,
            position_x=4.44,
            position_y=5.55,
            position_z=6.66,
            enabled=False
        )
        self.private_token_offline = '22222222222222222222222222222222'
        self.public_token_offline = '20202020202020202020202020202020'
        self.test_server_offline = Server.objects.create(
            object_key='00000000-0000-0000-0000-000000000002',
            object_name='Server B',
            type=Server.TYPE_DEFAULT,
            shard=first_shard,
            region=first_region,
            owner=first_agent,
            user=self.user,
            address='https://dl.dropboxusercontent.com/u/50597639/server/loopback_1_offline?ignore',
            private_token=self.private_token_offline,
            public_token=self.public_token_offline,
            position_x=4.44,
            position_y=5.55,
            position_z=6.66,
            enabled=False
        )

    def test_server_online(self):
        response = self.client.get(reverse('server:status', kwargs={'public_token': self.public_token}))
        self.assertTrue(is_json_success(response.json()))

    def test_server_offline(self):
        response = self.client.get(reverse('server:status', kwargs={'public_token': self.public_token_offline}))
        self.assertTrue(is_json_error(response.json()))

    def test_invalid_server(self):
        invalid_public_tokens = [
            '30303030303030303030303030303030',
        ]
        for invalid_token in invalid_public_tokens:
            response = self.client.get(reverse('server:status', kwargs={'public_token': invalid_token}))
            self.assertTrue(is_json_error(response.json()))
