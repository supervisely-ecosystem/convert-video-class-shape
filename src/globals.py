import os
import supervisely as sly
from supervisely.app.v1.app_service import AppService

my_app: AppService = AppService()

TEAM_ID = int(os.environ['context.teamId'])
WORKSPACE_ID = int(os.environ['context.workspaceId'])
PROJECT_ID = int(os.environ['modal.state.slyProjectId'])

ORIGINAL_META = None
REMAIN_UNCHANGED = "remain unchanged"

SHAPE_TO_ICON = {
    sly.Rectangle: {"icon": "zmdi zmdi-crop-din", "color": "#ea9d22", "bg": "#fcefd9"},
    sly.Bitmap: {"icon": "zmdi zmdi-brush", "color": "#ff8461", "bg": "#ffebe3"},
    sly.Polygon: {"icon": "icons8-polygon", "color": "#2cd26e", "bg": "#d8f8e7"},
    sly.AnyGeometry: {"icon": "zmdi zmdi-grain", "color": "#e09e11", "bg": "#faf0d8"},
    sly.Polyline: {"icon": "zmdi zmdi-minus", "color": "#ceadff", "bg": "#f6ebff"},
    sly.Point: {"icon": "zmdi zmdi-dot-circle-alt", "color": "#899aff", "bg": "#edeeff"},
}

UNKNOWN_ICON = {"icon": "zmdi zmdi-shape", "color": "#ea9d22", "bg": "#fcefd9"}


def init_data_and_state(api: sly.Api):
    global ORIGINAL_META

    data = {}
    state = {}
    state["selectors"] = {}
    table = []

    meta_json = api.project.get_meta(PROJECT_ID)
    ORIGINAL_META = sly.ProjectMeta.from_json(meta_json)

    for obj_class in ORIGINAL_META.obj_classes:
        obj_class: sly.ObjClass
        row = {
            "name": obj_class.name,
            "color": sly.color.rgb2hex(obj_class.color),
            "shape": obj_class.geometry_type.geometry_name(),
            "shapeIcon": SHAPE_TO_ICON.get(obj_class.geometry_type, UNKNOWN_ICON)
        }

        possible_shapes = [{"value": REMAIN_UNCHANGED, "label": REMAIN_UNCHANGED}]
        transforms = obj_class.geometry_type.allowed_transforms()
        for g in transforms:
            possible_shapes.append({"value": g.geometry_name(), "label": g.geometry_name()})

        sly.logger.debug("{!r} -> {}".format(obj_class.geometry_type.geometry_name(), possible_shapes))

        row["convertTo"] = possible_shapes
        state["selectors"][obj_class.name] = REMAIN_UNCHANGED
        table.append(row)

    data["table"] = table
    data["projectId"] = PROJECT_ID

    project = api.project.get_info_by_id(PROJECT_ID)
    data["projectName"] = project.name
    data["projectPreviewUrl"] = api.image.preview_url(project.reference_image_url, 100, 100)
    return data, state