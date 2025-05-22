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
        matchPivot(offset_group, curve)

    if cmds.objExists(ORIGO):
        cmds.delete(ORIGO)

    return curve if not include_offset else [curve, offset_group]

def matchPivot(source, target):
    pivot = cmds.xform(target, q=True, ws=True, rp=True)
    cmds.xform(source, ws=True, rp=pivot)
    cmds.xform(source, ws=True, sp=pivot)

def matchTransform(source, target):
    return cmds.delete(cmds.parentConstraint(target, source))

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
    selection = cmds.ls(selection=True) # Store the selection
    name = cmds.textField(name_field, q=True, text=True)
    prefix = cmds.textField(prefix_field, q=True, text=True) if cmds.checkBox("prefixEnableCheck", q=True, value=True) else ""
    suffix = cmds.textField(suffix_field, q=True, text=True) if cmds.checkBox("suffixEnableCheck", q=True, value=True) else ""
    size = cmds.floatField(size_field, q=True, value=True)
    shape = cmds.optionMenu(shape_option, q=True, value=True)
    include_offset = cmds.checkBox("addOffsetGroupCheck", q=True, value=True)

    if not name.strip():
        cmds.warning("Name cannot be empty.")
        return

    full_name = "{}{}{}".format(
        (prefix + "_") if prefix else "",
        name,
        ("_" + suffix) if suffix else ""
    )

    result = create_custom_controller(full_name, size, shape, rgb=CURRENT_COLOR_RGB_CREATE, include_offset=include_offset)

    if selection:
        target = selection[0]
        if cmds.objectType(target) in ["joint", "locator"]:
            source = result[1] if include_offset else result
            matchTransform(source, target)
            cmds.warning(source + " matched transform to: " + target)
        else:
            cmds.warning("Selected object is not a joint or locator. Skipping matchTransform.")


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

#UI Styling
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
        source, target = target, source  # try swapping
        if cmds.objectType(target) not in ["joint", "locator"]:
            cmds.warning("One selected object must be a joint or locator.")
            return

    matchTransform(source, target)
    cmds.warning(source + " matched to " + target)

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

        if not shape_targets:
            cmds.warning("No controller shape found under: " + obj)
            continue

        for ctrl in shape_targets:
            color_controller(ctrl, rgb=rgb)


def with_standard_row(label, build_control_func):
    cmds.rowLayout(nc=3, adjustableColumn=2, columnWidth3=(50, 9, 250), columnAlign=(1, 'left'),
                   columnAttach=[(1, 'both', 5), (2, 'both', 0), (3, 'both', 0)])
    cmds.text(label=label, align='left')
    cmds.text(label="")
    result = build_control_func()
    cmds.setParent('..')
    return result

def formatLayout(label, controlType, name, **kwargs):
    return with_standard_row(label, lambda: controlType(name, **kwargs))

def formatOptionMenu(label, name, options):
    def build_menu():
        menu = cmds.optionMenu(name)
        for item in options:
            cmds.menuItem(label=item)
        return menu
    return with_standard_row(label, build_menu)

def formatTextRows(nameLabel, textFieldName, text, hasCheckBox):
    checkBox_result = [None]  # Mutable container to store checkbox

    def build_control():
        editable = textFieldName != "namePreviewField"
        return cmds.textField(textFieldName, text=text, editable=editable, cc="update_name_preview()")

    cmds.rowLayout(nc=3, adjustableColumn=2, columnWidth3=(50, 9, 250), columnAlign=(1, 'left'),
                   columnAttach=[(1, 'both', 5), (2, 'both', 0), (3, 'both', 0)])
    cmds.text(label=nameLabel, align='left')

    # Always insert something in column 2, checkbox or blank placeholder
    if hasCheckBox:
        checkBox_result[0] = insertcheckBox(nameLabel)
    else:
        cmds.text(label="")  # empty spacer

    textField = build_control()
    cmds.setParent('..')
    return checkBox_result[0], textField

def insertcheckBox(label):
    checkBox_name = "%sEnableCheck" % label.lower()
    textField_name = "ctrl%sField" % label
    return cmds.checkBox(checkBox_name, label="", value=True,
                         cc=lambda *_: toggle_textField_enabled(checkBox_name, textField_name))

def toggle_textField_enabled(checkBox_name, textField_name):
    is_checked = cmds.checkBox(checkBox_name, q=True, value=True)
    cmds.textField(textField_name, e=True, editable=is_checked)
    update_name_preview()

def formatButtonRow(buttons):
    cmds.rowLayout(nc=len(buttons), columnWidth=[(i + 1, 80) for i in range(len(buttons))], columnAlign=(1, 'center'), columnAttach=[(1, 'left', 40), (2, 'both', 3), (3, 'right', 3)])
    for label, cmd in buttons:
        cmds.button(label=label, w=80, h=25, command=cmd)
    cmds.setParent('..')

def Separator(index=0):
    styles = [
        {'h': 10, 'style': 'in'},  # Default: visible separator line
        {'h': 5, 'style': 'none'},  # Subtle spacing only
        {'h': 15, 'style': 'out'}  # Emphasized separator
    ]
    s = styles[min(index, len(styles) - 1)]
    cmds.separator(h=s['h'], style=s['style'])

# -----------------------------------------------------------------------------------------------------------------#
#                                           ~ UI Layout ~                                                          #
# -----------------------------------------------------------------------------------------------------------------#
def create_ui():
    if cmds.window("CTRLonDemand", exists=True):
        cmds.deleteUI("CTRLonDemand")

    window = cmds.window("CTRLonDemand", title="CTRLonDemand", sizeable=True)
    cmds.columnLayout(adjustableColumn=True)

    tabs = cmds.tabLayout(innerMarginWidth=5, innerMarginHeight=5)

    # Tab 1: Create controller
    create_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=8)

    # Section: Controller Settings
    cmds.frameLayout(label="CTRL ON DEMAND", collapsable=True, collapse=False, marginHeight=6, marginWidth=6)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)

    prefix_checkBox, prefix_field = formatTextRows("Prefix", "ctrlPrefixField", "prefix", True)
    _, name_field = formatTextRows("Name", "ctrlNameField", "ctrl", False)
    suffix_checkBox, suffix_field = formatTextRows("Suffix", "ctrlSuffixField", "suffix", True)

    cmds.checkBox("addOffsetGroupCheck", label="Add offset group?", value=False)

    formatTextRows("Preview", "namePreviewField", cmds.textField("ctrlPrefixField", q=True, text=True) + "_" +
                                            cmds.textField("ctrlNameField", q=True, text=True) + "_" +
                                            cmds.textField("ctrlSuffixField", q=True, text=True), False )


    shape_option = formatOptionMenu("Shape", "ctrlShapeMenu", sorted(SHAPE_CREATORS.keys()))
    Separator(0)
    size_field = formatLayout("Size", cmds.floatField, "ctrlSizeField", value=1.0)
    Separator(2)
    cmds.setParent("..")  # columnLayout
    cmds.setParent("..")  # frameLayout

    # Color Selection
    cmds.frameLayout(label="Choose Color", collapsable=True, collapse=False, marginHeight=6, marginWidth=6)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)
    formatButtonRow([
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
    Separator(2)
    cmds.button(label="Create Controller", h=40, bgc=(0.2, 0.6, 0.3), #Green button
                command=lambda *_: on_create_button(name_field, prefix_field, suffix_field, size_field, shape_option))
    cmds.setParent('..')  # end of create_layout

    # --- Tab 2: Adjust Controller ---
    adjust_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=10)

    cmds.frameLayout(label="Adjust Controller", collapsable=True, collapse=False, marginHeight=6, marginWidth=6)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=5)

    cmds.text("Select the source then the target")
    cmds.button(label="Match Transform", h=30, bgc=(0.5, 0.5, 0.5), command=adjust_match_transform)
    Separator(1)

    # Change pivot --->>>>>>>>>

    cmds.frameLayout(label="Rotation Order", collapsable=True,collapse=False, marginHeight=6, marginWidth=6)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
    formatOptionMenu("Rotation Order", "rotationOrder", sorted(ROTATION_ORDER.keys()))
    cmds.button(label="Change rotation order", h=30, bgc=(0.5, 0.5, 0.5), command=adjust_rotate_order)
    Separator(1)

    cmds.frameLayout(label="Choose Color", collapsable=True, collapse=False, marginHeight=6, marginWidth=6)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)
    formatButtonRow([
        ("Blue", lambda *_: select_preset_color("Blue", "adjust")),
        ("Red", lambda *_: select_preset_color("Red", "adjust")),
        ("Yellow", lambda *_: select_preset_color("Yellow", "adjust"))
    ])

    cmds.rowLayout(nc=1, adjustableColumn=2, columnWidth1=250, columnAlign=(1, 'center'), columnAttach=[(1, 'both', 40)])
    cmds.button("colorPreviewAdjust", label="", bgc=CURRENT_COLOR_RGB_ADJUST, h=25, w=250, command=lambda *_: open_color_picker("adjust"))
    cmds.setParent("..")
    Separator(1)
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