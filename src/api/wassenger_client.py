import httpx
import os
import asyncio
from src.utils import app_logger
from src.storage import memory_store

class WassengerClient:
    def __init__(self, api_key=None, base_url=None):
        self.api_key = api_key or os.getenv('API_KEY')
        self.base_url = base_url or os.getenv('API_URL', 'https://api.wassenger.com/v1')
        self.headers = {
            'Authorization': self.api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    async def send_message(self, data):
        retries = 3
        while retries > 0:
            retries -= 1
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(f'{self.base_url}/messages', json={**data, 'enqueue': 'never'}, headers=self.headers)
                    resp.raise_for_status()
                    result = resp.json()
                    app_logger.debug(f'Message sent successfully: {result}')
                    return result
            except Exception as e:
                app_logger.error(f'Failed to send message: {e}, retries left: {retries}')
                if retries == 0:
                    raise
                await asyncio.sleep(1)
        return None

    async def load_device(self, device_id=None):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f'{self.base_url}/devices', headers=self.headers)
                resp.raise_for_status()
                devices = resp.json()
            if device_id and ' ' not in device_id:
                for device in devices:
                    if device['id'] == device_id and device['status'] == 'operative':
                        return device
            for device in devices:
                if device['status'] == 'operative':
                    return device
            return None
        except Exception as e:
            app_logger.error(f'Failed to load device: {e}')
            raise

    async def pull_members(self, device):
        cache_key = f"members_{device['id']}"
        cached = memory_store.get(cache_key)
        if cached is not None:
            return cached
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.base_url}/devices/{device['id']}/team", headers=self.headers)
                resp.raise_for_status()
                members = resp.json()
            memory_store.set(cache_key, members)
            return members
        except Exception as e:
            app_logger.error(f'Failed to pull members: {e}')
            raise

    async def pull_labels(self, device, force=False):
        cache_key = f"labels_{device['id']}"
        if not force:
            cached = memory_store.get(cache_key)
            if cached is not None:
                return cached
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.base_url}/devices/{device['id']}/labels", headers=self.headers)
                resp.raise_for_status()
                labels = resp.json()
            memory_store.set(cache_key, labels)
            return labels
        except Exception as e:
            app_logger.error(f'Failed to pull labels: {e}')
            raise

    async def create_labels(self, device, required_labels):
        existing_labels = await self.pull_labels(device)
        existing_label_names = [label['name'] for label in existing_labels]
        missing_labels = list(set(required_labels) - set(existing_label_names))
        for label_name in missing_labels:
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(f"{self.base_url}/devices/{device['id']}/labels", json={'name': label_name}, headers=self.headers)
                app_logger.info(f'Created label: {label_name}')
            except Exception as e:
                app_logger.error(f'Failed to create label {label_name}: {e}')
        if missing_labels:
            memory_store.delete(f"labels_{device['id']}")

    async def update_chat_labels(self, data, device, labels):
        chat_id = data['chat']['id']
        existing_labels = data['chat'].get('labels', [])
        new_labels = list(set(existing_labels + labels))
        if len(new_labels) > len(existing_labels):
            try:
                async with httpx.AsyncClient() as client:
                    await client.patch(f"{self.base_url}/chat/{device['id']}/chats/{chat_id}/labels", json={'labels': new_labels}, headers=self.headers)
                app_logger.debug(f'Updated chat labels: {chat_id} -> {new_labels}')
            except Exception as e:
                app_logger.error(f'Failed to update chat labels: {e}')

    async def update_chat_metadata(self, data, device, metadata):
        chat_id = data['chat']['id']
        try:
            async with httpx.AsyncClient() as client:
                await client.patch(f"{self.base_url}/chat/{device['id']}/contacts/{chat_id}/metadata", json={'metadata': metadata}, headers=self.headers)
            app_logger.debug(f'Updated chat metadata: {chat_id} -> {metadata}')
        except Exception as e:
            app_logger.error(f'Failed to update chat metadata: {e}')

    async def assign_chat_to_agent(self, data, device, agent_id):
        chat_id = data['chat']['id']
        try:
            async with httpx.AsyncClient() as client:
                await client.patch(f"{self.base_url}/chat/{device['id']}/chats/{chat_id}/owner", json={'agent': agent_id}, headers=self.headers)
            app_logger.info(f'Assigned chat {chat_id} to agent {agent_id}')
        except Exception as e:
            app_logger.error(f'Failed to assign chat to agent: {e}')
            raise

    async def register_webhook(self, webhook_url, device):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f'{self.base_url}/webhooks', headers=self.headers)
                resp.raise_for_status()
                webhooks = resp.json()
            # Check if webhook already exists
            for webhook in webhooks:
                if webhook['url'] == webhook_url and webhook['device'] == device['id']:
                    app_logger.info(f'Webhook already exists: {webhook_url}')
                    return webhook
            # Delete old webhooks for this device
            for webhook in webhooks:
                if webhook['device'] == device['id']:
                    try:
                        async with httpx.AsyncClient() as client:
                            await client.delete(f"{self.base_url}/webhooks/{webhook['id']}", headers=self.headers)
                        app_logger.info(f'Deleted old webhook: {webhook["url"]}')
                    except Exception as e:
                        app_logger.warning(f'Failed to delete old webhook: {e}')
            await asyncio.sleep(1)
            async with httpx.AsyncClient() as client:
                resp = await client.post(f'{self.base_url}/webhooks', json={
                    'url': webhook_url,
                    'name': 'Chatbot',
                    'events': ['message:in:new'],
                    'device': device['id'],
                }, headers=self.headers)
                resp.raise_for_status()
                webhook = resp.json()
            app_logger.info(f'Webhook registered successfully: {webhook_url}')
            return webhook
        except Exception as e:
            app_logger.error(f'Failed to register webhook: {e}')
            raise

    async def send_typing_state(self, data, device, action='typing'):
        try:
            async with httpx.AsyncClient() as client:
                await client.post(f"{self.base_url}/chat/{device['id']}/typing", json={
                    'action': action,
                    'duration': 10,
                    'chat': data['fromNumber'],
                }, headers=self.headers)
        except Exception as e:
            app_logger.debug(f'Failed to send typing state: {e}')

    async def download_media(self, media_id):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.base_url}/media/{media_id}", headers=self.headers)
                resp.raise_for_status()
                return resp.content
        except Exception as e:
            app_logger.error(f'Failed to download media {media_id}: {e}')
            return None

    # Add more methods as needed for labels, members, etc. 