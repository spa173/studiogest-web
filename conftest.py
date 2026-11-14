"""Collect app tests using the same import names as Django's app registry."""

import importlib
from pathlib import Path

import pytest
from django.apps import apps


class DjangoAppModule(pytest.Module):
    def _getobj(self):
        return importlib.import_module(self.django_module_name)


def pytest_pycollect_makemodule(module_path, parent):
    # apps/ is a Python package, but INSTALLED_APPS uses names like services.
    # Importing the tests as apps.services.tests would load models twice.
    for app in apps.get_app_configs():
        app_path = Path(app.path)
        if module_path.is_relative_to(app_path):
            relative = module_path.relative_to(app_path).with_suffix('')
            module = DjangoAppModule.from_parent(parent, path=module_path)
            module.django_module_name = '.'.join((app.name, *relative.parts))
            return module
    return None
