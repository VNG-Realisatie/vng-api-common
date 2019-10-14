class Audit:
    def __init__(self, component_name: str, main_resource: str):
        self.component_name = component_name
        self.main_resource = main_resource

    def __repr__(self):
        cls_name = self.__class__.__name__
        return f"{cls_name}(component_name={self.component_name}, main_resource={self.main_resource})"
