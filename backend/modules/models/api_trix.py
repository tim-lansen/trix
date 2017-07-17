# -*- coding: utf-8 -*-


from typing import List
from modules.utils.types import Guid
from modules.utils.jsoner import JSONer
from .interaction import Interaction


class ApiTrix:

    # Trix API description

    class Request(JSONer):

        class Methods(JSONer):

            class Authorize(JSONer):

                def __init__(self):
                    super().__init__()
                    self.external_session_id: str = ''

            class Interaction(JSONer):

                class Methods(JSONer):

                    class GetLock(JSONer):
                        def __init__(self):
                            super().__init__()
                            self.guid = Guid()

                        def handler(self, data):
                            # Handle 'interaction.get' request
                            self.guid = data['guid']
                            # The requested interaction's status must not be 'LOCK'


                    class GetList(JSONer):
                        def __init__(self):
                            super().__init__()
                            self.count = 0
                            self.sort_by = None
                            # Filtering criteria, example: 'type == 1 && status == 1'
                            self.selection = None

                    class Submit(JSONer):
                        def __init__(self):
                            super().__init__()
                            # Interaction's ID
                            self.guid = Guid()
                            self.update = {}

                    def __init__(self):
                        super().__init__()
                        self.getLock = self.GetLock()
                        self.getList = self.GetList()
                        self.submit = self.Submit()

                def __init__(self):
                    super().__init__()
                    self.method = None

            def __init__(self):
                super().__init__()
                self.authorize = self.Authorize()
                self.interaction = self.Interaction()

        class Data(JSONer):
            def __init__(self):
                super().__init__()
                self.input = {}
                self.output = {}

        def __init__(self):
            super().__init__()
            self.guid = Guid(0)
            self.method = None
            self.sessionId = Guid()
            self.data = {}


