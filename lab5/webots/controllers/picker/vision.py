"""One downward-looking RGB camera, known horizontal top plane."""
from math import dist, tan


def detect(bgra, width, height, color):
    if len(bgra) != width * height * 4 or width <= 0 or height <= 0:
        raise ValueError('Invalid BGRA buffer')
    if color not in ('red', 'green'):
        raise ValueError('Unknown target color')
    sx = sy = count = 0
    for i in range(width * height):
        b, g, r = bgra[4*i:4*i+3]
        a, other = (r, g) if color == 'red' else (g, r)
        if a > 90 and a > 1.45 * max(b, other):
            sx += i % width
            sy += i // width
            count += 1
    return (sx/count, sy/count) if count >= 4 else None


def project(pixel, width, height, fov, camera, plane_z):
    """Webots +X is optical forward; mounted with +X pointing down."""
    if not 0 < fov < 3.14 or camera[2] <= plane_z:
        raise ValueError('Invalid projection geometry')
    u, v = pixel
    scale = (camera[2] - plane_z) * 2 * tan(fov/2) / width
    return camera[0] - (v-(height-1)/2)*scale, camera[1] - (u-(width-1)/2)*scale


def fuse(points, tolerance=0.015):
    if len(points) < 2 or any(dist(a,b) > tolerance for a in points for b in points):
        raise ValueError('Insufficient or inconsistent observations')
    return tuple(sum(axis)/len(points) for axis in zip(*points))
