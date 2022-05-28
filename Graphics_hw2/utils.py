import numpy as np
from PIL import Image
from helper_classes import Light, Surface, Camera, normalize, Ray

EPSILON = 0.001


def calc_rotation_matrix_and_get_coordinates(source: np.ndarray, destination: np.ndarray):
    # get Vz vector
    toward_vector = destination - source
    vz = normalize(toward_vector)
    sx = -vz[1]
    cx = np.sqrt(1 - sx ** 2)
    sy = - vz[0] / cx
    cy = vz[2] / cx
    # build rotation matrix
    rotation_matrix = np.array([[cy, 0, sy], [-sx*sy, cx, sx*cy], [-cx*sy, -sx, cx*cy]])
    # coordinate system
    vx = rotation_matrix[0, :]
    vy = rotation_matrix[1, :]
    vz = rotation_matrix[2, :]
    return vx, vy, vz


def get_camera_coordinate_system(camera: Camera):
    return calc_rotation_matrix_and_get_coordinates(source = camera.position, destination = camera.look_at_point)


def get_camera_coordinate_system_wiki(camera: Camera):
    # get vectors that parallel to viewport
    look_at_vector = camera.look_at_point - camera.position
    right_vector = np.cross(camera.up_vector, look_at_vector)
    vz = normalize(look_at_vector)
    vx = normalize(right_vector)
    vy = np.cross(vz, vx)
    return vx, vy, vz


def distance(pt1, pt2):
    return np.linalg.norm(pt1 - pt2)


def calc_shadows(scene, light: Light, hitP):
    camera, settings, surfaces, lights = scene

    ray = Ray(hitP, light.position - hitP)
    intersect_out = ray.nearest_intersected_surface(surfaces)
    if intersect_out is not None:
        _, new_hitP = intersect_out
        if distance(hitP, new_hitP) < distance(hitP, light.position):
            return 0
    return 1


def soft_shadows(scene, light: Light, surface, hitP):
    camera, settings, surfaces, lights = scene
    N = settings.number_of_shadows_rays
    hit_rays = 0
    vx, vy, vz = calc_rotation_matrix_and_get_coordinates(light.position, hitP)
    screen_width = light.light_radius
    screen_height = light.light_radius
    center = light.position
    initial_pixel = center - vx * screen_width / 2 - vy * screen_height
    dx = vx * screen_width/N
    dy = vy * screen_height/N
    for i in range(N):
        for j in range(N):
            pixel = initial_pixel + dx * j + dy * i
            random_point = pixel+np.random.uniform(0, dx)
            random_point += np.random.uniform(0, dy)
            ray = Ray(random_point, hitP - random_point)
            intersect_out = ray.nearest_intersected_surface(surfaces)
            if intersect_out is not None:
                new_hitObj, _ = intersect_out
                if new_hitObj == surface:
                    hit_rays += 1
    ret = float(hit_rays / (N * N))
    return ret


def least_transparent(ray: Ray, new_surfaces, new_surface, surface, transparency):
    if transparency <= 0:
        return 0
    new_surfaces.remove(new_surface)
    intersect_out = ray.nearest_intersected_surface(new_surfaces)
    # if intersect_out is not None:
    new_hitObj, _ = intersect_out
    if new_hitObj == surface:
        return transparency
    else:
        transparency *= least_transparent(ray, new_surfaces, new_hitObj, surface, new_hitObj.material.transparency)
    return transparency


# calculate soft shadow + bonus with calculating all transparent surfaces that are on the way of the light ray
def transparent_soft_shadows(scene, light: Light, surface, hitP):
    camera, settings, surfaces, lights = scene
    N = settings.number_of_shadows_rays
    hit_rays = 0
    vx, vy, vz = calc_rotation_matrix_and_get_coordinates(light.position, hitP)
    screen_width = light.light_radius
    screen_height = light.light_radius
    center = light.position
    initial_pixel = center - vx * screen_width / 2 - vy * screen_height
    dx = vx * screen_width/N
    dy = vy * screen_height/N
    for i in range(N):
        for j in range(N):
            pixel = initial_pixel + dx * j + dy * i
            random_point = pixel+np.random.uniform(0, dx)
            random_point += np.random.uniform(0, dy)
            ray = Ray(random_point, hitP - random_point)
            intersect_out = ray.nearest_intersected_surface(surfaces)
            # if intersect_out is not None:
            new_hitObj, _ = intersect_out
            if new_hitObj == surface:
                hit_rays += 1
            else:
                new_surfaces = surfaces.copy()
                least = least_transparent(ray, new_surfaces, new_hitObj, surface, new_hitObj.material.transparency)
                hit_rays += least
    ret = float(hit_rays / (N * N))
    if ret < 0:
        return 0
    return ret


def get_cos_angle(vector1, vector2):
    vector1 = normalize(vector1)
    vector2 = normalize(vector2)
    return np.dot(vector1, vector2)


def reflected(vector, normal):
    return vector - 2 * np.dot(vector, normal) * normal


def get_reflected_ray(surface: Surface, point, ray: Ray):
    reflect = reflected(ray.direction, surface.get_normal(point))
    return Ray(point, reflect)


def calculate_diffuse_color(light: Light, surface: Surface, point) -> np.ndarray:
    normal_vector = surface.get_normal(point)
    light_vector = light.position - point
    cos_angle = get_cos_angle(light_vector, normal_vector)
    if cos_angle < 0:
        return np.zeros(3)
    i_p = light.color
    k_d = surface.material.diffuse
    return k_d * i_p * cos_angle


def calculate_specular_color(light: Light, surface: Surface, point, ray: Ray) -> np.ndarray:
    k_s = surface.material.specular
    i_p = light.specular_intensity * light.color
    n = surface.material.phong_spec_coefficient
    l = Ray(light.position, light.position-point)
    l_hat = reflected(l.direction, surface.get_normal(point))
    v = -1*ray.direction
    dot_product = np.dot(l_hat, v)
    if dot_product < 0:
        return k_s * i_p * np.power(dot_product, n)
    return np.zeros(3)


def get_color(scene, surface, point, ray, max_depth, curr_depth):
    camera, settings, surfaces, lights = scene
    color = np.array([0.0, 0.0, 0.0])
    # Get diffuse & specular light
    for light in lights:
        s_s = transparent_soft_shadows(scene, light, surface, point)
        light_intensity = (1-light.shadow_intensity)+light.shadow_intensity*s_s
        diffuse = calculate_diffuse_color(light, surface, point)
        specular = calculate_specular_color(light, surface, point, ray)
        # color += s_j * (diffuse + specular)
        color += light_intensity * (diffuse + specular) * (1 - surface.material.transparency)

    if curr_depth < max_depth:
        reflection_ray = get_reflected_ray(surface, point, ray)
        intersect_out = reflection_ray.nearest_intersected_surface(surfaces)
        if intersect_out is not None:
            reflect_surface, reflect_point = intersect_out
            color += get_color(scene, reflect_surface, reflect_point, reflection_ray, max_depth, curr_depth + 1) * surface.material.reflection
        else:
            color += settings.background * surface.material.reflection

    if surface.material.transparency > 0:
        transparency_surfaces = surfaces.copy()
        transparency_surfaces.remove(surface)
        intersect_out = ray.nearest_intersected_surface(transparency_surfaces)
        if intersect_out is not None:
            transparency_surface, next_point = intersect_out
            new_scene = (camera, settings, transparency_surfaces, lights)
            color += surface.material.transparency*get_color(new_scene, transparency_surface, next_point, ray, max_depth, curr_depth)
        else:
            color += settings.background * surface.material.transparency
    return color


def save_image(image_data, image_name: str = 'img'):
    Image.fromarray((image_data*255).astype(np.uint8)).save(f'{image_name}.png')
