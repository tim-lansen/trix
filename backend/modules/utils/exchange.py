import base64
import pickle


class Exchange:
    @staticmethod
    def object_encode(obj):
        r = base64.b64encode(pickle.dumps(obj))
        return r

    @staticmethod
    def object_decode(obj):
        if obj:
            obj = pickle.loads(base64.b64decode(obj))
        return obj
