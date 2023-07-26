#!/usr/bin/env python3
import argparse
import os
import re
import subprocess

# =============================================================================

COLORS = {
    "board":      ( 51,  43,  22, 255),
    "copper":     (179, 156,   0, 255),
    "soldermask": ( 20,  51,  36, 200),
    "silkscreen": (230, 230, 230, 255),
    "paste":      (128, 128, 128, 255),
}

# =============================================================================


def generate_gerbv_project(file, gerbers, layer, show_paste=False):

    def write_layer(fp, file_name, idx, color, is_inverted=False):
        fp.write("(define-layer! {} (cons 'filename \"{}\")\n".format(
            idx, file_name))

        if is_inverted:
            fp.write("\t(cons 'inverted #t)\n")

        _color = [x * 256 for x in color[:3]]
        _alpha = color[3] * 256
            
        fp.write("\t(cons 'visible #t)\n")
        fp.write("\t(cons 'color #({} {} {}))\n".format(*_color))
        fp.write("\t(cons 'alpha #({}))\n".format(_alpha))
        fp.write(")\n")

    # Compile the Gerbv project file
    with open(file, "w") as fp:
        layer_idx = 0

        # Prologue
        fp.write("(gerbv-file-version! \"2.0A\")\n")

        # Board outline
        if "Edge_Cuts" in gerbers:
            write_layer(fp, gerbers["Edge_Cuts"], layer_idx, (0, 0, 0, 255))
            layer_idx += 1

        # Drill layers
        for l in ("PTH", "NPTH"):
            if l in gerbers:
                write_layer(fp, gerbers[l], layer_idx, (0, 0, 0, 255))
                layer_idx += 1

        # For top and bottom overlay mask/paste/silkscreen
        if layer in ("F_Cu", "B_Cu"):
            prefix = layer[0]

            # Paste
            l = "{}_Paste".format(prefix)
            if l in gerbers and show_paste:
                write_layer(fp, gerbers[l], layer_idx, COLORS["paste"])
                layer_idx += 1

            # Silkscreen
            l = "{}_Silkscreen".format(prefix)
            if l in gerbers:
                write_layer(fp, gerbers[l], layer_idx, COLORS["silkscreen"])
                layer_idx += 1
            
            # Soldermask
            l = "{}_Mask".format(prefix)
            if l in gerbers:
                write_layer(fp, gerbers[l], layer_idx, COLORS["soldermask"], True)
                layer_idx += 1
           
        # Copper layer
        write_layer(fp, gerbers[layer], layer_idx, COLORS["copper"])
        layer_idx += 1

        # Eplilogue
        bk_color = [x * 256 for x in COLORS["board"][:3]]

        fp.write("(define-layer! -1 (cons 'filename \"\")\n")
        fp.write("\t(cons 'color #({} {} {}))\n".format(*bk_color))
        fp.write(")\n")
        fp.write("(set-render-type! 3)\n")

# =============================================================================


def find_gerber_files(path):
    gerbers = {}

    # Search for gerber files
    for file in sorted(os.listdir(path)):
        
        # Match against regex, decode fields from file name
        match = re.match("(.*)-(\w+).(\w+)$", file)
        if match is None:
            continue

        project = match.group(1)
        layer = match.group(2)
        ext = match.group(3).lower()

        # Reject non-gerber files
        if re.match("g[tb][opsl]|g\d+|gm\d+|drl", ext) is None:
            continue
        #print(project, layer, ext)

        print("Found '{}'".format(file))

        # Store
        if project not in gerbers:
            gerbers[project] = {}
        
        gerbers[project][layer] = os.path.join(path, file)

    return gerbers

# =============================================================================


def main():

    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "path",
        type=str,
        help="Path to gerber files")
    parser.add_argument(
        "--format",
        type=str,
        default="png",
        help="Export format (png|pdf|ps|svg def. png)")
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Board resolution as DPI (def. 300)")
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output path (def. gerber path)")
    parser.add_argument(
        "--gerbv",
        type=str,
        default="/usr/local/bin/gerbv",
        help="Path to Gerbv binary (def. '/usr/local/bin/gerbv')")
    parser.add_argument(
        "--show-paste",
        action="store_true",
        help="Enables showing of paste layers")

    args = parser.parse_args()

    # Find gerber files
    all_gerbers = find_gerber_files(args.path)

    # Generate gerbv projects
    gvp_files = []
    for project, gerbers in all_gerbers.items():

        # A helper func
        def write_gvp(layer_id, layer_name):
            file_name = "{}-{}.gvp".format(project, layer_name)
            print("Writing '{}'".format(file_name))
            file_name = os.path.join(args.path, file_name)

            generate_gerbv_project(file_name, gerbers, layer_id, args.show_paste)
            return file_name

        # Top
        if "F_Cu" in gerbers:
            gvp_files.append(write_gvp("F_Cu", "top"))
        
        # Bottom
        if "B_Cu" in gerbers:
            gvp_files.append(write_gvp("B_Cu", "bot"))

        # Intermediate layers
        for i in range(2, 32):
            layer_id   = "In{}_Cu".format(i-1)
            layer_name = "in{}".format(i-1)
            if layer_id in gerbers:
                gvp_files.append(write_gvp(layer_id, layer_name))

    # Use Gerbv to visualize PCBs
    for gvp_file in gvp_files:
        img_file = gvp_file.replace(".gvp", ".{}".format(args.format))

        if args.output is not None:
            img_file = os.path.join(args.output, os.path.basename(img_file))

        gvb_args = [
            args.gerbv,
            "--dpi={}".format(args.dpi),
            "--antialias",
            "--export={}".format(args.format),
            "--project={}".format(gvp_file),
            "--output={}".format(img_file),
        ]

        print("Generating '{}' ...".format(os.path.basename(img_file)))

        # Invoke Gerbv
        p = subprocess.Popen(gvb_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        p.wait()

        if p.returncode != 0:
            print(" ERROR! Gerbv failed with {}!".format(p.returncode))

# =============================================================================


if __name__ == "__main__":
    main()
