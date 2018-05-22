import os
import time
from PIL import Image


def compress_image (img_entry):

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


# TESTING
if __name__ == '__main__':
    example_images_path = '/home/packerc/shared/machine_learning/will5448/data/example_images/compression_issue/'
    image_files = os.listdir(example_images_path)
    output_postfix = '_compressed'
    image_input_paths = [''.join([example_images_path, file])
                         for file in image_files]
    image_output_paths = [''.join([example_images_path,
                          file.split('.')[0] + output_postfix + '.' +
                          file.split('.')[1]]) for
                          file in image_files]
    image_data = list()

    for image_input_path, image_output_path in zip(image_input_paths, image_output_paths):
        image_entry = {'imnum': 0, 'totim': 100, 't0': 100, 'invalid': 0,
                        'absimpath': image_input_path,
                        'comprimgpath': image_output_path,
                        'quality': 17}
        image_data.append(image_entry)

    compress_image(image_data)


    # TEST
    # img = Image.open(image_input_paths[0])
    # img.thumbnail(img.size)
    # img.save(image_output_paths[0],"JPEG",quality=17)
    # img.close()
