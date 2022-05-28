import numpy as np

from helper_classes import Camera, Settings, Material, Sphere, InfinitePlane, Light, Cube
import sys


def get_args():
    if len(sys.argv) < 2:
        print('the input text file is missing')
        sys.exit(0)
    if len(sys.argv) == 2:
        return sys.argv[1], 500, 500
    else:
        return sys.argv[1], int(sys.argv[2]), int(sys.argv[3])


def parse_scene(scene: str):
    materials = []
    surfaces = []
    lights = []
    camera = None
    settings = None

    try:
        with open(scene, 'r') as f:
            line = f.readline()
            while line != "":
                if line.startswith("#"):
                    line = f.readline()
                    continue
                else:
                    code = line[0:3].lower()
                    params = line[3:].split()
                    params = [float(param) for param in params]
                    if code == "cam":
                        camera = Camera(np.array((params[0], params[1], params[2])),
                                        np.array((params[3], params[4], params[5])),
                                        np.array((params[6], params[7], params[8])),
                                        params[9], params[10])
                    elif code == "set":
                        settings = Settings(np.array((params[0], params[1], params[2])),
                                           int(params[3]), int(params[4]))
                    elif code == "mtl":
                        material = Material(np.array((params[0], params[1], params[2])),
                                            np.array((params[3], params[4], params[5])),
                                            np.array((params[6], params[7], params[8])),
                                            params[9], params[10])
                        materials.append(material)
                    elif code == "sph":
                        sphere = Sphere(np.array((params[0], params[1], params[2])),
                                        params[3], materials[int(params[4]) - 1])
                        surfaces.append(sphere)
                    elif code == "box":
                        cube = Cube(np.array((params[0], params[1], params[2])),
                                    params[3], materials[int(params[4]) - 1])
                        surfaces.append(cube)
                    elif code == "pln":
                        plane = InfinitePlane(np.array((params[0], params[1], params[2])),
                                              params[3], materials[int(params[4]) - 1])
                        surfaces.append(plane)
                    elif code == "lgt":
                        light = Light(np.array((params[0], params[1], params[2])),
                                      np.array((params[3], params[4], params[5])),
                                      params[6], params[7], params[8])
                        lights.append(light)
                line = f.readline()
            f.close()
            return camera, settings, surfaces, lights
    except IOError:
        print("Error: File not found")
        return None, None, None, None