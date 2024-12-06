Setup configuration
===================

Loading JWTSecrets from a YAML file
***************************************************

This library provides a ``ConfigurationStep``
(from the library ``django-setup-configuration``, see the
`documentation <https://github.com/maykinmedia/django-setup-configuration>`_
for more information on how to run ``setup_configuration``)
to configure the client credentials.

To add this step to your configuration steps, add ``django_setup_configuration`` to ``INSTALLED_APPS`` and add the following setting:

    .. code:: python

        SETUP_CONFIGURATION_STEPS = [
            ...
            "vng_api_common.contrib.setup_configuration.steps.JWTSecretsConfigurationStep"
            ...
        ]

The YAML file that is passed to ``setup_configuration`` must set the
``vng_api_common_credentials_config_enable`` flag to ``true`` to enable the step. Any number of ``identifier`` and
``secret`` pairs can be defined under ``vng_api_common_credentials.items``

Example file:

    .. code:: yaml

        vng_api_common_credentials_config_enable: True
        vng_api_common_credentials:
          items:
          - identifier: user-id
            secret: super-secret
          - identifier: user-id2
            secret: super-secret2
