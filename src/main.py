import globals as g
import supervisely_lib as sly
from supervisely_lib.video_annotation.key_id_map import KeyIdMap
from supervisely_lib.annotation.json_geometries_map import GET_GEOMETRY_FROM_STR


def convert_annotation(ann: sly.Annotation, dst_meta):
    new_labels = []
    for lbl in ann.labels:
        new_cls = dst_meta.obj_classes.get(lbl.obj_class.name)
        if lbl.obj_class.geometry_type == new_cls.geometry_type:
            new_labels.append(lbl)
        else:
            converted_labels = lbl.convert(new_cls)
            new_labels.extend(converted_labels)
    return ann.clone(labels=new_labels)


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
