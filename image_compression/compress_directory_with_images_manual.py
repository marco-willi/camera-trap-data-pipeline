""" Compress a directory of images
    - input: a directory containing images
    - output: a different directory with compressed images
"""
import re
import os
import sys
from PIL import Image
from collections import OrderedDict

###############################
# Parameter
###############################

args = dict()
args['input_image_dir'] = 'C:\\my_images\\'
args['output_image_dir'] = 'C:\\my_compressed_images\\'
args['max_image_pixel_side'] = 1440
args['image_quality'] = 50
args['image_types'] = 'jpg|jpeg|png'


###############################
# Image Compression
###############################

def compress_images(image_source_list,
                    image_dest_list,
                    save_quality=None,
                    max_pixel_of_largest_side=None):
    """ Compresses images for use with multiprocessing

        Arguments:
        -----------
        image_source_list (list):
            image source paths
        image_source_list (list):
            image destination paths
        save_quality (int):
            compression quality of images
        max_pixel_of_largest_side (int):
            max allowed size in pixels of largest side of an image,
            if an image exceeds this, its largest side is resized to this
            while preserving the aspect ratio
    """
    # Check Input
    assert any([save_quality, max_pixel_of_largest_side]) is not None,\
        "At least one of save_quality or max_pixel_of_largest_side must be \
         specified"
    if save_quality is not None:
        assert (save_quality <= 100) and (save_quality > 0), \
            "save_quality must be between 1 and 100"
    # Loop over all images and process each
    counter = 0
    n_tot = len(image_source_list)
    for source, dest in zip(image_source_list, image_dest_list):
        if (counter % 2000) == 0:
            print("Done %s/%s" % (counter, n_tot))
            sys.stdout.flush()
        try:
            img = Image.open(source)
            # Check largest side of image and resize if necessary
            if max_pixel_of_largest_side is not None:
                if any([x > max_pixel_of_largest_side for x in img.size]):
                    img.thumbnail(size=[max_pixel_of_largest_side,
                                        max_pixel_of_largest_side],
                                  resample=1)
            if save_quality is not None:
                img.save(dest, "JPEG",
                         quality=save_quality)
            else:
                img.save(dest)
            img.close()
            # save result "Successful Compression"
        except:
            # save result "Not Compressed"
            print("Failed to compress %s" % source)
        counter += 1
    # Print process end status
    print("Finished")


def find_images_in_dir(dirpath, ext='jpg|jpeg'):
    """ get all files in dirpath with ending """
    all = os.listdir(dirpath)
    all_files = [x for x in all if os.path.isfile(os.path.join(dirpath, x))]
    all_images = [x for x in all_files if
                  re.match(r'([\w-]+\.(?:' + ext + '))', x, re.IGNORECASE)]
    return all_images


for k, v in args.items():
    print("Argument %s: %s" % (k, v))

# Check Inputs
if not os.path.isdir(args['input_image_dir']):
    raise FileNotFoundError("input_image_dir: %s is not a directory" %
                            args['input_image_dir'])

if not os.path.isdir(args['output_image_dir']):
    raise FileNotFoundError("output_image_dir: %s is not a directory" %
                            args['output_image_dir'])

if args['input_image_dir'] == args['output_image_dir']:
    raise ValueError("input_image_dir is the same as output_image_dir,\
                      must be different")

if not ((args['image_quality'] > 0) and (args['image_quality'] <= 100)):
    raise ValueError("image_quality has to be between 1 and 100")

# Read Season Captures CSV
image_names = find_images_in_dir(args['input_image_dir'], args['image_types'])

print("Found %s images in %s" %
      (len(image_names), args['input_image_dir']))

# Define source and destination paths for all images
images = OrderedDict()
n_duplicates = 0
for img in image_names:
    images[img] = {
        'source': os.path.join(args['input_image_dir'], img),
        'dest': os.path.join(args['output_image_dir'], img)
        }

# Create source and destination lists
image_source_path_list = list()
image_dest_path_list = list()

for value in images.values():
    image_source_path_list.append(value['source'])
    image_dest_path_list.append(value['dest'])

compress_images(
    image_source_list=image_source_path_list,
    image_dest_list=image_dest_path_list,
    save_quality=args['image_quality'],
    max_pixel_of_largest_side=args['max_image_pixel_side'])
