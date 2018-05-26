import argparse

def main():
  parser = argparse.ArgumentParser(description='Process Command-line Arguments')
  parser.add_argument('--load_size', nargs= 2, default= [256,256], type= int, action= 'store', help= 'The width and height of images for loading from disk')
  parser.add_argument('--crop_size', nargs= 2, default= [224,224], type= int, action= 'store', help= 'The width and height of images after random cropping')
  parser.add_argument('--batch_size', default= 512, type= int, action= 'store', help= 'The testing batch size')
  parser.add_argument('--num_classes', default= 2, type= int, action= 'store', help= 'The number of classes')
  parser.add_argument('--top_n', default= 2, type= int, action= 'store', help= 'Top N accuracy')
  parser.add_argument('--num_channels', default= 3, type= int, action= 'store', help= 'The number of channels in input images')
  parser.add_argument('--num_batches' , default=-1 , type= int, action= 'store', help= 'The number of batches of data')
  parser.add_argument('--path_prefix' , default='/project/EvolvingAI/mnorouzz/Serengiti/EmptyVsFullEQ/', action= 'store', help= 'The prefix address for images')
  parser.add_argument('--delimiter' , default=',', action = 'store', help= 'Delimiter for the input files')
  parser.add_argument('--data_info'   , default= 'EF_val.csv', action= 'store', help= 'File containing the addresses and labels of testing images')
  parser.add_argument('--num_threads', default= 20, type= int, action= 'store', help= 'The number of threads for loading data')
  parser.add_argument('--architecture', default= 'resnet', help='The DNN architecture')
  parser.add_argument('--depth', default= 50, type= int, help= 'The depth of ResNet architecture')
  parser.add_argument('--log_dir', default= None, action= 'store', help='Path for saving Tensorboard info and checkpoints')
  parser.add_argument('--save_predictions', default= None, action= 'store', help= 'Save top-5 predictions of the networks along with their confidence in the specified file')

  args = parser.parse_args()
  print(args)


if __name__ == '__main__':
  main()
