import numpy as np

from utils import get_color, save_image, get_camera_coordinate_system, \
    get_camera_coordinate_system_wiki
from helper_classes import Ray
from ray_tracer_parser import get_args, parse_scene


def render_scene(scene, height, width):
    camera, settings, surfaces, lights = scene
    max_depth = settings.max_depth
    vx, vy, vz = get_camera_coordinate_system(camera)
    vy = -vy
    # vx, vy, vz = get_camera_coordinate_system_wiki(camera)
    # camera sizes
    screen_width = camera.screen_width
    screen_height = screen_width * height / width
    viewport_center = camera.position + vz * camera.screen_distance
    initial_pixel = viewport_center - vx * screen_width / 2 - vy * screen_height / 2
    # directions
    dx = vx * screen_width / width
    dy = vy * screen_height / height
    # new until here
    image = np.zeros((height, width, 3))
    for i in range(height):
        for j in range(width):
            pixel = initial_pixel + dx * j + dy * i
            ray = Ray(camera.position, pixel-camera.position)
            intersect_out = ray.nearest_intersected_surface(surfaces)
            if intersect_out is not None:
                hitObj, hitP = intersect_out
                color = get_color(scene, hitObj, hitP, ray, max_depth, 0)
            else:
                color = settings.background
            # We clip the values between 0 and 1 so all pixel values will make sense.
            image[i, j] = color
    image = np.clip(image, 0.0, 1.0)
    return image


def main():
    args = get_args()
    camera, settings, surfaces, lights = parse_scene(args[0])
    width, height = args[1], args[2]
    image = render_scene((camera, settings, surfaces, lights), height, width)
    save_image(image)


if __name__ == '__main__':
    main()