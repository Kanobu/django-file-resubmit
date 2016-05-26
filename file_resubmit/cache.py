# -*- coding: utf-8 -*-

import os

# Django 1.9 removes support for django.core.cache.get_cache
try:
    from django.core.cache import get_cache
except ImportError:
    from django.core.cache import caches
    get_cache = lambda cache_name: caches[cache_name]

from django.core.files.storage import default_storage as storage
from django.core.files.uploadedfile import InMemoryUploadedFile


class FileCache(object):
    def __init__(self):
        self.backend = self.get_backend()

    def get_backend(self):
        return get_cache('file_resubmit')

    def save_to_storage(self, key, upload):
        return storage.save(os.path.join('file_resubmit', key), upload.file)

    def get_from_storage(self, name):
        if storage.exists(name):
            return storage.open(name, 'rb')

    def delete_from_storage(self, name):
        if storage.exists(name):
            return storage.delete(name)

    def set(self, key, upload):
        storage_name = self.save_to_storage(key, upload)
        state = {
            "name": upload.name,
            "size": upload.size,
            "content_type": upload.content_type,
            "charset": upload.charset,
            "storage_name": storage_name,
        }
        upload.file.seek(0)
        self.backend.set(key, state)

    def get(self, key, field_name):
        upload = None
        state = self.backend.get(key)
        if state:
            f = self.get_from_storage(state["storage_name"])
            if not f:
                return upload
            upload = InMemoryUploadedFile(
                file=f,
                field_name=field_name,
                name=state["name"],
                content_type=state["content_type"],
                size=state["size"],
                charset=state["charset"],
            )
            upload.file.seek(0)
        return upload

    def delete(self, key):
        state = self.backend.get(key)
        if state:
            self.delete_from_storage(state["storage_name"])
        self.backend.delete(key)
