import os
import sys
import time

# from src.callbacks.holonet_callbacks import HoloNetCallback

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

import numpy as np
from keras_contrib.losses import DSSIMObjective
from keras.layers import Activation
from src.data.loader import DataLoader
from keras.optimizers import Adam
from src.arch.unet import get_unet
from src.arch.holo_transfer import get_holo_transfer
from src.arch.dcgan import DCGAN, DCGAN_discriminator
from keras.callbacks import ModelCheckpoint, CSVLogger, TensorBoard
import keras.backend as K
from src.processing.folders import Folders
from src.visualization.fit_plotter import FitPlotter

from keras.utils import generic_utils
import pandas as pd
import inspect
import csv
import keras.layers.advanced_activations as A
import keras.backend

from src.callbacks.fit_plotter_callback import FitPlotterCallback
from src.callbacks.time_history_callback import TimeHistory
from src.callbacks.ssim_plotter_callback import SSIMPlotterCallback
from src.callbacks.model_to_experiment import ModelToExperiment
from src.callbacks.holonet_filter_callbacks import HoloNetFilterCallback

def get_callbacks(model_name, experiment_id, batch_size = 32,
                  save_best_only = True, period=5,
                  test_data=None, test_labels=None, holonet = False):
    models_folder = Folders.models_folder()
    experiments_folder = Folders.experiments_folder()
    os.makedirs(experiments_folder + experiment_id, exist_ok=True)

    file_suffix = '_{epoch:02d}.h5'
    if save_best_only:
        file_suffix = '.h5'

    model_checkpoint = ModelCheckpoint(models_folder + "{0}/weights".format(model_name) + file_suffix,
                                       monitor='val_loss', save_best_only=save_best_only)
    csv_logger = CSVLogger(models_folder + "{0}/perflog.csv".format(model_name),
                                            separator=',', append=False)
    fit_plotter = FitPlotterCallback(model_name, experiment_id)
    time_history = TimeHistory(model_name, experiment_id)
    ssim_plotter = SSIMPlotterCallback(model_name, experiment_id, test_data, test_labels)
    # copycallback = ModelToExperiment(model_name, experiment_id)
    callbacks = [model_checkpoint, csv_logger, fit_plotter, time_history, ssim_plotter]#, copycallback]

    if keras.backend.backend() == 'tensorflow':
        tensorboard = TensorBoard(log_dir=models_folder + model_name, histogram_freq=0,
                              batch_size=batch_size, write_graph=True, write_grads=False,
                              write_images=True, embeddings_freq=0,
                              embeddings_layer_names=None, embeddings_metadata=None)
        callbacks.append(tensorboard)
    if holonet:
        callbacks.append(HoloNetFilterCallback(model_name, experiment_id, period=period))
        # callbacks.append(HoloNetCallback(model_name, experiment_id))

    return callbacks


def train(model_name, model, data, labels, epochs, save_summary=True,
          batch_size=32, save_best_only=True, model_metadata=None,
          test_data=None, test_labels=None, holonet=False, period=5):
    """ Train a generic model and save relevant data """
    models_folder = Folders.models_folder()
    os.makedirs(models_folder + model_name, exist_ok=True)
    experiment_id = time.strftime("%Y%m%d-%H%M%S") + '_' + model_name
    m_path = models_folder + model_name
    # e_path = Folders.experiments_folder() + experiment_id
    if save_summary:
        def summary_saver(path):

            def summary_save(s):
                with open(path, 'a+') as f:
                    print(s, file=f)
            return summary_save
        model.summary(print_fn=summary_saver(m_path+ '/model_summary.txt'))
        # model.summary(print_fn=summary_saver(e_path+ '/model_summary.txt'))

    if model_metadata is not None:
        model_metadata['model_name'] = model_name
        save_metadata(m_path + '/metadata.csv', model_metadata)
        # save_metadata(e_path + '/metadata.csv', model_metadata)

    # Step 2: train and save best weights for the given architecture
    print('-' * 30)
    print('Fitting model {0}...'.format(model_name))
    print('-' * 30)
    history = model.fit(
        data, labels, batch_size=batch_size,
        epochs=epochs, verbose=1, shuffle=True,
        validation_split=0.2, callbacks=get_callbacks(
            model_name, experiment_id, batch_size=batch_size,
            save_best_only=save_best_only, holonet=holonet,
            test_data=test_data, test_labels=test_labels, period=period))

    # Step 3: Plot the validation results of the model, and save the performance data
    plot_path = os.path.join(Folders.models_folder(), '{0}/train_validation'.format(model_name))
    FitPlotter.save_plot(history.history, plot_path)

    val_loss = np.asarray(history.history['val_loss'])
    min_loss_epoch = np.argmin(val_loss)
    min_train_loss = history.history['loss'][min_loss_epoch]

    return min_loss_epoch, min_train_loss, val_loss[min_loss_epoch]


    # (TODO) Step 3: Save other visuals


def save_metadata(path, model_metadata):
    with open(path, 'w') as f:
        for k, v in model_metadata.items():
            f.write('{0}: {1}\n'.format(k, v))

def extract_metadata(frame):
    _, _, _, values = inspect.getargvalues(frame)
    ignore_keys = ['frame', 'd_raw', 'metadata']
    metadata = {}
    for k,v in values.items():
        if k not in ignore_keys:
            if str(v).startswith('<class'):
                v = v.__name__
            metadata[k] = v
    metadata['keras_backend'] = keras.backend.backend()
    metadata['keras_version'] = keras.__version__
    metadata['platform'] = sys.platform
    metadata['python_version'] = sys.version
    return metadata

def train_unet(descriptive_name, dataset='ds-lymphoma',
               num_layers=6, filter_size=3, conv_depth=32,
               learn_rate=1e-4, epochs=18, loss='mse', records=-1,
               separate=True,  batch_size=32, activation: object='relu',
               last_activation: object='relu', advanced_activations=False,
               a_only=False, b_only=False, output_depth=2,
               save_best_only=True, long_description=''):
    """ Train a unet model and save relevant data """

    loss_abbrev = loss
    if isinstance(loss, DSSIMObjective):
        loss_abbrev = 'dssim'

    # gather up the params
    metadata = extract_metadata(inspect.currentframe())

    # Step 1: load data
    d_raw = DataLoader.load_training(dataset=dataset, records=records, separate=separate)
    d_test_raw = DataLoader.load_testing(dataset=dataset, records=records, separate=separate)

    # Step 2: Configure architecture
    # Step 3: Configure Training Parameters and Train

    if separate:
        suffix_a, suffix_b = 'real', 'imag'
        if 'magphase' in dataset:
            suffix_a, suffix_b = 'magnitude', 'phase'

        train_data, train_label_a, train_label_b = d_raw
        img_rows, img_cols = train_data.shape[1], train_data.shape[2]

        model_name_a = model_name_b = ''
        epoch_a = epoch_b = 0
        train_loss_a = val_loss_a = train_loss_b = val_loss_b = 0.0

        if not b_only:
            modela = get_unet(img_rows, img_cols, num_layers=num_layers, filter_size=filter_size,
                              conv_depth=conv_depth, optimizer=Adam(lr=learn_rate), loss=loss,
                              last_activation=last_activation, activation=activation,
                              advanced_activations=advanced_activations, output_depth=1)
            model_name_a = '{0}_{1}'.format(descriptive_name, suffix_a)
            epoch_a, train_loss_a, val_loss_a = train(model_name_a, modela,
                train_data, train_label_a, epochs, model_metadata=metadata,
                batch_size=batch_size, save_best_only=save_best_only)

        if not a_only:
            model_name_b = '{0}_{1}'.format(descriptive_name, suffix_b)
            # output_depth = 2 if split_b else 1
            modelb = get_unet(img_rows, img_cols, num_layers=num_layers, filter_size=filter_size,
                              conv_depth=conv_depth, optimizer=Adam(lr=learn_rate), loss=loss,
                              last_activation=last_activation, activation=activation,
                              advanced_activations=advanced_activations, output_depth=output_depth)
            epoch_b, train_loss_b, val_loss_b = train(model_name_b, modelb,
                train_data, train_label_b, epochs, model_metadata=metadata,
                batch_size=batch_size, save_best_only=save_best_only)

        return model_name_a, epoch_a, train_loss_a, val_loss_a, \
             model_name_b, epoch_b, train_loss_b, val_loss_b
    else:
        train_data, train_label = d_raw
        test_data, test_label = d_test_raw
        img_rows, img_cols = train_data.shape[1], train_data.shape[2]

        model = get_unet(img_rows, img_cols, num_layers=num_layers, filter_size=filter_size,
                         conv_depth=conv_depth, optimizer=Adam(lr=learn_rate), loss=loss,
                         output_depth=output_depth, activation=activation, advanced_activations=advanced_activations,
                         last_activation=last_activation)
        model_name = descriptive_name
        epoch, train_loss, val_loss = train(model_name, model, train_data,
            train_label, epochs, model_metadata=metadata, batch_size=batch_size,
                save_best_only=save_best_only, test_data=test_data, test_labels=test_label)
        return model_name, epoch, train_loss, val_loss

def train_holo_net(descriptive_name, dataset='ds-lymphoma',
               filter_size=32, conv_depth=1, extra_phase_layers=0,
               learn_rate=1e-4, epochs=18, loss='mse', records=-1,
               separate=False,  batch_size=32, activation: object='relu',
               advanced_activations=True, period=5,
               output_depth=1, save_best_only=True, long_description=''):

    # gather up the params
    metadata = extract_metadata(inspect.currentframe())

    # Step 1: load data
    d_raw = DataLoader.load_training(dataset=dataset, records=records, separate=separate)
    d_test_raw = DataLoader.load_testing(dataset=dataset, records=records, separate=separate)

    # Step 2: Configure architecture
    # Step 3: Configure Training Parameters and Train

    train_data, train_label = d_raw
    test_data, test_label = d_test_raw
    test_label = np.squeeze(test_label)
    train_label = np.squeeze(train_label)
    img_rows, img_cols = train_data.shape[1], train_data.shape[2]

    model = get_holo_transfer(img_rows, img_cols, filter_size=filter_size,
                     conv_depth=conv_depth, optimizer=Adam(lr=learn_rate), loss=loss,
                     output_depth=output_depth, activation=activation,
                     advanced_activations=advanced_activations,
                     extra_phase_layers=extra_phase_layers)
    model_name = descriptive_name
    epoch, train_loss, val_loss = train(model_name, model, train_data,
        train_label, epochs, model_metadata=metadata, batch_size=batch_size, holonet=True,
            save_best_only=save_best_only, test_data=test_data, test_labels=test_label, period=period)
    return model_name, epoch, train_loss, val_loss



# train a single unet on a small dataset
#train_unet('small-dataset-test', 6, 3, learn_rate=1e-4, epochs=2, records=64)

# train a single unet with DSSIM loss
# train_unet('dssim_test', num_layers=6, filter_size=3, learn_rate=1e-4,
#           epochs=2, loss=DSSIMObjective(), records=64)

# train a toy unet for the image evolution plot test
#train_unet('evplot', num_layers=3, filter_size=3, learn_rate=1e-4, conv_depth=1, epochs=2, records=64)

# train a toy UNET + DCGAN
#train_dcgan(num_layers=3, filter_size=3, conv_depth=2, learn_rate=1e-3, epochs=2,
#                 loss='mean_squared_error', records=64, batch_size=2)

# train a large UNET + DCGAN
# train_dcgan(num_layers=7, filter_size=3, conv_depth=32, learn_rate=1e-3, epochs=15,
#                   loss='mean_squared_error', records=-1, batch_size=32)



# train_unet('dual-test', num_layers=6, filter_size=3,
#            learn_rate=1e-4, conv_depth=32, epochs=18,
#            records=-1, separate=False, batch_size=16,
#            activation='relu', last_activation='relu')
#

# train_unet('prelu-test', num_layers=6, filter_size=3,
#            learn_rate=1e-4, conv_depth=32, epochs=25,
#            records=-1, separate=True, batch_size=16,
#            activation=A.PReLU, advanced_activations=True,
#            last_activation=A.PReLU)

# train_unet('prelu-dual-test', num_layers=6, filter_size=3,
#            learn_rate=1e-4, conv_depth=32, epochs=18,
#            records=-1, separate=False, batch_size=16,
#            activation=A.PReLU, advanced_activations=True,
#            last_activation='relu')


# train_unet('prelu-test', num_layers=6, filter_size=3,
#            learn_rate=1e-4, conv_depth=32, epochs=25,
#            records=-1, separate=True, batch_size=16,
#            activation=A.PReLU, advanced_activations=True,
#            last_activation=A.PReLU, b_only=True)

# train_unet('prelu-test-magphase', dataset='ds-lymphoma-magphase',
#            num_layers=6, filter_size=3,
#            learn_rate=1e-4, conv_depth=32, epochs=25,
#            records=-1, separate=True, batch_size=16,
#            activation=A.PReLU, advanced_activations=True,
#            last_activation=A.PReLU)


# train_unet('prelu-split-phase-only', dataset='ds-lymphoma-magphase-splitphase',
#            num_layers=6, filter_size=3,
#            learn_rate=1e-4, conv_depth=32, epochs=25,
#            records=-1, separate=False, b_only=True,
#            batch_size=16, activation=A.PReLU, advanced_activations=True,
#            last_activation=A.PReLU)
#
#


# centered text test
# train_unet('text', num_layers=6, filter_size=3,
#     dataset = 'ds-text', save_best_only=False,
#     learn_rate=1e-4, conv_depth=32, epochs=25,
#     records=-1, separate=False, batch_size=16,
#     activation=A.PReLU, advanced_activations=True,
#     last_activation='sigmoid', output_depth=1)

