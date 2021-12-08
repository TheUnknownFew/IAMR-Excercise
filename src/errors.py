class UniquenessError(Exception):
    def __init__(self, elems: list, message: str=''):
        super().__init__(f'Issue occurred when gathering a unique resource. Multiple instances hit'
                         f'\nelements: {elems}.'
                         f'\n{message}.')
