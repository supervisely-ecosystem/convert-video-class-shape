<div align="center" markdown> 
<img src="https://user-images.githubusercontent.com/106374579/183414846-10e2d52b-6e85-4f25-bc46-14fe045c5018.png"/>


# Convert Video Classes Shape



<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#Preparation">Preparation</a> •
  <a href="#How-To-Run">How To Run</a> •
  <a href="#How-To-Use">How To Use</a>
</p>


[![](https://img.shields.io/badge/supervisely-ecosystem-brightgreen)](https://ecosystem.supervisely.com/apps/supervisely-ecosystem/convert-video-class-shape)
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervisely.com/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/convert-video-class-shape)
[![views](https://app.supervisely.com/img/badges/views/supervisely-ecosystem/convert-video-class-shape.png)](https://supervisely.com)
[![runs](https://app.supervisely.com/img/badges/runs/supervisely-ecosystem/convert-video-class-shape.png)](https://supervisely.com)

</div>

## Overview 
It is often needed to convert labeled objects from one geometry to another while doing computer vision reseach. There are huge number of scenarios , here are some examples:
- you labeled data with polygons to train semantic segmentation model, and then you decided to try detection model. Therefore you have to convert your labels from polygons to rectangles (bounding boxes)
- or you applied neural network to videos and it produced pre-annotations as bitmaps (masks). Then you want to transform them to polygons for manual correction.

This app covers following transformations:
- from `Bitmap` to `Polygon`, `Rectangle` and `AnyShape`
- from `Polygon` to `Rectangle`, `Bitmap` and `AnyShape`
- from `Polyline` to `Rectangle`, `Bitmap`, `Polygon`, `AnyShape`
- from `Rectangle` to `Polygon`, `Bitmap` and `AnyShape`
- from `Point` to `AnyShape`
- `Cuboid`, `Cuboid3d`, `Pointcloud` (segmentation of point clouds), `Point3d`, `Graph` are not supported yet (send us a feature request if you need it)

**Notes:**

- Your data is safe: app creates new project with modified figures and objects. The original project remains unchanged
- Note: transformation from raster (bitmap) to vector (polygon) will result in huge number of points. App performs approximation to reduce the number. That can lead to slight loss of accuracy at borders. Special settings to control approximation will be released in next version.

## How To Run

### Step 1: Run from context menu of project

Go to "Context Menu" (videos project) -> "Run App" -> "Transform" -> "Convert Video Class Shape"

<img src="https://i.imgur.com/gqh7ORk.png" width="800"/>

### Step 2:  Waiting until the app is started
Once app is started, new task appear in workspace tasks. Wait message `Application is started ...` (1) and then press `Open` button (2).

<img src="https://i.imgur.com/9f4v4KD.png"/>

### Step 3: Define transformations

App contains 3 sections: information about input project, information about output and the list of all classes from input project. In column `CONVERT TO` there are dropdown lists in front of each class (row of the table). You have to define transformations for classes of interest. 

Default `remain unchanged` option is selected and means that class and all its objects will be copied without modification to a new project. Dropdown lists only contain allowed shapes (see <a href="#Overview">Overview</a>), for example `Rectangle` can not be transformed to `Polyline` or `Point`. 

<img src="https://i.imgur.com/rdj3OvN.png"/>

### Step 4: Press RUN button and wait

Press `Run` button. The progress bas will appear in `Output` section. Also you can monitor progress from tasks list of the current workspace.

<img src="https://i.imgur.com/kdYwkde.png" width="600"/>

App creates new project and it will appear in `Output` section.

<img src="https://i.imgur.com/YjVtbYA.png" width="600"/>

### Step 5: App shuts down automatically

Even if app is finished, you can always use it as a history: open it from tasks list in `Read Only` mode to check Input project, list of applied transformations and Output project. 
