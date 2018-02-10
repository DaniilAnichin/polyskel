import logging
import argparse
import re
from PIL import Image, ImageDraw  # flake8: noqa
import polyskel

import matplotlib.pyplot as plt
import numpy as np

from math import cos, pi
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def graph_parallelepiped(points: list, ax, color: str) -> None:
    """"""
    points = np.array(points)

    length = len(points) // 2
    p1 = points[:length]
    p2 = points[length:]

    verts = [p1, p2]
    for i, p in enumerate(p1):
        verts.append([p, p1[(i + 1) % length], p2[(i + 1) % length], p2[i]])

    # Plot vertices
    ax.scatter3D(points[:, 0], points[:, 1], points[:, 2])
    # Remove axis
    ax.set_axis_off()
    # plot sides
    ax.add_collection3d(Poly3DCollection(verts, facecolors=color, linewidths=1, edgecolors='black'))


def ccw(a: np.array, b: np.array, c: np.array) -> bool:
    """
    Tests whether the turn formed by a, b, and c is clockwise.
    If points on the same line returns True in any case!!!
    """
    d1 = b - a
    d2 = c - a
    return d1[0] * d2[1] <= d1[1] * d2[0]


def simple_skeleton(points: np.array, stepback: float) -> list:
    length = len(points)
    result = []

    for i, point in enumerate(points):
        prev_side = points[i - 1] - point
        next_side = points[(i + 1) % length] - point
        bisector = prev_side / np.linalg.norm(prev_side) + next_side / np.linalg.norm(next_side)
        bisector *= stepback
        if not ccw(points[i - 1], point, points[(i + 1) % length]):
            bisector *= -1
        result.append(point + bisector)

    return result


def reverse(points: list, upper_points: list) -> bool:
    for i, (point, upper_point) in enumerate(zip(points, upper_points)):
        sec = (upper_points[i - 1] - upper_point)
        if not np.linalg.norm(sec):
            continue
        if any((points[i - 1] - point) * sec < 0):
            return True
    return False


if __name__ == "__main__":
    logging.basicConfig()

    argparser = argparse.ArgumentParser(description="Construct the straight skeleton of a polygon. The polygon is to be given as a counter-clockwise series of vertices specified by their coordinates: see the example files for the exact format.")
    argparser.add_argument('polygon_file', metavar="<polygon-file>", type=argparse.FileType('r'), help="text file describing the polygon ('-' for standard input)")
    argparser.add_argument('--verbose', '--v', action="store_true", default=False, help="Show construction of the skeleton")
    argparser.add_argument(
        '--log',
        dest='loglevel',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='WARNING',
        help="Set log level")
    args = argparser.parse_args()

    polyskel.log.setLevel(getattr(logging, args.loglevel))
    polygon_line_pat = re.compile(r"\s*(?P<coord_x>\d+(\.\d+)?)\s*,\s*(?P<coord_y>\d+(\.\d+)?)\s*(#.*)?")

    contours = []
    poly = []
    for line in args.polygon_file:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        if line.startswith('-'):
            contours.append(poly)
            poly = []
            continue

        match = polygon_line_pat.match(line)
        poly.append((float(match.group("coord_x")), float(match.group("coord_y"))))

    if not args.polygon_file.isatty():
        args.polygon_file.close()

    contours.append(poly)
    poly = contours[0]
    holes = contours[1:] if len(contours) > 0 else None
    bbox_end_x = int(max(poly, key=lambda x: x[0])[0]+20)
    bbox_end_y = int(max(poly, key=lambda x: x[1])[1]+20)

    # TODO New approach of half-skeleton

    skeleton = polyskel.skeletonize(poly, holes)
    contour = polyskel._normalize_contour(poly)

    poly = [np.array(pair) for pair in poly]
    length = len(poly)
    base_points = list(np.append(poly, np.ones((length, 1)) * 0, axis=1))

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_zlim(0, 100)

    heights = [9, 15]
    cotangents = [cos(15 * pi / 180), cos(60 * pi / 180)]

    steps = []
    prev_ccw = None
    for i, p in enumerate(poly):
        print('Checking %d ' % i)
        prev = poly[i - 1]
        if prev_ccw is None:
            prev_ccw = ccw(poly[i - 2], prev, p)
        this_ccw = ccw(prev, p, poly[(i + 1) % length])
        if this_ccw and prev_ccw:
            print('The oscar goes to...')
            steps.append(np.linalg.norm(p - prev))
        prev_ccw = this_ccw

    max_stepback = min(steps) / 2
    min_height = 0
    cotangent = np.random.random() * (cotangents[1] - cotangents[0]) + cotangents[0]
    cotangent = 1
    print(max_stepback / cotangent)
    print((heights[1] - max_stepback / cotangent))
    height = max_stepback / cotangent - 2
    # height = np.random.random() * (2 ** 0.5 - max_stepback / cotangent) + max_stepback / cotangent

    stepback = (height - min_height) / cotangent
    simple_skull = simple_skeleton(poly, height)

    if reverse(poly, simple_skull):
        print('Shit no, it\'s reversed !!1!')

    upper_points = list(np.append(simple_skull, np.ones((length, 1)) * height, axis=1))
    print(height)
    # for arc in skeleton:
    #     print(arc)
    #     height = 0
    #     for sink in arc.sinks:
    #         if sink in contour:
    #             index = contour.index(sink)
    #             upper_ponts[index] = [arc.source.x, arc.source.y]
    #             heights[index] = arc.height * angle_ratio
    #             heights[index] = np.linalg.norm(np.array([arc.source.x - sink.x, arc.source.y - sink.y])) * angle_ratio

    graph_parallelepiped(base_points + upper_points, ax, 'yellow')
    plt.show()

    #
    # im = Image.new("RGB", (bbox_end_x, bbox_end_y), "white")
    # draw = ImageDraw.Draw(im)
    # if args.verbose:
    #     polyskel.set_debug((im, draw))
    #
    # for contour in contours:
    #     for point, next in zip(contour, contour[1:]+contour[:1]):
    #         draw.line((point[0], point[1], next[0], next[1]), fill=0)
    # print(poly)
    # print(holes)
    # skeleton = polyskel.skeletonize(poly, holes)
    #
    # for arc in skeleton:
    #     print(arc)
    #     for sink in arc.sinks:
    #         color = 'red' if sink not in polyskel._normalize_contour(poly) else 'blue'
    #         draw.line((arc.source.x, arc.source.y, sink.x, sink.y), fill=color)
    #
    # im.show()
