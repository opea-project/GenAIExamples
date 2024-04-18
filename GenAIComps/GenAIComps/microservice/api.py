from typing import Dict, List


def client(service_name: str):
    """Creates a client object for interfacing with an existing microservice.

    :return: Client object that can be used to interface with the deployed microservice.
    """


def serve(
    service_name: str = "",
    service_config: Dict = None,
    **kwargs,
):
    """Creates a microservice.

    :param service_name: microservice name.
    :param service_config: Dictionary containing microservice configuration fields.
    """


def pipeline(
    application_name: str = "",
    service_list: List[str] = None,
    **kwargs,
):
    """Creates a microservice pipeline to deploy a application.

    :param application_name: the application name.
    :param
    """
