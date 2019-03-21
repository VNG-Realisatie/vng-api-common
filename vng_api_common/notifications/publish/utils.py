from urllib.parse import urlparse


def get_kenmerken_from_model (url, model, topics):
    # parse url to uuid
    uuid = urlparse(url).path.strip('/').split('/')[-1]
    # retrieve object from model based on uuid
    model_object = model.objects.get(uuid=uuid)
    return [{k: getattr(model_object, k)} for k in topics]
