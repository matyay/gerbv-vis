# Gerbv vis

This Python script allows visualizing gerber files for a PCB project using gerbv (http://gerbv.geda-project.org/). It generates a project file for gerbv which references the gerber files and then launches gerbv in headless mode to generate image files.

## Requirements

Apart from having gerbv installed the script itself relies only on built-in Python libraries.

## Usage

The only required argument is the path to a directory with gerber files.

```
usage: gerbv_vis.py [-h] [--format FORMAT] [--dpi DPI] [--output OUTPUT]
                    [--gerbv GERBV] [--show-paste]
                    path

positional arguments:
  path             Path to gerber files

optional arguments:
  -h, --help       show this help message and exit
  --format FORMAT  Export format (png|pdf|ps|svg def. png)
  --dpi DPI        Board resolution as DPI (def. 300)
  --output OUTPUT  Output path (def. gerber path)
  --gerbv GERBV    Path to Gerbv binary (def. '/usr/local/bin/gerbv')
  --show-paste     Enables showing of paste layers
```

## Gerber files discovery

The script automatically discovers gerber/drill files in the given directory. **So far it has been tested only with gerbers generated using KiCad with the "Use Protel filename extenstions" option enabled.**

The generic reognized gerber/drill file naming convention is `<project_name>-<layer_name>.<extension>`. Files for more than one project can be present in the same directory.