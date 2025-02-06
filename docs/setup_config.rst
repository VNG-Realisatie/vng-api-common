Setup configuration
===================

This library has an optional integration with ``django-setup-configuration``, see the
`documentation <https://django-setup-configuration.readthedocs.io/en/latest/>`_
for more information on how to run ``setup_configuration``.
To make use of this, you must install the ``setup-configuration`` dependency group:

.. code-block:: bash

    pip install commonground-api-common[setup-configuration]


Loading JWTSecrets from a YAML file
***********************************

This library provides a ``ConfigurationStep`` to configure the client credentials.

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

You can use the following example YAML and adapt it to your needs:

.. setup-config-example:: vng_api_common.contrib.setup_configuration.steps.JWTSecretsConfigurationStep


Loading Applicaties from a YAML file
************************************

This library also provides a ``ConfigurationStep`` to configure the applicaties.

To add this step to your configuration steps, add ``django_setup_configuration`` to ``INSTALLED_APPS`` and add the following setting:

    .. code:: python

        SETUP_CONFIGURATION_STEPS = [
            ...
            "vng_api_common.contrib.setup_configuration.steps.ApplicatieConfigurationStep"
            ...
        ]

The YAML file that is passed to ``setup_configuration`` must set the
``vng_api_common_applicaties_config_enable`` flag to ``true`` to enable the step.
Any number of ``Applicaties`` can be defined under ``vng_api_common_applicaties.items``

You can use the following example YAML and adapt it to your needs:

.. setup-config-example:: vng_api_common.contrib.setup_configuration.steps.ApplicatieConfigurationStep
