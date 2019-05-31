import sys
import time

import xpybutil
import xpybutil.event as event
import xpybutil.ewmh as ewmh
import xpybutil.rect as rect
import xpybutil.util as util
import xpybutil.window as window
import xpybutil.xinerama as xinerama

from . import config

PYTYLE_STATE = 'startup'
GRAB = None

_wmrunning = False

wm = 'N/A'
utilwm = window.WindowManagers.Unknown
while not _wmrunning:
    w = ewmh.get_supporting_wm_check(xpybutil.root).reply()
    if w:
        childw = ewmh.get_supporting_wm_check(w).reply()
        if childw == w:
            _wmrunning = True
            wm = ewmh.get_wm_name(childw).reply()
            if wm.lower() == 'openbox':
                utilwm = window.WindowManagers.Openbox
            elif wm.lower() == 'kwin':
                utilwm = window.WindowManagers.KWin

            print(f'{wm} window manager is running...')
            sys.stdout.flush()

    if not _wmrunning:
        time.sleep(1)

root_geom = ewmh.get_desktop_geometry().reply()
monitors = xinerama.get_monitors()
phys_monitors = xinerama.get_physical_mapping(monitors)
desk_num = ewmh.get_number_of_desktops().reply()
activewin = ewmh.get_active_window().reply()
desktop = ewmh.get_current_desktop().reply()
visibles = ewmh.get_visible_desktops().reply() or [desktop]
stacking = ewmh.get_client_list_stacking().reply()
workarea = []


def pt3_monitor_rects(monitors):
    """
    (fixed version of xpybutil.rect.monitor_rects(monitors) working for
    Python 3)
    Takes a list of monitors returned by ```inerama.get_monitors``` and returns
    a new list of rectangles, in the same order, of monitor areas that account
    for all struts set by all windows. Duplicate struts are ignored.

    :param monitors: A list of 4-tuples representing monitor rectangles.
    :return: A list of 4-tuples representing monitor rectangles after
             substracing strut areas.
    :rtype: [(top_left_x, top_left_y, width, height)]
    """

    mons = monitors  # alias
    wa = mons[:]

    clients = ewmh.get_client_list().reply()

    log = []  # Identical struts should be ignored

    for c in clients:
        try:
            cx, cy, cw, ch = window.get_geometry(c)
        except xproto.BadWindow:
            continue

        for i, (x, y, w, h) in enumerate(wa):
            if rect.rect_intersect_area((x, y, w, h), (cx, cy, cw, ch)) > 0:
                struts = ewmh.get_wm_strut_partial(c).reply()
                if not struts:
                    struts = ewmh.get_wm_strut(c).reply()

                key = (cx, cy, cw, ch, struts)
                if key in log:
                    continue
                log.append(key)

                if struts and not all([v == 0 for v in struts.values()]):
                    if struts['left'] or struts['right']:
                        if struts['left']:
                            x += cw
                        w -= cw
                    if struts['top'] or struts['bottom']:
                        if struts['top']:
                            y += ch
                        h -= ch
                elif struts:
                    # x/y shouldn't be zero
                    if cx > 0 and w == cx + cw:
                        w -= cw
                    elif cy > 0 and h == cy + ch:
                        h -= ch
                    elif cx > 0 and x == cx:
                        x += cw
                        w -= cw
                    elif cy > 0 and y == cy:
                        y += ch
                        h -= ch

            wa[i] = (x, y, w, h)

    return wa


def quit():
    # Add desktop notification

    if config.send_desktop_notification:
        import gi
        gi.require_version('Notify', '0.7')
        from gi.repository import Notify
        Notify.init("Pytyle3")
        quit_notif = Notify.Notification.new("Pytyle3 Quit",
                                             "Pytyle3 is quitting",
                                             "dialog-information")
        quit_notif.show()

    print('Exiting...')
    from . import tile
    for tiler in tile.tilers:
        tile.get_active_tiler(tiler)[0].untile()
    sys.exit(0)


def update_workarea():
    '''
    We update the current workarea either by autodetecting struts, or by
    using margins specified in the config file. Never both, though.
    '''
    global workarea

    if hasattr(config, 'use_margins') and config.use_margins:
        workarea = monitors[:]
        for physm, margins in enumerate(config.margins):
            if physm == len(phys_monitors):
                break
            i = phys_monitors[physm]
            mx, my, mw, mh = workarea[i]
            workarea[i] = (mx + margins['left'], my + margins['top'],
                           mw - (margins['left'] + margins['right']),
                           mh - (margins['top'] + margins['bottom']))
    else:
        workarea = pt3_monitor_rects(monitors)


def cb_property_notify(e):
    global activewin, desk_num, desktop, monitors, phys_monitors, root_geom, \
        stacking, visibles, workarea

    aname = util.get_atom_name(e.atom)
    if aname == '_NET_DESKTOP_GEOMETRY':
        root_geom = ewmh.get_desktop_geometry().reply()
        monitors = xinerama.get_monitors()
        phys_monitors = xinerama.get_physical_mapping(monitors)
    elif aname == '_NET_ACTIVE_WINDOW':
        activewin = ewmh.get_active_window().reply()
    elif aname == '_NET_CURRENT_DESKTOP':
        desktop = ewmh.get_current_desktop().reply()
        if visibles is None or len(visibles) == 1:
            visibles = [desktop]
    elif aname == '_NET_VISIBLE_DESKTOPS':
        visibles = ewmh.get_visible_desktops().reply()
    elif aname == '_NET_NUMBER_OF_DESKTOPS':
        desk_num = ewmh.get_number_of_desktops().reply()
    elif aname == '_NET_CLIENT_LIST_STACKING':
        stacking = ewmh.get_client_list_stacking().reply()
    elif aname == '_NET_WORKAREA':
        update_workarea()


window.listen(xpybutil.root, 'PropertyChange')
event.connect('PropertyNotify', xpybutil.root, cb_property_notify)

update_workarea()
