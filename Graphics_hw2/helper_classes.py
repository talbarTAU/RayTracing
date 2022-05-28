import numpy as np

def normalize(vector):
    norm = np.linalg.norm(vector)
    if norm == 0:
       return vector
    return vector / norm

def add_error_to_vector(vector, error=1e-8):
    # add error to vector coordinate if coordinate is 0
    if vector[0] == 0:
        vector[0] = error
    if vector[1] == 0:
        vector[1] = error
    if vector[2] == 0:
        vector[2] = error
    return vector

class Ray:
    def __init__(self, origin, direction):
        self.origin = origin
        self.direction = normalize(direction)

    def nearest_intersected_surface(self, surfaces):
        nearest_surface = None
        nearest_distance = np.inf
        for surface in surfaces:
            distance = surface.intersect(self)
            if distance is not None and distance < nearest_distance:
                nearest_surface = surface
                nearest_distance = distance
        if nearest_surface is None:
            return None
        nearest_point = self.get_intersection_point(nearest_distance)
        return nearest_surface, nearest_point

    def get_intersection_point(self, t):
        return self.origin + self.direction * t

class Material:

    # diffuse, specular, reflection: (r, g, b)
    # phong_spec_coefficient: float - when high (100) - renders small and sharp specular reflections, when low (1) - renders wide and soft specular reflections
    # transparency: float - 0.0 - opaque, 1.0 - transparent
    def __init__(self, diffuse, specular, reflection, phong_spec_coefficient, transparency):
        self.diffuse = diffuse
        self.specular = specular
        self.reflection = reflection
        self.phong_spec_coefficient = phong_spec_coefficient
        self.transparency = transparency


class Surface:

    def __init__(self, material: Material):
        self.material = material

    def intersect(self, ray):
        pass

    def get_normal(self, point):
        pass


class Sphere(Surface):

    # center - (x,y,z)
    def __init__(self, center, radius, material: Material):
        super().__init__(material)
        self.center = center
        self.radius = radius

    def intersect(self, ray: Ray):
        l = self.center - ray.origin
        t_ca = np.dot(l, ray.direction)
        if t_ca < 0:
            return None
        d_2 = np.dot(l, l) - t_ca * t_ca
        if d_2 > self.radius * self.radius:
            return None
        t_hc = np.sqrt(self.radius * self.radius - d_2)
        t_1 = t_ca - t_hc
        t_2 = t_ca + t_hc
        if t_1 > 0:
            return t_1
        if t_2 > 0:
            return t_2
        return None

    def get_normal(self, point):
        return normalize(point - self.center)


class InfinitePlane(Surface):

    def __init__(self, normal, offset, material: Material):
        super().__init__(material)
        self.normal = normalize(normal)
        self.offset = offset

    def intersect(self, ray: Ray):
        dot_product =  np.dot(ray.direction, self.normal)
        if dot_product == 0:
            dot_product += 1e-8
        t = -(np.dot(ray.origin, self.normal) - self.offset) / dot_product
        if t > 0:
            return t
        return None

    def get_normal(self, point):
        return self.normal

class Cube(Surface):

    # center - (x,y,z)

    def __init__(self,center, edge_length, material: Material):
        super().__init__(material)
        self.center = center
        self.edge_length = edge_length
        self.min_corner = self.center - self.edge_length / 2
        self.max_corner = self.center + self.edge_length / 2

    def intersect(self, ray: Ray):
        ray_direction_with_error = add_error_to_vector(ray.direction)
        ray_origin = ray.origin
        if ray_direction_with_error[0] >= 0:
            t_min = (self.min_corner[0] - ray_origin[0]) / ray_direction_with_error[0]
            t_max = (self.max_corner[0] - ray_origin[0]) / ray_direction_with_error[0]
        else:
            t_min = (self.max_corner[0] - ray_origin[0]) / ray_direction_with_error[0]
            t_max = (self.min_corner[0] - ray_origin[0]) / ray_direction_with_error[0]
        if ray_direction_with_error[1] >= 0:
            t_y_min = (self.min_corner[1] - ray_origin[1]) / ray_direction_with_error[1]
            t_y_max = (self.max_corner[1] - ray_origin[1]) / ray_direction_with_error[1]
        else:
            t_y_min = (self.max_corner[1] - ray_origin[1]) / ray_direction_with_error[1]
            t_y_max = (self.min_corner[1] - ray_origin[1]) / ray_direction_with_error[1]
        if t_min > t_y_max or t_y_min > t_max:
            return None
        if t_y_min > t_min:
            t_min = t_y_min
        if t_y_max < t_max:
            t_max = t_y_max
        if ray_direction_with_error[2] >= 0:
            t_z_min = (self.min_corner[2] - ray_origin[2]) / ray_direction_with_error[2]
            t_z_max = (self.max_corner[2] - ray_origin[2]) / ray_direction_with_error[2]
        else:
            t_z_min = (self.max_corner[2] - ray_origin[2]) / ray_direction_with_error[2]
            t_z_max = (self.min_corner[2] - ray_origin[2]) / ray_direction_with_error[2]
        if t_min > t_z_max or t_z_min > t_max:
            return None
        if t_z_min > t_min:
            t_min = t_z_min
        if t_z_max < t_max:
            t_max = t_z_max
        if t_min > 0:
            return t_min
        if t_max > 0:
            return t_max
        return None

    def get_normal(self, point):
        # calculate the cube plane that the point is on
        # then return the normal of that plane
        if np.isclose(point[0], self.min_corner[0]):
            return np.array([-1, 0, 0])
        elif np.isclose(point[0], self.max_corner[0]):
            return np.array([1, 0, 0])
        elif np.isclose(point[1], self.min_corner[1]):
            return np.array([0, -1, 0])
        elif np.isclose(point[1], self.max_corner[1]):
            return np.array([0, 1, 0])
        elif np.isclose(point[2], self.min_corner[2]):
            return np.array([0, 0, -1])
        elif np.isclose(point[2], self.max_corner[2]):
            return np.array([0, 0, 1])
        else:
            # we should not get here
            return None


class Light:

    # position - (x,y,z)
    # color - (r,g,b)
    # specular_intensity - float - 1.0 - the light intensity will be the same for the diffuse component and the specular component computation.
    #                                 0.0 - the light intensity will be the same for the diffuse component computation only.
    # shadow_intensity - float - 0.0 - no shadows, 1.0 - full shadows
    def __init__(self, position ,color, specular_intensity,shadow_intensity, light_radius):
        self.position = position
        self.color = color
        self.specular_intensity = specular_intensity
        self.shadow_intensity = shadow_intensity
        self.light_radius = light_radius


class Camera:

    # position - (x,y,z)
    # look_at_point - (x,y,z)
    # up_vector - (x,y,z)
    # screen_distance - float
    # screen_width - int
    def __init__(self, position, look_at_point, up_vector, screen_distance, screen_width):
        self.position = position
        self.look_at_point = look_at_point
        self.up_vector = up_vector
        self.screen_distance = screen_distance
        self.screen_width = screen_width

class Settings:

    def __init__(self, background, number_of_shadows_rays, max_depth):
        self.background = background  # - (r,g,b)
        self.number_of_shadows_rays = number_of_shadows_rays
        self.max_depth = max_depth