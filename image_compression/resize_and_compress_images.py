""" Functions to Resize and Compress Images
    - single images
    - list of images
    - multiprocessing
"""
import os
from PIL import Image
import traceback
from multiprocessing import Process, Manager
import io

from utils import slice_generator


def aspect_preserving_max_side_resize(img, max_side):
    """ Resize image object to the largest side having
        'max_side' number of pixels while preserving the aspect ratio
    """
    if any([x > max_side for x in img.size]):
        img.thumbnail(size=[max_side, max_side], resample=1)


def save_and_compress_image(img, output_bytes, quality=None):
    """ Compress image object (only JPEG) """
    if (quality is not None) and (img.format == 'JPEG'):
        img.save(output_bytes, quality=quality, format="JPEG")
    else:
        img.save(output_bytes, format="JPEG")


def resize_and_compress_single_image(
        image_path,
        max_pixel_of_largest_side=None,
        save_quality=None):
    """ Resize and compress a single image and return Byte object """
    # Read the file from disk
    with open(image_path, 'rb') as f:
        img = Image.open(io.BytesIO(f.read()))
        # resize if necessary
        if max_pixel_of_largest_side is not None:
            aspect_preserving_max_side_resize(img, max_pixel_of_largest_side)
        # Save to Bytes and Change quality (only for JPEG)
        bytes_obj = io.BytesIO()
        save_and_compress_image(img, bytes_obj, save_quality)
        readable_bytes = io.BytesIO(bytes_obj.getvalue())
    return readable_bytes


def resize_and_compress_list_of_images(
        image_path_list,
        results_dict,
        process_id=None,
        max_pixel_of_largest_side=None,
        save_quality=None):
    """ Compress a list of images """
    if process_id is not None:
        print("Starting process: {:2}".format(process_id))
    for image_path in image_path_list:
        try:
            img_bytes = resize_and_compress_single_image(
                            image_path,
                            max_pixel_of_largest_side,
                            save_quality)
            results_dict[image_path] = img_bytes
        except:
            print("Failed to compress: {}".format(image_path))
            results_dict[image_path] = ''
    if process_id is not None:
        print("Finished process: {:2}".format(process_id))


def process_images_list_multiprocess(
        image_source_list,
        image_process_function,
        n_processes=4,
        **kwargs):
    """ Processes a list of images using multiprocessing
        Arguments:
        ----------
        image_source_list (list):
            list of source image paths
        image_process_function (func):
            a function to process images, takes as input:
            pid (int), image_source_list, image_dest_list,
            status_messages (dict), additional keyword arguments
        n_processes (int): the number of processes to use
    """
    n_records = len(image_source_list)
    n_processes = min(n_processes, n_records)
    # Shared dictionary to store results
    manager = Manager()
    results_dict = manager.dict()
    for image_source in image_source_list:
        results_dict[image_source] = ''
    try:
        processes_list = list()
        slices = slice_generator(n_records, n_processes)
        for i, (start_i, end_i) in enumerate(slices):
            pr = Process(target=image_process_function,
                         args=(image_source_list[start_i:end_i],
                               results_dict, i),
                         kwargs=kwargs)
            pr.start()
            processes_list.append(pr)
        for p in processes_list:
            p.join()
    except Exception:
        print(traceback.format_exc())

    # convert result to a list
    results_list = list()
    for image_source in image_source_list:
        results_list.append(results_dict[image_source])

    return results_list

#
# if __name__ == '__main__':
#     image_root = 'D:\\Studium_GD\\Zooniverse\\Data\\snapshot_serengeti\\test_images\\'
#     img_names = os.listdir(image_root)
#     image_path_list = [os.path.join(image_root, x) for x in img_names]
#     max_pixel_of_largest_side = 1440
#     save_quality = None
#
#     tt = process_images_list_multiprocess(
#             image_path_list,
#             resize_and_compress_list_of_images,
#             max_pixel_of_largest_side=max_pixel_of_largest_side,
#             save_quality=save_quality)
