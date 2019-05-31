from xpybutil.compat import xproto

import xpybutil.rect as rect
import xpybutil.ewmh as ewmh
import xpybutil.window as window


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
