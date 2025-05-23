import maya.cmds as cmds

ORIGO = "Origo"
CURRENT_COLOR_INDEX = [6]
CURRENT_COLOR_RGB_CREATE = [0.0, 0.0, 1.0]
CURRENT_COLOR_RGB_ADJUST = [0.0, 0.0, 1.0]
# -----------------------------------------------------------------------------------------------------------------#
#                                         ~ Controller Shape Definitions ~                                       #
# -----------------------------------------------------------------------------------------------------------------#

def create_pyramid_controller(name, size):
    base_points = [
        (7.894737, 0, -7.894737),
        (0, 0, 7.894737),
        (-7.894737, 0, -7.894737),
        (7.894737, 0, -7.894737),
        (7.894737, 0, -23.684211),
        (0, 0, -39.473684),
        (-7.894737, 0, -23.684211),
        (7.894737, 0, -23.684211),
        (-7.894737, 0, -23.684211),
        (-7.894737, 0, -7.894737),
    ]
    points = [(x * size, y * size, z * size) for x, y, z in base_points]
    curve = cmds.curve(d=1, p=points, k=range(len(points)), name=name)

    cmds.select(curve + ".ep[5]")
    cmds.move(0, 0, 23.684211 * size, r=True)
    cmds.select(curve + ".ep[1]")
    cmds.move(0, 0, -23.684211 * size, r=True)
    cmds.select([curve + ".ep[1]", curve + ".ep[5]"])
    cmds.move(0, 12.992507 * size, 0, r=True)

    return curve


def create_circle_controller(name, size):
    return cmds.circle(name=name, radius=5 * size, normal=[0, 1, 0])[0]


def create_box_controller(name, size):
    points = [
        (-1, 0, -1), (1, 0, -1),
        (1, 0, 1), (-1, 0, 1),
        (-1, 0, -1)
    ]
    scaled = [(x * size * 5, y, z * size * 5) for x, y, z in points]
    return cmds.curve(p=scaled, d=1, name=name)


ROTATION_ORDER = {
    "XYZ":0,
    "YZX":1,
    "ZXY":2,
    "XZY":3,
    "YXZ":4,
    "ZYX":5,
}

SHAPE_CREATORS = {
    "Pyramid": create_pyramid_controller,
    "Circle": create_circle_controller,
    "Box": create_box_controller,
}

COLOR_PRESETS = {
    "Blue": (6, [0.0, 0.0, 1.0]),
    "Red": (13, [1.0, 0.0, 0.0]),
    "Yellow": (17, [1.0, 1.0, 0.0]),
}

# -----------------------------------------------------------------------------------------------------------------#
#                                         ~ Core Controller Creation ~                                             #
# -----------------------------------------------------------------------------------------------------------------#

def find_origo():
    if not cmds.objExists(ORIGO):
        cmds.group(empty=True, name=ORIGO)

def match_pivot(source, target):
    pivot = cmds.xform(target, q=True, ws=True, rp=True)
    cmds.xform(source, ws=True, rp=pivot)
    cmds.xform(source, ws=True, sp=pivot)

def color_controller(ctrl, color_index=None, rgb=None):
    shapes = cmds.listRelatives(ctrl, s=True, f=True) or []
    for shape in shapes:
        if cmds.objectType(shape) == "nurbsCurve":
            cmds.setAttr(shape + ".overrideEnabled", 1)

            if rgb and isinstance(rgb, (list, tuple)) and len(rgb) == 3:
                cmds.setAttr(shape + ".overrideRGBColors", 1)
                # Forum-style method (more robust)
                cmds.setAttr(shape + ".overrideColorR", rgb[0])
                cmds.setAttr(shape + ".overrideColorG", rgb[1])
                cmds.setAttr(shape + ".overrideColorB", rgb[2])
            elif color_index is not None:
                cmds.setAttr(shape + ".overrideRGBColors", 0)
                cmds.setAttr(shape + ".overrideColor", color_index)

def create_custom_controller(name, size, shape_type, rgb=None, include_offset=True):
    find_origo()
    offset_group = [None]
    ctrl_name = "%s" % (name)
    if shape_type not in SHAPE_CREATORS:
        cmds.warning("Shape type '%s' not supported." % shape_type)
        return

    curve = SHAPE_CREATORS[shape_type](ctrl_name, size)

    cmds.xform(curve, cp=True)
    if shape_type == "Pyramid":
        cmds.move(0, 6.496254 * size, 0, curve + ".scalePivot", curve + ".rotatePivot", r=True)

    matchTransform(curve, ORIGO)
    cmds.makeIdentity(curve, apply=True, t=1, r=1, s=1, n=0)

    color_controller(curve, CURRENT_COLOR_INDEX[0], rgb=rgb)

    if include_offset:
        offset_group = cmds.group(empty=True, name=ctrl_name + "_offset")
        cmds.parent(curve, offset_group)
        match_pivot(offset_group, curve)

    if cmds.objExists(ORIGO):
        cmds.delete(ORIGO)

    return curve if not include_offset else [curve, offset_group]


def matchTransform(source, target):
    return cmds.delete(cmds.parentConstraint(target, source))

def safe_set_attr(node, attrs, lock, keyable, channelBox, value=None):
    for attr in attrs:
        full_attr = node + "." + attr
        cmds.setAttr(full_attr, lock=lock)
        if not keyable:
            cmds.setAttr(full_attr, keyable=keyable)
        cmds.setAttr(full_attr, channelBox=channelBox)
        if keyable:
            cmds.setAttr(full_attr, keyable=keyable)


# -----------------------------------------------------------------------------------------------------------------#
#                                           ~ UI Callbacks ~                                                       #
# -----------------------------------------------------------------------------------------------------------------#
def select_preset_color(label, tab="create"):
    index, rgb = COLOR_PRESETS[label]
    CURRENT_COLOR_INDEX[0] = index

    if tab == "create":
        CURRENT_COLOR_RGB_CREATE[:] = rgb
        cmds.button("colorPreviewCreate", e=True, bgc=rgb)
    else:
        CURRENT_COLOR_RGB_ADJUST[:] = rgb
        cmds.button("colorPreviewAdjust", e=True, bgc=rgb)

    update_name_preview()

def open_color_picker(tab="create"):
    result = cmds.colorEditor()
    if cmds.colorEditor(query=True, result=True):
        rgb = cmds.colorEditor(query=True, rgb=True)

        if tab == "create":
            CURRENT_COLOR_RGB_CREATE[:] = rgb
            cmds.button("colorPreviewCreate", e=True, bgc=rgb)
        else:
            CURRENT_COLOR_RGB_ADJUST[:] = rgb
            cmds.button("colorPreviewAdjust", e=True, bgc=rgb)

def on_create_button(name_field, prefix_field, suffix_field, size_field, shape_option):
    selection = cmds.ls(selection=True)
    do_match = cmds.checkBox("createMatchTransformCheck", q=True, value=True)
    name = cmds.textField(name_field, q=True, text=True)
    prefix = cmds.textField(prefix_field, q=True, text=True) if cmds.checkBox("prefixEnableCheck", q=True, value=True) else ""
    suffix = cmds.textField(suffix_field, q=True, text=True) if cmds.checkBox("suffixEnableCheck", q=True, value=True) else ""
    size = cmds.floatField(size_field, q=True, value=True)
    shape = cmds.optionMenu(shape_option, q=True, value=True)
    include_offset = cmds.checkBox("addOffsetGroupCheck", q=True, value=True)
    lock_offset_channels = cmds.checkBox("lockOffsetGroupCheck", q=True, value=True)

    if not name.strip():
        cmds.warning("Name cannot be empty.")
        return

    full_name = "{}{}{}".format(
        (prefix + "_") if prefix else "",
        name,
        ("_" + suffix) if suffix else ""
    )

    result = create_custom_controller(full_name, size, shape, rgb=CURRENT_COLOR_RGB_CREATE, include_offset=include_offset)

    if do_match and selection:
        target = selection[0]
        if cmds.objectType(target) in ["joint", "locator"]:
            source = result[1] if include_offset else result

            t_all = cmds.checkBox("createMatchTranslateAll", q=True, value=True)
            t_axes = [cmds.checkBox("createMatchTranslate" + axis, q=True, value=True) for axis in "XYZ"]

            r_all = cmds.checkBox("createMatchRotateAll", q=True, value=True)
            r_axes = [cmds.checkBox("createMatchRotate" + axis, q=True, value=True) for axis in "XYZ"]

            if t_all or any(t_axes):
                t_values = cmds.xform(target, q=True, ws=True, t=True)
                if not t_all:
                    s_values = cmds.xform(source, q=True, ws=True, t=True)
                    t_values = [t if a else s for t, s, a in zip(t_values, s_values, t_axes)]
                cmds.xform(source, ws=True, t=t_values)

            if r_all or any(r_axes):
                r_values = cmds.xform(target, q=True, ws=True, ro=True)
                if not r_all:
                    s_values = cmds.xform(source, q=True, ws=True, ro=True)
                    r_values = [r if a else s for r, s, a in zip(r_values, s_values, r_axes)]
                cmds.xform(source, ws=True, ro=r_values)

            cmds.warning(source + " matched transform to: " + target)
        else:
            cmds.warning("Selected object is not a joint or locator. Skipping matchTransform.")
    if include_offset and lock_offset_channels:
        offset_group = result[1]
        attrs = ["translateX", "translateY", "translateZ",
                 "rotateX", "rotateY", "rotateZ",
                 "scaleX", "scaleY", "scaleZ", "visibility"]
        safe_set_attr(offset_group, attrs, lock=True, keyable=False, channelBox=False)
        cmds.warning("Locked and hid all channels on offset group: %s" % offset_group)


def update_name_preview():
    name = cmds.textField("ctrlNameField", q=True, text=True) if cmds.control("ctrlNameField", exists=True) else ""
    prefix = cmds.textField("ctrlPrefixField", q=True, text=True) if cmds.control("ctrlPrefixField", exists=True) and cmds.checkBox("prefixEnableCheck", q=True, value=True) else ""
    suffix = cmds.textField("ctrlSuffixField", q=True, text=True) if cmds.control("ctrlSuffixField", exists=True) and cmds.checkBox("suffixEnableCheck", q=True, value=True) else ""
    full_name = "{}{}{}".format(
        (prefix + "_") if prefix else "",
        name,
        ("_" + suffix) if suffix else ""
    )

    if cmds.control("namePreviewField", exists=True):
        cmds.textField("namePreviewField", e=True, text=full_name)

def lock_mode_sync(active):
    cmds.checkBox("modeLock", e=True, value=(active == "Lock"))
    cmds.checkBox("modeLockHide", e=True, value=(active == "LockHide"))
    cmds.checkBox("modeUnlock", e=True, value=(active == "Unlock"))

def adjust_lock_channels(*_):
    selection = cmds.ls(selection=True, long=True)
    if not selection:
        cmds.warning("Select a controller or offset group.")
        return

    lock = [None]
    keyable = True
    channelBox = [None]
    # Which attributes
    attrs = []

    # Translate
    t_all = cmds.checkBox("lockTranslateAll", q=True, value=True)
    if t_all or cmds.checkBox("lockTranslateX", q=True, value=True): attrs.append("translateX")
    if t_all or cmds.checkBox("lockTranslateY", q=True, value=True): attrs.append("translateY")
    if t_all or cmds.checkBox("lockTranslateZ", q=True, value=True): attrs.append("translateZ")

    # Rotate
    r_all = cmds.checkBox("lockRotateAll", q=True, value=True)
    if r_all or cmds.checkBox("lockRotateX", q=True, value=True): attrs.append("rotateX")
    if r_all or cmds.checkBox("lockRotateY", q=True, value=True): attrs.append("rotateY")
    if r_all or cmds.checkBox("lockRotateZ", q=True, value=True): attrs.append("rotateZ")

    # Scale
    s_all = cmds.checkBox("lockScaleAll", q=True, value=True)
    if s_all or cmds.checkBox("lockScaleX", q=True, value=True): attrs.append("scaleX")
    if s_all or cmds.checkBox("lockScaleY", q=True, value=True): attrs.append("scaleY")
    if s_all or cmds.checkBox("lockScaleZ", q=True, value=True): attrs.append("scaleZ")

    # Visibility (no axis options)
    if cmds.checkBox("lockVisibility", q=True, value=True): attrs.append("visibility")

    # Mode
    if cmds.checkBox("modeLock", q=True, value=True):
        lock, keyable, channelBox = True, False, True
    elif cmds.checkBox("modeLockHide", q=True, value=True):
        lock, keyable, channelBox = True, False, False
    elif cmds.checkBox("modeUnlock", q=True, value=True):   # Unlock
        lock, keyable, channelBox = False, True, True

    # Apply to controller or its child with shape
    for obj in selection:
        safe_set_attr(node=obj, attrs=attrs, lock=lock, keyable=keyable, channelBox=channelBox)
        cmds.warning("Updated lock state on: %s" % obj)



def adjust_rotate_order(*_):
    selection = cmds.ls(selection=True, long=True)
    if not selection:
        cmds.warning("Select a controller or its offset group.")
        return

    selected_order_label = cmds.optionMenu("rotationOrder", q=True, value=True)
    rotation_order = ROTATION_ORDER.get(selected_order_label, 0)

    for obj in selection:
        targets = []

        # Direct controller with shape?
        if cmds.objectType(obj) == "transform":
            shapes = cmds.listRelatives(obj, shapes=True, f=True) or []
            if any(cmds.objectType(s) == "nurbsCurve" for s in shapes):
                targets.append(obj)

        # Offset group? Look inside for child with shape
        children = cmds.listRelatives(obj, children=True, fullPath=True) or []
        for child in children:
            shapes = cmds.listRelatives(child, shapes=True, f=True) or []
            if any(cmds.objectType(s) == "nurbsCurve" for s in shapes):
                targets.append(child)

        if not targets:
            cmds.warning("No controller found under: %s" % obj)
            continue

        for ctrl in targets:
            try:
                cmds.setAttr(ctrl + ".rotateOrder", rotation_order)
                cmds.warning("Set rotate order to %s on: %s" % (selected_order_label, ctrl))
            except Exception as e:
                cmds.warning("Failed to set rotate order on %s: %s" % (ctrl, str(e)))

def adjust_match_transform(*_):
    selection = cmds.ls(selection=True)
    if len(selection) != 2:
        cmds.warning("Select a controller and a target joint or locator.")
        return

    source, target = selection
    if cmds.objectType(target) not in ["joint", "locator"]:
        source, target = target, source
        if cmds.objectType(target) not in ["joint", "locator"]:
            cmds.warning("One selected object must be a joint or locator.")
            return

    # Match options
    t_all = cmds.checkBox("matchTranslateAll", q=True, value=True)
    t_axes = [cmds.checkBox("matchTranslate" + axis, q=True, value=True) for axis in "XYZ"]

    r_all = cmds.checkBox("matchRotateAll", q=True, value=True)
    r_axes = [cmds.checkBox("matchRotate" + axis, q=True, value=True) for axis in "XYZ"]

    # Apply transform matching
    if t_all or any(t_axes):
        t_values = cmds.xform(target, q=True, ws=True, t=True)
        if not t_all:
            s_values = cmds.xform(source, q=True, ws=True, t=True)
            t_values = [t if a else s for t, s, a in zip(t_values, s_values, t_axes)]
        cmds.xform(source, ws=True, t=t_values)

    if r_all or any(r_axes):
        r_values = cmds.xform(target, q=True, ws=True, ro=True)
        if not r_all:
            s_values = cmds.xform(source, q=True, ws=True, ro=True)
            r_values = [r if a else s for r, s, a in zip(r_values, s_values, r_axes)]
        cmds.xform(source, ws=True, ro=r_values)

    cmds.warning(source + " matched transform to " + target)

def adjust_change_color(*_):
    selection = cmds.ls(selection=True, long=True)
    if not selection:
        cmds.warning("Select a controller or its offset group.")
        return

    rgb = CURRENT_COLOR_RGB_ADJUST

    for obj in selection:
        shape_targets = []

        # Case 1: Direct curve shape on selected node
        if cmds.objectType(obj) == "transform":
            shapes = cmds.listRelatives(obj, shapes=True, f=True) or []
            if any(cmds.objectType(s) == "nurbsCurve" for s in shapes):
                shape_targets.append(obj)

        # Case 2: Offset group selected — try to find child with shape
        children = cmds.listRelatives(obj, children=True, fullPath=True) or []
        for child in children:
            shapes = cmds.listRelatives(child, shapes=True, f=True) or []
            if any(cmds.objectType(s) == "nurbsCurve" for s in shapes):
                shape_targets.append(child)

        for ctrl in shape_targets:
            color_controller(ctrl, rgb=rgb)

# -----------------------------------------------------------------------------------------------------------------#
#                                            ~ UI Styling ~                                                        #
# -----------------------------------------------------------------------------------------------------------------#
def with_standard_row(label, build_control_func):
    cmds.rowLayout(nc=3, adjustableColumn=2, columnWidth3=(50, 9, 250), columnAlign=(1, 'left'),
                   columnAttach=[(1, 'both', 5), (2, 'both', 0), (3, 'both', 0)])
    cmds.text(label=label, align='left')
    cmds.text(label="")
    result = build_control_func()
    cmds.setParent('..')
    return result

def format_layout(label, control_type, name, **kwargs):
    return with_standard_row(label, lambda: control_type(name, **kwargs))

def format_option_menu(label, name, options):
    def build_menu():
        menu = cmds.optionMenu(name)
        for item in options:
            cmds.menuItem(label=item)
        return menu
    return with_standard_row(label, build_menu)

def format_text_rows(nameLabel, textFieldName, text, hasCheckBox):
    checkBox_result = [None]  # Mutable container to store checkbox

    def build_control():
        editable = textFieldName != "namePreviewField"
        return cmds.textField(textFieldName, text=text, editable=editable, cc="update_name_preview()")

    cmds.rowLayout(nc=3, adjustableColumn=2, columnWidth3=(50, 9, 250), columnAlign=(1, 'left'),
                   columnAttach=[(1, 'both', 5), (2, 'both', 0), (3, 'both', 0)])
    cmds.text(label=nameLabel, align='left')

    # Always insert something in column 2, checkbox or blank placeholder
    if hasCheckBox:
        checkBox_result[0] = insert_checkBox(nameLabel)
    else:
        cmds.text(label="")  # empty spacer

    textField = build_control()
    cmds.setParent('..')
    return checkBox_result[0], textField

def insert_checkBox(label):
    checkBox_name = "%sEnableCheck" % label.lower()
    textField_name = "ctrl%sField" % label
    return cmds.checkBox(checkBox_name, label="", value=True,
                         cc=lambda *_: toggle_textField_enabled(checkBox_name, textField_name))

def toggle_textField_enabled(checkBox_name, textField_name):
    is_checked = cmds.checkBox(checkBox_name, q=True, value=True)
    cmds.textField(textField_name, e=True, editable=is_checked)
    update_name_preview()

def format_button_row(buttons):
    cmds.rowLayout(nc=len(buttons), columnWidth=[(i + 1, 80) for i in range(len(buttons))], columnAlign=(1, 'center'), columnAttach=[(1, 'left', 40), (2, 'both', 3), (3, 'right', 3)])
    for label, cmd in buttons:
        cmds.button(label=label, w=80, h=25, command=cmd)
    cmds.setParent('..')

def separator(index=0):
    styles = [
        {'h': 10, 'style': 'in'},  # Default: visible separator line
        {'h': 5, 'style': 'none'},  # Subtle spacing only
        {'h': 15, 'style': 'out'}  # Emphasized separator
    ]
    s = styles[min(index, len(styles) - 1)]
    cmds.separator(h=s['h'], style=s['style'])

def match_option_sync(prefix, changed):
    if changed == "All":
        for axis in "XYZ":
            cmds.checkBox(prefix + axis, e=True, value=False)
    else:
        cmds.checkBox(prefix + "All", e=True, value=False)

def lock_axis_sync(prefix, changed):
    if changed == "All":
        # Disable individual axes
        for axis in "XYZ":
            cmds.checkBox(prefix + axis, e=True, value=False)

        update_global_lock_all()

    else:
        cmds.checkBox(prefix + "All", e=True, value=False)
        cmds.checkBox("matchChannelLockAll", e=True, value=False)
        cmds.checkBox("matchChannelLockNone", e=True, value=False)

def update_global_lock_all():
    all_all = (
        cmds.checkBox("lockTranslateAll", q=True, value=True) and
        cmds.checkBox("lockRotateAll", q=True, value=True) and
        cmds.checkBox("lockScaleAll", q=True, value=True) and
        cmds.checkBox("lockVisibility", q=True, value=True)
    )
    cmds.checkBox("matchChannelLockAll", e=True, value=all_all)

    if not all_all:
        cmds.checkBox("matchChannelLockNone", e=True, value=False)

def handle_global_channel_lock_toggle(mode):
    is_all = (mode == "All")
    is_none = (mode == "None")

    cmds.checkBox("lockTranslateAll", e=True, value=is_all)
    cmds.checkBox("lockRotateAll", e=True, value=is_all)
    cmds.checkBox("lockScaleAll", e=True, value=is_all)
    cmds.checkBox("lockVisibility", e=True, value=is_all)

    for prefix in ["lockTranslate", "lockRotate", "lockScale"]:
        for axis in "XYZ":
            cmds.checkBox(prefix + axis, e=True, value=False)

    cmds.checkBox("matchChannelLockAll", e=True, value=is_all)
    cmds.checkBox("matchChannelLockNone", e=True, value=is_none)

# -----------------------------------------------------------------------------------------------------------------#
#                                           ~ UI Layout ~                                                          #
# -----------------------------------------------------------------------------------------------------------------#
def create_ui():
    if cmds.window("CTRLonDemand", exists=True):
        cmds.deleteUI("CTRLonDemand")

    window = cmds.window("CTRLonDemand", title="CTRLonDemand", sizeable=True)
    cmds.columnLayout(adjustableColumn=True)

    tabs = cmds.tabLayout(innerMarginWidth=5, innerMarginHeight=5)

    # -------------------------------------#
    # ----- Tab 1: Create controller ----- #
    # -------------------------------------#
    create_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=8)

    # Section: Controller Settings
    cmds.frameLayout(label="CTRL ON DEMAND", collapsable=True, collapse=False, marginHeight=6, marginWidth=6)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)

    prefix_checkBox, prefix_field = format_text_rows("Prefix", "ctrlPrefixField", "prefix", True)
    _, name_field = format_text_rows("Name", "ctrlNameField", "ctrl", False)
    suffix_checkBox, suffix_field = format_text_rows("Suffix", "ctrlSuffixField", "suffix", True)

    cmds.rowLayout(nc=2)
    cmds.checkBox("addOffsetGroupCheck", label="Add offset group?", value=False)
    cmds.checkBox("lockOffsetGroupCheck", label="Lock/Hide offset group channels", value=False)
    cmds.setParent("..")

    format_text_rows("Preview", "namePreviewField", cmds.textField("ctrlPrefixField", q=True, text=True) + "_" +
                     cmds.textField("ctrlNameField", q=True, text=True) + "_" +
                     cmds.textField("ctrlSuffixField", q=True, text=True), False)


    shape_option = format_option_menu("Shape", "ctrlShapeMenu", sorted(SHAPE_CREATORS.keys()))
    separator(0)
    size_field = format_layout("Size", cmds.floatField, "ctrlSizeField", value=1.0)
    separator(2)
    cmds.setParent("..")  # columnLayout
    cmds.setParent("..")  # frameLayout

    # Section: Match Transform
    cmds.frameLayout(label="Match Transform", collapsable=True, collapse=False, marginHeight=6, marginWidth=6)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)

    cmds.checkBox("createMatchTransformCheck", label="Match to selected joint or locator", value=True)

    # Translate options
    cmds.text(label="Translate:", align="left")
    cmds.rowLayout(nc=4)
    cmds.checkBox("createMatchTranslateAll", label="All", value=True,
                  cc=lambda *_: match_option_sync("createMatchTranslate", "All"))
    cmds.checkBox("createMatchTranslateX", label="X", value=False,
                  cc=lambda *_: match_option_sync("createMatchTranslate", "X"))
    cmds.checkBox("createMatchTranslateY", label="Y", value=False,
                  cc=lambda *_: match_option_sync("createMatchTranslate", "Y"))
    cmds.checkBox("createMatchTranslateZ", label="Z", value=False,
                  cc=lambda *_: match_option_sync("createMatchTranslate", "Z"))
    cmds.setParent("..")

    # Rotate options
    cmds.text(label="Rotate:", align="left")
    cmds.rowLayout(nc=4)
    cmds.checkBox("createMatchRotateAll", label="All", value=True,
                  cc=lambda *_: match_option_sync("createMatchRotate", "All"))
    cmds.checkBox("createMatchRotateX", label="X", value=False,
                  cc=lambda *_: match_option_sync("createMatchRotate", "X"))
    cmds.checkBox("createMatchRotateY", label="Y", value=False,
                  cc=lambda *_: match_option_sync("createMatchRotate", "Y"))
    cmds.checkBox("createMatchRotateZ", label="Z", value=False,
                  cc=lambda *_: match_option_sync("createMatchRotate", "Z"))
    cmds.setParent("..")
    cmds.setParent("..")  # end columnLayout
    cmds.setParent("..")  # end frameLayout

    # Section: Color
    cmds.frameLayout(label="Choose Color", collapsable=True, collapse=False, marginHeight=6, marginWidth=6)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)
    format_button_row([
        ("Blue", lambda *_: select_preset_color("Blue", "create")),
        ("Red", lambda *_: select_preset_color("Red", "create")),
        ("Yellow", lambda *_: select_preset_color("Yellow", "create"))
    ])

    cmds.rowLayout(nc=1, adjustableColumn=2, columnWidth1=250, columnAlign=(1, 'center'), columnAttach=[(1, 'both', 40)])
    cmds.button("colorPreviewCreate", label="", bgc=CURRENT_COLOR_RGB_CREATE, h=25, w=250, command=lambda *_: open_color_picker("create"))
    cmds.setParent("..")
    cmds.setParent("..")
    cmds.setParent("..")

    # Section: Create Button
    separator(2)
    cmds.button(label="Create Controller", h=40, bgc=(0.2, 0.6, 0.3), # Green button
                command=lambda *_: on_create_button(name_field, prefix_field, suffix_field, size_field, shape_option))
    cmds.setParent('..')  # end of create_layout

    # -------------------------------------#
    # ----- Tab 2: Adjust Controller ----- #
    # -------------------------------------#

    adjust_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=10)

    # Section: Match Transform
    cmds.frameLayout(label="Match Transform", collapsable=True, collapse=False, marginHeight=6, marginWidth=6)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=5)

    cmds.frameLayout(label="Match Options", collapsable=True, collapse=False, marginHeight=6, marginWidth=6)
    cmds.columnLayout(adjustableColumn=True)

    # Subsection: Match Options
    cmds.text(label="Translate:", align="left")
    cmds.rowLayout(nc=4)
    cmds.checkBox("matchTranslateAll", label="All", value=True,
                  cc=lambda _: match_option_sync("matchTranslate", "All"))
    cmds.checkBox("matchTranslateX", label="X", value=False,
                  cc=lambda _: match_option_sync("matchTranslate", "X"))
    cmds.checkBox("matchTranslateY", label="Y", value=False,
                  cc=lambda _: match_option_sync("matchTranslate", "Y"))
    cmds.checkBox("matchTranslateZ", label="Z", value=False,
                  cc=lambda _: match_option_sync("matchTranslate", "Z"))
    cmds.setParent("..")

    cmds.text(label="Rotate:", align="left")
    cmds.rowLayout(nc=4)
    cmds.checkBox("matchRotateAll", label="All", value=True,
                  cc=lambda _: match_option_sync("matchRotate", "All"))
    cmds.checkBox("matchRotateX", label="X", value=False,
                  cc=lambda _: match_option_sync("matchRotate", "X"))
    cmds.checkBox("matchRotateY", label="Y", value=False,
                  cc=lambda _: match_option_sync("matchRotate", "Y"))
    cmds.checkBox("matchRotateZ", label="Z", value=False,
                  cc=lambda _: match_option_sync("matchRotate", "Z"))
    cmds.setParent("..")
    cmds.setParent("..")  # end columnLayout
    cmds.setParent("..")  # end frameLayout

    cmds.text("Select the source then the target")
    separator(1)
    cmds.button(label="Match Transform", h=30, bgc=(0.5, 0.5, 0.5), command=adjust_match_transform)
    cmds.setParent("..")  # columnLayout
    cmds.setParent("..")  # frameLayout


    # Section: Lock/Unlock Channels
    cmds.frameLayout(label="Channel Locking", collapsable=True, collapse=False, marginHeight=6, marginWidth=6)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)

    # Channel options
    # Channel axis options
    cmds.rowLayout(nc=3)
    cmds.text(label="Affect Channels:", align="left")
    cmds.checkBox("matchChannelLockAll", label="All", value=True,
                  cc=lambda *_: handle_global_channel_lock_toggle("All"))
    cmds.checkBox("matchChannelLockNone", label="None", value=False,
                  cc=lambda *_: handle_global_channel_lock_toggle("None"))
    cmds.setParent("..")

    # Translate
    cmds.rowLayout(nc=6)
    cmds.text(label="Translate", align="left", w=65)
    cmds.checkBox("lockTranslateAll", label="All", value=True,
                  cc=lambda *_: lock_axis_sync("lockTranslate", "All"))
    cmds.checkBox("lockTranslateX", label="X", value=False,
                  cc=lambda *_: lock_axis_sync("lockTranslate", "X"))
    cmds.checkBox("lockTranslateY", label="Y", value=False,
                  cc=lambda *_: lock_axis_sync("lockTranslate", "Y"))
    cmds.checkBox("lockTranslateZ", label="Z", value=False,
                  cc=lambda *_: lock_axis_sync("lockTranslate", "Z"))
    cmds.setParent("..")

    # Rotate
    cmds.rowLayout(nc=6)
    cmds.text(label="Rotate", align="left", w=65)
    cmds.checkBox("lockRotateAll", label="All", value=True,
                  cc=lambda *_: lock_axis_sync("lockRotate", "All"))
    cmds.checkBox("lockRotateX", label="X", value=False,
                  cc=lambda *_: lock_axis_sync("lockRotate", "X"))
    cmds.checkBox("lockRotateY", label="Y", value=False,
                  cc=lambda *_: lock_axis_sync("lockRotate", "Y"))
    cmds.checkBox("lockRotateZ", label="Z", value=False,
                  cc=lambda *_: lock_axis_sync("lockRotate", "Z"))
    cmds.setParent("..")

    # Scale
    cmds.rowLayout(nc=6)
    cmds.text(label="Scale", align="left", w=65)
    cmds.checkBox("lockScaleAll", label="All", value=True,
                  cc=lambda *_: lock_axis_sync("lockScale", "All"))
    cmds.checkBox("lockScaleX", label="X", value=False,
                  cc=lambda *_: lock_axis_sync("lockScale", "X"))
    cmds.checkBox("lockScaleY", label="Y", value=False,
                  cc=lambda *_: lock_axis_sync("lockScale", "Y"))
    cmds.checkBox("lockScaleZ", label="Z", value=False,
                  cc=lambda *_: lock_axis_sync("lockScale", "Z"))
    cmds.setParent("..")

    # Visibility
    cmds.rowLayout(nc=2)
    cmds.text(label="Visibility", align="left", w=65)
    cmds.checkBox("lockVisibility", label="", value=True,
                  cc=lambda *_: update_global_lock_all())

    cmds.setParent("..")

    # Mode options
    cmds.text(label="Operation:", align="left")
    cmds.rowLayout(nc=3)
    cmds.checkBox("modeLock", label="Lock", value=False,
                  cc=lambda *_: lock_mode_sync("Lock"))
    cmds.checkBox("modeLockHide", label="Lock & Hide", value=False,
                  cc=lambda *_: lock_mode_sync("LockHide"))
    cmds.checkBox("modeUnlock", label="Unlock & Unhide", value=False,
                  cc=lambda *_: lock_mode_sync("Unlock"))
    cmds.setParent("..")

    cmds.button(label="Apply Channel Locking", h=30, bgc=(0.5, 0.5, 0.5), command=adjust_lock_channels)
    cmds.setParent("..")  # columnLayout
    cmds.setParent("..")  # frameLayout

    # Change pivot --->>>>>>>>>

    # Section: Rotation Order
    cmds.frameLayout(label="Rotation Order", collapsable=True,collapse=False, marginHeight=6, marginWidth=6)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
    format_option_menu("Rotation Order", "rotationOrder", sorted(ROTATION_ORDER.keys()))
    cmds.button(label="Change rotation order", h=30, bgc=(0.5, 0.5, 0.5), command=adjust_rotate_order)
    cmds.setParent("..")  # columnLayout
    cmds.setParent("..")  # frameLayout

    # Section: Choose Color
    cmds.frameLayout(label="Choose Color", collapsable=True, collapse=False, marginHeight=6, marginWidth=6)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)
    format_button_row([
        ("Blue", lambda *_: select_preset_color("Blue", "adjust")),
        ("Red", lambda *_: select_preset_color("Red", "adjust")),
        ("Yellow", lambda *_: select_preset_color("Yellow", "adjust"))
    ])

    cmds.rowLayout(nc=1, adjustableColumn=2, columnWidth1=250, columnAlign=(1, 'center'), columnAttach=[(1, 'both', 40)])
    cmds.button("colorPreviewAdjust", label="", bgc=CURRENT_COLOR_RGB_ADJUST, h=25, w=250, command=lambda *_: open_color_picker("adjust"))
    cmds.setParent("..")
    separator(1)
    cmds.button("adjustColorButton", label="Change Color", h=30, bgc=(0.5, 0.5, 0.5), command=adjust_change_color, ann="Select a controller or offset group")

    cmds.setParent('..')  # columnLayout
    cmds.setParent('..')  # frameLayout
    cmds.setParent('..')  # adjust_layout

    cmds.tabLayout(tabs, edit=True, tabLabel=[(create_layout, "Create Controller"), (adjust_layout, "Adjust Controller")])

    def update_change_color_button_state():
        selection = cmds.ls(selection=True, long=True)
        enable = False

        for obj in selection:
            # Check if selected or its children have a nurbsCurve
            if cmds.objectType(obj) == "transform":
                if any(cmds.objectType(s) == "nurbsCurve" for s in (cmds.listRelatives(obj, s=True, f=True) or [])):
                    enable = True
                    break
                children = cmds.listRelatives(obj, c=True, f=True) or []
                for child in children:
                    if any(cmds.objectType(s) == "nurbsCurve" for s in (cmds.listRelatives(child, s=True, f=True) or [])):
                        enable = True
                        break

        cmds.button("adjustColorButton", e=True, enable=enable)

    # Attach scriptJob to selection changes
    cmds.scriptJob(event=["SelectionChanged", update_change_color_button_state], parent=window)
    update_change_color_button_state()

    cmds.showWindow(window)

if __name__ == "__main__":
    create_ui()