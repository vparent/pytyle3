import abc

import pt3.state as state


class Layouts(object, metaclass=abc.ABCMeta):

    """Base class for layouts """

    @abc.abstractmethod
    def __init__(self):
        self.desk = desk  # Should never change
        self.active = False
        self.tiling = False

    @abc.abstractmethod
    def add(self, c): pass

    @abc.abstractmethod
    def remove(self, c): pass

    @abc.abstractmethod
    def tile(self, save=True):
        if not self.active or self.desk not in state.visibles:
            return False

        if not self.tiling and save:
            for c in self.clients():
                c.save()
                # c.unmaximize()

        for c in self.clients():  # unmaximize all windows while tiling
            c.unmaximize()
        self.tiling = True

        return True

    @abc.abstractmethod
    def untile(self): pass

    @abc.abstractmethod
    def next_client(self): pass

    @abc.abstractmethod
    def switch_next_client(self): pass

    @abc.abstractmethod
    def prev_client(self): pass

    @abc.abstractmethod
    def switch_prev_client(self): pass

    @abc.abstractmethod
    def clients(self): pass

    def get_workarea(self):
        if self.desk not in state.visibles:
            return None

        mon = state.workarea[state.visibles.index(self.desk)]

        return mon

    def __str__(self):
        wa = self.get_workarea()
        if wa is None:
            wastr = 'wich isn\'t visible'
        else:
            wx, wy, ww, wh = wa
            wastr = f'{ww}x{wh}+{wx}+{wy}'

        istiling = '- TILING' if self.tiling else ''

        return f'{self.__class__.__name__} (desk {self.desk},' \
            f' {wastr}{istiling}'
