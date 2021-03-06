
import os
# force-train on CPU to avoid holonet 128 error
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"   # see issue #152
# os.environ["CUDA_VISIBLE_DEVICES"] = ""
import sys

if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3, not {0}.{1}".format(sys.version_info[0], sys.version_info[1]))

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import scipy.sparse.linalg
from sys import platform
from src.data.diffraction import DiffractionGenerator
# on windows box (with AMD GPU) use keras plaidml backend...
# if platform == "win32":
#     os.environ["KERAS_BACKEND"] = "plaidml.keras.backend"
    # import plaidml.keras
    # plaidml.keras.install_backend()
import timeit

import keras.layers.advanced_activations as A

from src.processing.train import train_unet
from src.processing.train import train_holo_net
from src.loss.avg import mse_dssim_loss
from src.processing.predict import prediction
from src.processing.predict import prediction_with_merge
from src.data.loader import DataLoader
from src.processing.predict_realtime import prediction_realtime

# all directories are relative to the src folder

# Run 100 Epochs
# train_unet('nucleus-4dirs', dataset='0129-2dirs',
#            num_layers=6, filter_size=3,
#            learn_rate=1e-4, conv_depth=32, epochs=100,
#            records=-1, batch_size=16, activation=A.PReLU,
#            advanced_activations=True, last_activation=A.PReLU)


# Run 25 epochs, saving every epoch's weights (if an evolution plot is desired)
# train_unet('nucleus-25-epochs', dataset='nucleus',
#             num_layers=6, filter_size=3, save_best_only=False,
#             learn_rate=1e-4, conv_depth=32, epochs=25,
#             records=-1, batch_size=16, activation=A.PReLU,
#             advanced_activations=True, last_activation=A.PReLU)

# # run 5 epochs with small 32-image test dataset (make sure NN architecture works)
# train_unet('nicha_sarvesh_test', dataset='test-mydataset-dapi',
#           num_layers=6, filter_size=3,
#           learn_rate=1e-4, conv_depth=32, epochs=5,
#           records=-1, batch_size=16, activation=A.PReLU,
#           advanced_activations=True, last_activation=A.PReLU)


# run 25 epochs with custom loss function
#train_unet('nucleus-custom-loss', dataset='0129-2dirs',
#           num_layers=6, filter_size=3, loss='mse_ssim',
#           learn_rate=1e-4, conv_depth=32, epochs=25,
#           records=-1, batch_size=16, activation=A.PReLU,
#           advanced_activations=True, last_activation=A.PReLU)


# Run 25 epochs, saving every 5 epoch's weights (if an evolution plot is desired)
# train_unet('nucleus-25-epochs', dataset='nucleus',
#             num_layers=6, filter_size=3, save_best_only=False,
#             learn_rate=1e-4, conv_depth=32, epochs=25,
#             records=-1, batch_size=16, activation=A.PReLU,
#             advanced_activations=True, last_activation=A.PReLU, period=5)





#load a folder of full-sized images, tile them, run the model, and then merge the predictions
# patches, padded_results = prediction_with_merge('unet_6-3_mse_ssim_test_031418_100epochs',
#                '/home/ubuntu/nucleus-prediction/data/smooth_merge_test/input/',
#                '/home/ubuntu/nucleus-prediction/data/smooth_merge_test/output/',
#                weights_file='weights_95.h5', debug_images=True, high_quality=False)

# to shutdown AWS instance automatically
# import subprocess
# subprocess.call(['sudo','shutdown','-h','0'])


# train_unet('text-full', dataset='ds-text', records=-1,
#            num_layers=6, filter_size=3,
#            learn_rate=1e-4, conv_depth=32, epochs=100,
#            batch_size=16, activation=A.PReLU,
#            separate=False, advanced_activations=True,
#            last_activation='sigmoid', output_depth=1)
# data, label_text = DataLoader.load_testing(records=-1, separate = False,
#             dataset='ds-text')
# ssim = prediction('unet_6-3_mse_text-full', data, label_text, transpose=False)

# train_unet('mnist-metatest', dataset='mnist-diffraction', records=256,
#            num_layers=6, filter_size=3,
#            learn_rate=1e-4, conv_depth=32, epochs=12,
#            batch_size=16, activation=A.PReLU,
#            separate=False, advanced_activations=True,
#            last_activation='sigmoid', output_depth=1,
#            long_description='This is a simple/minimal test to ensure all \
#             callbacks are working')

# data, label_text = DataLoader.load_testing(records=-1, separate = False,
#             dataset='mnist-diffraction')
# data, label_text = DataLoader.load_testing(records=-1, separate = False,
#             dataset='mnist-chopped')
# ssim = prediction('unet_6-3_mse_mnist-3750', data, label_text, transpose=False)

# data, label = DataLoader.load_training(records=-1, separate = False,
#             dataset='hangul_1')
# ssim = prediction('unet_6-3_mse_mnist-3750', data, label, transpose=False)

# train_unet('hangul_5', dataset='hangul_5', records=-1,
#            num_layers=6, filter_size=3,
#            learn_rate=1e-4, conv_depth=32, epochs=15,
#            batch_size=16, activation=A.PReLU,
#            separate=False, advanced_activations=True,
#            last_activation='sigmoid', output_depth=1,
#            long_description='Training a model directly on hangul dataset')

# data, label = DataLoader.load_training(records=-1, separate = False,
#             dataset='mnist-diffraction')
# ssim = prediction('hangul_5', data, label, transpose=False,
#         long_description='Predict full training set of MNIST holograms (mnist-diffraction) using hangul_5 model')


# start = timeit.timeit()
# train_holo_net('holo_net_64_1', dataset='hangul_5', records=-1,
#             filter_size=64, learn_rate=1e-4, conv_depth=1, epochs=76,
#            batch_size=16, activation='sigmoid',
#            output_depth=1, long_description='2nd-pass training of holonet single 64x64 filter')
# end = timeit.timeit()
# print(end - start)

# train_holo_net('holo_net_64_3', dataset='ds-lymphoma', records=-1,
#             filter_size=64, learn_rate=1e-4, conv_depth=3, epochs=76,
#            batch_size=16, activation='sigmoid',
#            output_depth=3, long_description='1st training of holonet triple 64x64 filter with lymphoma Holo --> Mag-Real-Imag pairs')

# train_holo_net('holo_net_64_3_phase_arms', dataset='ds-lymphoma', records=-1,
#             filter_size=64, learn_rate=1e-4, conv_depth=1, epochs=76,
#            batch_size=16, activation='sigmoid',
#            output_depth=3, long_description='Feed magnitude information into phase prediction')

# train_holo_net('holo_net_64_3_phase_depth_2', dataset='ds-lymphoma', records=-1,
#             filter_size=64, learn_rate=1e-4, conv_depth=1, epochs=76,
#            batch_size=16, activation='sigmoid', extra_phase_layers=1,
#            output_depth=3, long_description='Feed magnitude information into phase prediction')
#
# train_holo_net('holo_net_64_3_phase_depth_2_prelu', dataset='ds-lymphoma', records=-1,
#             filter_size=64, learn_rate=1e-4, conv_depth=1, epochs=151, period=15,
#            batch_size=16, activation=A.PReLU, advanced_activations=True, extra_phase_layers=1,
#            output_depth=3, long_description='Feed magnitude information into phase prediction')

# train_holo_net('holo_net_64_3_phase_depth_2_prelu_sigmoid', dataset='ds-lymphoma', records=-1,
#             filter_size=64, learn_rate=1e-4, conv_depth=1, epochs=151, period=15,
#            batch_size=16, activation='sigmoid', advanced_activations=True, extra_phase_layers=1,
#            output_depth=3, long_description='Feed magnitude information into phase prediction')

train_holo_net('holo_net_128', dataset='ds-lymphoma', records=64,
            filter_size=128, learn_rate=1e-4, conv_depth=1, epochs=151, period=15,
           batch_size=4, activation='sigmoid', advanced_activations=True, extra_phase_layers=1,
           output_depth=3, long_description='Feed magnitude information into phase prediction')
#

# data, label = DataLoader.load_training(records=-1, separate = False, dataset='hangul_5')
# ssim = prediction_realtime('holo_net_64_1', data, label, transpose=False, long_description='')

# generate free space transfer
# import numpy as np
# import imageio
# data, label = DataLoader.load_testing(records=1, separate = False,
#             dataset='mnist-diffraction')
# Gfp = DiffractionGenerator.freeSpaceTransfer(np.squeeze(data[0]), z=2.5e-3, lmbda=405e-9, upsample=2)
# center = Gfp.shape[0] //
# 2
# Gfp_mag = np.abs(Gfp)[center-32:center+32,center-32:center+32]
# imageio.imwrite('f:/d3-recon-ml/Gfp64mag.png', Gfp_mag)


# train_holo_net('holo_net_64_2_lymphoma', dataset='ds-lymphoma', records=-1,
#             filter_size=64, learn_rate=1e-4, conv_depth=2, epochs=76,
#            batch_size=16, activation='sigmoid',
#            output_depth=1, long_description='Train holonet64 with 2 filters on lymphoma (real/imag) dataset')
#



# w = m.layers[1].get_weights()
# imageio.imwrite('f:/d3-recon-ml/holo64x64.png',w[0])

# Only fit SSIM Histogram on last epoch, otherwise use normal/skew distribution...
# TODO: Add metadata to predictions folder
# TODO: Create a simple folder that can be uploaded to the "Experiments" dropbox
# DONE: Add platform and GPU to the model metadata file
# TODO: Test AWS vs. local GPU performance
# DONE: Change model name to remove "unet_6_3" etc. This is now in metadata.csv
# TODO: Add a text description the "train_unet" function which gets stored in metadata.csv
# TODO: Add model train/predict timings for easy performance comparison
# TODO: Organize SSIM best to worst, and create a "sample" folder with some examples
# TODO: Predict on every epoch for small subset and save to an evolution folder
# TODO: update train/validation curve on each epoch for live monitoring
# TODO: Add rotation/stretching and partial predictions (train on whole)
# TODO: vectorize graphs so they are easily incorporated into paper.

