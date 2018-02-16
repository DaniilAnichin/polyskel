import argparse
import logging
import re
from PIL import Image, ImageDraw
from euclid import Line2

import polyskel


def get_args():
    parser = argparse.ArgumentParser(
        description='Construct the straight skeleton of a polygon.'
                    'The polygon is to be given as a counter-clockwise '
                    'series of vertices specified by their coordinates:'
                    'see the example files for the exact format.')
    parser.add_argument(
        'polygon_file', metavar='<polygon-file>', type=argparse.FileType('r'),
        help='text file describing the polygon ("-" for standard input)')
    parser.add_argument(
        '--verbose', '--v', action='store_true', default=False,
        help='Show construction of the skeleton')
    parser.add_argument(
        '--log', dest='loglevel', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='WARNING',
        help='Set log level')
    parser.add_argument(
        '--reverse', '-r', dest='reverse', action='store_true', default=False,
        help='Reverse dots order')
    return parser.parse_args()


def draw_contours(draw, *contours: list) -> None:
    for contour in contours:
        for point, next_point in zip(contour, contour[1:] + contour[:1]):
            draw.line((point[0], point[1], next_point[0], next_point[1]), fill=0)


def draw_skeleton(draw, skeleton: list, polygon: list, mark_leaves: bool=True) -> None:
    min_leaf = None
    for arc in skeleton:
        print('Arc: ', arc)
        for sink in arc.sinks:
            if mark_leaves and sink in polygon:
                color = 'blue'
                distance = arc.source.distance(sink) * 0.707106781186
                min_leaf = min(min_leaf or distance, distance)
            else:
                color = 'red'
            draw.line((arc.source.x, arc.source.y, sink.x, sink.y), fill=color)

    print('Min leaf is')
    print(min_leaf)


def get_polygon_from_file(polygon_file, reverse: bool=False) -> tuple:
    polygon_line_pat = re.compile(r"\s*(?P<coord_x>\d+(\.\d+)?)\s*,\s*(?P<coord_y>\d+(\.\d+)?)\s*(#.*)?")

    print(reverse)
    print(type(reverse))
    contours = []
    poly = []
    for line in polygon_file:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        if line.startswith('-'):
            contours.append(poly)
            poly = []
            continue

        match = polygon_line_pat.match(line)
        pair = (float(match.group("coord_x")) + 50, float(match.group("coord_y")) + 50)
        if reverse:
            poly.insert(0, pair)
        else:
            poly.append(pair)

    if not polygon_file.isatty():
        polygon_file.close()

    contours.append(poly)
    return contours[0], contours


def main():
    args = get_args()

    logging.basicConfig()
    polyskel.log.setLevel(getattr(logging, args.loglevel))

    poly, contours = get_polygon_from_file(args.polygon_file, reverse=args.reverse)
    holes = contours[1:] if len(contours) > 0 else None

    bbox_end_x = int(max(poly, key=lambda x: x[0])[0]+100)
    bbox_end_y = int(max(poly, key=lambda x: x[1])[1]+100)

    im = Image.new("RGB", (bbox_end_x, bbox_end_y), "white")
    draw = ImageDraw.Draw(im)
    if args.verbose:
        polyskel.set_debug((im, draw))

    print('Polygon: ', poly)
    print('Holes: ', holes)
    draw_contours(draw, *contours)
    draw_skeleton(draw, polyskel.skeletonize(poly, holes), polyskel._normalize_contour(poly))
    im.show()


if __name__ == "__main__":
    main()
