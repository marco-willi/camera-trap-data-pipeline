import os
import time
from PIL import Image
from shutil import copyfile


def compress_image_old(img_entry):

	if img_entry['imnum']%2000 == 500:
		approxtrem = (img_entry['totim'] - img_entry['imnum'] - 1) * (time.time()-img_entry['t0'])/(img_entry['imnum']+1)
		print("\nEstimated time remaining: " + time.strftime("%H:%M:%S",time.gmtime(approxtrem)))
		print("(Approx. "+str(img_entry['imnum'])+" out of "+str(img_entry['totim'])+" images compressed...)")

	if img_entry['invalid'] in [0,3]:
		if img_entry['absimpath'] != "NF":
			try:
				img = Image.open(img_entry['absimpath'])
				img.thumbnail(img.size)
				img.save(img_entry['comprimgpath'],"JPEG",quality=img_entry['quality'])
				img.close()
			except Exception, e:
				print e

			if os.path.isfile(img_entry['comprimgpath']):
				return "SC" #Successful compression
			else:
				return "CR" #not compressed
		else:
			return "NF" #not found
	else:
		return "IN" #invalid


def compress_image(img_entry, max_pixel_of_largest_side=None,
                   resize_type=Image.BILINEAR,
                   check_disk_size_below_KB=None):
    """ Compress image by resizing
        Arguments:
        ----------
        max_pixel_of_largest_side (int): checks width and height of an image
            and resizes the largest side to this size if either is larger,
            keeps aspect ratio
        resize_type: PIL method to resize images
        check_disk_size_below_KB (int): checks image size on disk in KB and
            omits any processing if image is below that size
    """

    if img_entry['imnum'] % 2000 == 500:
        approxtrem = (img_entry['totim'] - img_entry['imnum'] - 1) * \
                     (time.time()-img_entry['t0']) / (img_entry['imnum']+1)

        print("\nEstimated time remaining: " +
              time.strftime("%H:%M:%S", time.gmtime(approxtrem)))

        print("(Approx. " + str(img_entry['imnum']) +
              " out of " + str(img_entry['totim']) + " images compressed...)")

    if img_entry['invalid'] in [0, 3]:

        if img_entry['absimpath'] != "NF":
            try:
                image_is_processed = False

                # Check image size on disk
                if check_disk_size_below_KB is not None:
                    file_size_KB = os.path.getsize(img_entry['absimpath']) / 1024
                    if file_size_KB <= check_disk_size_below_KB:
                        copyfile(img_entry['absimpath'],
                                 img_entry['comprimgpath'])
                        image_is_processed = True

                # check if any size (width, height) is above max
                # if so, resize it to the max
                elif (not image_is_processed) and \
                     (max_pixel_of_largest_side is not None):
                    img = Image.open(img_entry['absimpath'])
                    if any([x > max_pixel_of_largest_side for x in img.size]):
                        img.thumbnail(size=[max_pixel_of_largest_side,
                                            max_pixel_of_largest_side])
                    img.save(img_entry['comprimgpath'])
                    img.close()
                    image_is_processed = True

                # Compress image by reducing quality
                else:
                    img = Image.open(img_entry['absimpath'])
                    img.thumbnail(img.size)
                    img.save(img_entry['comprimgpath'],
                             "JPEG", quality=img_entry['quality'])
                    img.close()
                    image_is_processed = True

            except Exception, e:
                print e

            # Successful compression
            if os.path.isfile(img_entry['comprimgpath']):
                return "SC"
            # not compressed
            else:
                return "CR"
        # not found
        else:
            return "NF"
    # invalid
    else:
        return "IN"


# TESTING
if __name__ == '__main__':
    example_images_path = '/home/packerc/shared/machine_learning/will5448/data/example_images/compression_issue/'
    image_files = [x for x in os.listdir(example_images_path) if '.' in x]

    image_input_paths = [''.join([example_images_path, file])
                         for file in image_files]


     max_pixel_of_largest_side=[None, 2048, 2048, 2048, 2048],
     resize_type=[Image.BILINEAR, Image.BILINEAR, PIL.Image.BICUBIC,  Image.BILINEAR]
     check_disk_size_below_KB=[None, None, None, 600]
     output_postfixes = ['_compressed', '_max2048_bilinear',
                         '_max2048_bicubic', '_max2048_bilinear_ignore600KB']

    for i in range(0, len(output_postfixes)):
        ma = max_pixel_of_largest_side[i]
        re = resize_type[i]
        ck = check_disk_size_below_KB[i]
        op = output_postfixes[i]


    output_postfix = op
    image_output_paths = [''.join([example_images_path,
                          file.split('.')[0] + output_postfix + '.' +
                          file.split('.')[1]]) for
                          file in image_files]

    for image_input_path, image_output_path in zip(image_input_paths, image_output_paths):
        image_entry = {'imnum': 0, 'totim': 100, 't0': 100, 'invalid': 0,
                        'absimpath': image_input_path,
                        'comprimgpath': image_output_path,
                        'quality': 17}
        compress_image(image_entry, max_pixel_of_largest_side=ma,
                       resize_type=re,
                       check_disk_size_below_KB=ck)


    # # TEST
    # # get size of image
    # KB_size = os.path.getsize(image_input_paths[1]) / 1024
    #
    # max_pixel_of_largest_side = 2048
    #
    # img = Image.open(image_input_paths[1])
    #
    # if any([x > max_pixel_of_largest_side for x in img.size]):
    #     img.thumbnail(size=[max_pixel_of_largest_side,
    #                         max_pixel_of_largest_side])
    # img.save(image_output_paths[1])
    #
    #
    #
    # img.save(image_output_paths[1],"JPEG",quality=17)
    # img.close()
