import globals as g
import supervisely_lib as sly
from supervisely_lib.video_annotation.key_id_map import KeyIdMap
from supervisely_lib.annotation.json_geometries_map import GET_GEOMETRY_FROM_STR


def convert_annotation(ann: sly.VideoAnnotation, dst_meta):

    frames = []
    new_objects = {}

    for curr_object in ann.objects:
        curr_obj_class = curr_object.obj_class
        new_obj_class = dst_meta.obj_classes.get(curr_obj_class.name)
        if curr_obj_class.geometry_type == new_obj_class.geometry_type:
            new_objects[curr_object._key] = curr_object
        else:
            new_object = sly.VideoObject(obj_class=new_obj_class, tags=curr_object.tags)
            new_objects[curr_object._key] = new_object

    for curr_frame in ann.frames:
        new_frame_figures = []
        for curr_figure in curr_frame.figures:
            curr_figure_obj_class = curr_figure.video_object.obj_class
            new_obj_class = dst_meta.obj_classes.get(curr_figure_obj_class.name)
            if curr_figure_obj_class.geometry_type == new_obj_class.geometry_type:
                new_frame_figures.append(curr_figure)
            else:
                new_geometries = curr_figure.geometry.convert(new_obj_class.geometry_type)
                for new_geometry in new_geometries:
                    new_figure = curr_figure.clone(video_object=new_objects[curr_figure.video_object._key], geometry=new_geometry)
                    new_frame_figures.append(new_figure)
        new_frame = sly.Frame(curr_frame.index, new_frame_figures)
        frames.append(new_frame)

    new_frames_collection = sly.FrameCollection(frames)
    new_objects = sly.VideoObjectCollection(list(new_objects.values()))

    return ann.clone(objects=new_objects, frames=new_frames_collection)


@g.my_app.callback("convert")
@sly.timeit
def convert(api: sly.Api, task_id, context, state, app_logger):
    api.task.set_field(task_id, "data.started", True)
    src_project = api.project.get_info_by_id(g.PROJECT_ID)

    src_meta_json = api.project.get_meta(src_project.id)
    src_meta = sly.ProjectMeta.from_json(src_meta_json)

    new_classes = []
    need_action = False
    selectors = state["selectors"]
    for cls in src_meta.obj_classes:
        cls: sly.ObjClass
        dest = selectors[cls.name]
        if dest == g.REMAIN_UNCHANGED:
            new_classes.append(cls)
        else:
            need_action = True
            new_classes.append(cls.clone(geometry_type=GET_GEOMETRY_FROM_STR(dest)))

    if need_action is False:
        fields = [
            {
                "field": "state.showWarningDialog",
                "payload": True
            },
            {
                "field": "data.started",
                "payload": False,
            }
        ]
        api.task.set_fields(task_id, fields)
        return

    dst_project = api.project.create(src_project.workspace_id, src_project.name + "(new shapes)",
                                     type=sly.ProjectType.VIDEOS,
                                     description="new shapes",
                                     change_name_if_conflict=True)
    sly.logger.info('Destination project is created.',
                    extra={'project_id': dst_project.id, 'project_name': dst_project.name})
    dst_meta = src_meta.clone(obj_classes=sly.ObjClassCollection(new_classes))
    api.project.update_meta(dst_project.id, dst_meta.to_json())

    total_progress = api.project.get_images_count(src_project.id)
    current_progress = 0
    ds_progress = sly.Progress('Processing:', total_cnt=total_progress)
    for ds_info in api.dataset.get_list(src_project.id):
        dst_dataset = api.dataset.create(dst_project.id, ds_info.name)

        key_id_map = KeyIdMap()
        vid_infos_all = api.video.get_list(ds_info.id)
        for vid_info in vid_infos_all:
            vid_name = vid_info.name
            vid_id = vid_info.id
            vid_hash = vid_info.hash

            ann_info = api.video.annotation.download(vid_id)
            ann = sly.VideoAnnotation.from_json(ann_info, src_meta, key_id_map)
            new_ann = convert_annotation(ann, dst_meta)

            new_vid_info = api.video.upload_hash(dst_dataset.id, vid_name, vid_hash)
            new_vid_id = new_vid_info.id
            api.video.annotation.append(new_vid_id, new_ann, key_id_map=key_id_map)

            current_progress += len(vid_infos_all)
            api.task.set_field(task_id, "data.progress", int(current_progress * 100 / total_progress))
            ds_progress.iter_done_report()

    api.task.set_output_project(task_id, dst_project.id, dst_project.name)

    # to get correct "reference_image_url"
    res_project = api.project.get_info_by_id(dst_project.id)
    fields = [
        {
            "field": "data.resultProject",
            "payload": dst_project.name,
        },
        {
            "field": "data.resultProjectId",
            "payload": dst_project.id,
        },
        {
            "field": "data.resultProjectPreviewUrl",
            "payload": api.image.preview_url(res_project.reference_image_url, 100, 100),
        }

    ]
    api.task.set_fields(task_id, fields)
    g.my_app.stop()


def main():
    api = sly.Api.from_env()
    data, state = g.init_data_and_state(api)

    data["started"] = False
    data["progress"] = 0
    data["resultProject"] = ""

    state["showWarningDialog"] = False
    # state["showFinishDialog"] = False

    # Run application service
    g.my_app.run(data=data, state=state)


if __name__ == "__main__":
    sly.main_wrapper("main", main)
