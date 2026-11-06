# Aly's Guide to PlanT2.0

To get this bad boy working:
- I made some changes to the code
- I loaded the weights to CPU first instead of GPU
- I obv. followed the README
- Had to run Carla with `-quality-level=Low and -RenderOffScreen`
- Made `export.sh` and `run.sh` for convenienve
- Used pip instead of conda, see requirements.txt for details
- Measured memory

## To do it yourself:

- Set up a venv
- Follow the repo README but also:
    - Install requirements with pip
    - fill out export.sh
- `source export.sh`
- `./run.sh`
- `/path/to/CarlaUE4.sh -quality-level=Low -RenderOffScreen`
- `python carla_camera_viewer.py`
- Enjoy.
