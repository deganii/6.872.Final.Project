
from __future__ import print_function

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

import PIL.ImageOps
# import keras
import scipy, scipy.ndimage
from PIL import Image, ImageDraw, ImageFont
import random
import string
import numpy as np
import os
import ntpath
import imageio
import imageio
import glob

from src.processing.folders import Folders


class DiffractionGenerator(object):

    @classmethod
    def ft2(cls, g, delta=2.2e-6):
        print('ft2 shift')
        return np.fft.fftshift(np.fft.fft2((np.fft.fftshift(g)))) #* delta ** 2

    @classmethod
    def ift2(cls, G, dfx, dfy):
        print('ift2 shift')
        Nx, Ny = np.shape(G)
        return np.fft.ifftshift(np.fft.ifft2(np.fft.ifftshift(G))) #* Nx * Ny * dfx * dfy

    @classmethod
    def ft2_noshift(cls, g, delta=2.2e-6):
        print('ft2 noshift')
        # return np.fft.fft2((np.fft.fftshift(g)))* delta ** 2
        return np.fft.fft2(((g))) #* delta ** 2

    @classmethod
    def ift2_noshift(cls, G, dfx, dfy):
        print('ift2 noshift')
        Nx, Ny = np.shape(G)
        # return np.fft.ifftshift(np.fft.ifft2(G)) * Nx * Ny * dfx * dfy
        return (np.fft.ifft2(G)) #* Nx * Ny * dfx * dfy


    @classmethod
    def upsampling(cls, data, dx1, upsample=2):
        dx2 = dx1 / (2 ** upsample)
        x_size = ((2 ** upsample) * data.shape[0]) - (2 ** (upsample) - 1)
        y_size = ((2 ** upsample) * data.shape[1]) - (2 ** (upsample) - 1)
        data = data.astype("float32")
        upsampled = scipy.ndimage.zoom(data, [x_size / data.shape[0], y_size / data.shape[1]], order=3)
        # self .debug_save_mat(upsampled, 'upsampledPy')
        return upsampled, dx2

    @classmethod
    def freeSpaceTransfer(cls, bf_image, z = 5e-4, lmbda = 405e-9,
                             delta=2.2e-6, upsample=2, pad_width=0):
        if type(bf_image) is not np.ndarray:
            recon = np.array(bf_image)
        else:
            recon = bf_image
        if upsample > 1:
            recon, delta = DiffractionGenerator.upsampling(recon, delta, upsample)
        recon = np.pad(recon, pad_width=pad_width, mode='edge')
        k = 2 * np.pi / lmbda
        Nx, Ny = np.shape(recon)
        dfx = 1 / (Nx * delta)
        dfy = 1 / (Ny * delta)
        fx, fy = np.meshgrid(np.arange(-Ny / 2, Ny / 2, 1) * dfy,
                                 np.arange(-Nx / 2, Nx / 2, 1) * dfx)
        # forward propagate img => hologram, non-cascaded (Kreis 2002)
        Gfp = np.exp((-1j * k * z) * np.sqrt(1 - lmbda ** 2 * fx ** 2 - lmbda ** 2 * fy ** 2))
        return Gfp

    @classmethod
    def freeSpaceKernelOnly(cls, Nx, Ny, z = 5e-4, lmbda = 405e-9,
                             delta=2.2e-6):
        k = 2 * np.pi / lmbda
        dfx = 1 / (Nx * delta)
        dfy = 1 / (Ny * delta)
        fx, fy = np.meshgrid(np.arange(-Ny / 2, Ny / 2, 1) * dfy,
                                 np.arange(-Nx / 2, Nx / 2, 1) * dfx)
        # forward propagate img => hologram, non-cascaded (Kreis 2002)
        Gfp = np.exp((-1j * k * z) * np.sqrt(1 - lmbda ** 2 * fx ** 2 - lmbda ** 2 * fy ** 2))
        return Gfp

    @classmethod
    def freeSpacePropagation(cls, bf_image, z = 5e-4, lmbda = 405e-9,
                             delta=2.2e-6, upsample=2, pad_width=0, Gfp=None):
        ft2 = DiffractionGenerator.ft2
        ift2 = DiffractionGenerator.ift2
        if type(bf_image) is not np.ndarray:
            recon = np.array(bf_image)
            recon = recon / np.max(recon)
        else:
            recon = bf_image

        if upsample > 1:
            recon, delta = DiffractionGenerator.upsampling(recon, delta, upsample)
            #imageio.imwrite('../../data/ds-simulated/00000-0-US.png', recon)

        recon = np.pad(recon, pad_width=pad_width, mode='edge')
        #imageio.imwrite('../../data/ds-simulated/00000-0-PAD.png', recon)

        k = 2 * np.pi / lmbda
        Nx, Ny = np.shape(recon)
        dfx = 1 / (Nx * delta)
        dfy = 1 / (Ny * delta)

        if Gfp is None:
            fx, fy = np.meshgrid(np.arange(-Ny / 2, Ny / 2, 1) * dfy,
                                 np.arange(-Nx / 2, Nx / 2, 1) * dfx)
            # forward propagate img => hologram, non-cascaded (Kreis 2002)
            Gfp = np.exp((-1j * k * z) * np.sqrt(1 - lmbda ** 2 * fx ** 2 - lmbda ** 2 * fy ** 2))
        R = ft2(recon, delta)
        Output = ift2(np.multiply(R, Gfp), dfx, dfy)
        return Output

    @classmethod
    def freeSpacePropagationNoShift(cls, bf_image, z = 5e-4, lmbda = 405e-9,
                             delta=2.2e-6, upsample=2, pad_width=0, Gfp=None):
        ft2 = DiffractionGenerator.ft2_noshift
        ift2 = DiffractionGenerator.ift2_noshift
        if type(bf_image) is not np.ndarray:
            recon = np.array(bf_image)
            recon = recon / np.max(recon)
        else:
            recon = bf_image

        if upsample > 1:
            recon, delta = DiffractionGenerator.upsampling(recon, delta, upsample)
            #imageio.imwrite('../../data/ds-simulated/00000-0-US.png', recon)

        recon = np.pad(recon, pad_width=pad_width, mode='edge')
        #imageio.imwrite('../../data/ds-simulated/00000-0-PAD.png', recon)

        k = 2 * np.pi / lmbda
        Nx, Ny = np.shape(recon)
        dfx = 1 / (Nx * delta)
        dfy = 1 / (Ny * delta)

        if Gfp is None:
            fx, fy = np.meshgrid(np.arange(-Ny / 2, Ny / 2, 1) * dfy,
                                 np.arange(-Nx / 2, Nx / 2, 1) * dfx)
            # forward propagate img => hologram, non-cascaded (Kreis 2002)
            Gfp = np.exp((-1j * k * z) * np.sqrt(1 - lmbda ** 2 * fx ** 2 - lmbda ** 2 * fy ** 2))
            imageio.imwrite(r'c:\dev\Gfpi.png', np.real(np.fft.ifftshift(Gfp)))
            imageio.imwrite(r'c:\dev\Gfpf.png', np.real(np.fft.fftshift(Gfp)))
            print("GFPShift equal: {0}".format(
                str(np.array_equal(np.fft.ifftshift(Gfp), np.fft.fftshift(Gfp)))))
            Gfp = np.fft.ifftshift(Gfp)

        R = ft2(recon, delta)
        Output = ift2(np.multiply(R, Gfp), dfx, dfy)
        return Output


    @classmethod
    def generateRandomText(cls,  text_len = 3):
        return "".join([random.choice(string.digits + string.ascii_letters)
                             for i in range(text_len)])

    @classmethod
    def generateCenteredTextSample(cls, size=(192,192), z = 1.5e-3, lmbda = 405e-9,
                       delta=2.2e-6, upsample=1, text=None, text_len = 3, font_size=40,
                        exclude='CSB'):
        w, h = size
        image = Image.new('L', size, (255))
        draw = ImageDraw.Draw(image)

        # random placements of non-overlapping shapes with different refractive indices
        fnt = ImageFont.truetype('arial.ttf', font_size)
        if text is None:
            rand_text = exclude
            while rand_text == exclude: # don't include the test sample
                rand_text = DiffractionGenerator.generateRandomText(text_len)
            text = rand_text
        tw, th = fnt.getsize(text)
        tx, ty = (w - tw)/2, (h - th)/2,
        draw.text((tx, ty), text, font=fnt, fill=(0))
         # introduce a random magnitude and phase shift
        recon = np.array(image) #.astype(np.complex64)
        # propagate to a hologram
        holo = np.abs(DiffractionGenerator.freeSpacePropagation(recon,
                upsample=upsample, z=z, lmbda=lmbda))
        # cropx, cropy = int(w/upsample), int(h/upsample)
        # holo = holo[cropx:-cropx, cropy:-cropy]
        # imageio.imwrite('holo.png', holo)
        # imageio.imwrite('label.png', np.abs(recon))
        return holo, recon

    @classmethod
    def generateTextDataset(cls, set_name='ds-text', samples=10000,
            size=(192,192), z = 1.5e-3, lmbda = 405e-9,
            delta=2.2e-6, upsample=1, text_len = 3, font_size=40):

        size_w,size_h = size
        data = np.zeros((samples, size_w, size_h))
        labels = np.zeros((samples, size_w, size_h))

        data_folder = Folders.data_folder()
        image_folder = data_folder + set_name + '/'
        if not os.path.exists(image_folder):
            os.makedirs(image_folder)
        text = None
        text_set = {}
        for i in range(samples):
            if i % 400 == 0:
                print("Generating Sample: {0}/{1}".format(i, samples))
            if i == samples -1:
                text = 'CSB'
            else:
                while text is None or text in text_set:
                    text = DiffractionGenerator.generateRandomText(text_len)
            text_set[text] = True
            holo, recon = DiffractionGenerator.generateCenteredTextSample(size=size,
                z=z, lmbda=lmbda, delta=delta, upsample=upsample,
                text_len=text_len, font_size=font_size, text=text)
            data[i] = holo
            labels[i] = recon

            holoDestFilename = '{0:05}-H-{1}.png'.format(i,text)
            magnDestFilename = '{0:05}-M-{1}.png'.format(i,text)

            # save hologram and magnitude
            imageio.imwrite(image_folder +  holoDestFilename, np.squeeze(holo))
            imageio.imwrite(image_folder +  magnDestFilename, np.squeeze(recon))

        # partition and save
        test_count = int(np.floor(labels.shape[0] * 0.8))
        training_data, test_data = data[:test_count, ...], data[test_count:, ...]
        training_labels, test_labels =labels[:test_count, ...], labels[test_count:, ...]
        np.savez(os.path.join(data_folder, set_name + '-training.npz'), data=training_data, labels=training_labels)
        np.savez(os.path.join(data_folder, set_name + '-test.npz'), data=test_data, labels=test_labels)

    @classmethod
    def generateSample(cls, size=(192,192), z = 7e-4, lmbda = 405e-9,
                       delta=2.2e-6, upsample=4):
        w, h = size
        # super_size = (w * 10, h * 10)
        # super_image = Image.new('L', super_size, (255))

        image = Image.new('L', size, (255))
        draw = ImageDraw.Draw(image)

        # image = PIL.ImageOps.invert(image)
        # draw objects on the order of 5-10 microns (about 20-30 pixels
        objects_bound = []

        def place(obj_size):
            obj_w, obj_h = obj_size
            # try 20 times before giving up
            for i in range(20):
                r_x, r_y = (random.randint(0, w - obj_w), random.randint(0, h - obj_h))
                collision = False
                for other in objects_bound:
                    o_x, o_y, o_w, o_h = other
                    if (o_x < r_x + obj_w and
                            o_x + o_w > r_x and
                        o_y < r_y + obj_h and
                            o_h + o_y > r_y):
                        collision = True
                        break
                if not collision:
                    objects_bound.append((r_x, r_y, obj_w, obj_h))
                    return r_x, r_y, obj_w, obj_h
            return -1, -1, -1, -1

        for i in range(20):
            obj_type = random.randint(0, 4)
            if obj_type == 0 or obj_type > 2:
                # random placements of non-overlapping shapes with different refractive indices
                fnt = ImageFont.truetype('arial.ttf', 20)
                t_len = random.randint(1,6)
                rand_text = "".join([random.choice(string.digits + string.ascii_letters)
                                     for i in range(t_len)])
                text_size = fnt.getsize(rand_text)
                t_x, t_y, t_w, t_h = place(text_size)
                if t_x >= 0:
                    draw.text((t_x, t_y), rand_text, font=fnt, fill=(0))
            if obj_type == 1:
                e_w = random.randint(5,20)
                e_h = random.randint(5,20)
                t_x, t_y, t_w, t_h = place((e_w, e_h))
                if t_x >= 0:
                    draw.ellipse([(t_x, t_y), (t_x+t_w, t_y+t_h)], fill=(0))
            if obj_type == 2:
                t_w = random.randint(5, 20)
                t_h = random.randint(5, 20)
                t_x, t_y, t_w, t_h = place((t_w, t_h))
                if t_x >= 0:
                    draw.polygon([(t_x, t_y), (t_x + t_w, t_y + random.randint(t_h-5, t_h)),
                                               (t_x + random.randint(0,10), t_y + t_h)], fill=(0))


        # introduce a random magnitude and phase shift
        recon = np.array(image).astype(np.complex64)
        mag = random.uniform    (0.0, 1.0)
        phase = random.uniform(0.0, 2 * np.pi)
        recon = recon * mag * np.exp(1j * phase)
        # propagate to a hologram
        holo = np.abs(DiffractionGenerator.freeSpacePropagation(recon, upsample=1, z=7e-4))
        # image.save('output.png')
        imageio.imwrite('holo.png', np.abs(holo))
        imageio.imwrite('label.png', np.abs(recon))

        return holo, recon
        # return np.vstack([np.real(recon), np.imag(recon)])

    # @classmethod
    # def generateNewImagePair(cls, destination, seq, save=True, dx=0.8, dy=0.8, z=0.2, lmbda=405):
    #     bf_image, label = BrightfieldGenerator.generateImage(destination,seq,save=save)
    #     return DiffractionGenerator.generateImage( destination, seq, bf_image, label, save=save, dx=dx, dy=dy, z=z, lmbda=lmbda)

    @classmethod
    def generateDiffractionDataset(cls, source_data, source_labels, destination, npzName, save=True, dx=0.8, dy=0.8, z=0.2, lmbda=405):
        #bf_image, label = BrightfieldGenerator.generateImage(destination,seq,save=save)
        # load source dataset
        num_images = source_data.shape[0]
        dimage_size = 80 * 80
        data = np.zeros([num_images, dimage_size], dtype='float32', )

        if not os.path.exists(destination):
            os.makedirs(destination)

        for i in range(num_images):
            image = source_data[i,:].reshape([40,40])
            label = np.where(source_labels[i] == 1)[0][0]
            dImage, label = DiffractionGenerator.generateImage(destination, i, image, label, save=True, dx=dx, dy=dy, z=z, lmbda=lmbda)
            data[i, :] = dImage.reshape(dimage_size)
        # labels haven't changed...
        dir = os.path.dirname(os.path.dirname(destination))
        np.savez(os.path.join(dir,npzName + '.npz'), data=data, labels=source_labels)
        return data, source_labels

    @classmethod
    def diffractDS1Dataset(cls):
        # bf_image, label = BrightfieldGenerator.generateImage(destination,seq,save=save)
        # load source dataset
        data_folder = '../../data/ds1-pristine/'
        train_destination = '../../data/ds2-diffraction/training/'
        test_destination = '../../data/ds2-diffraction/test/'

        train_npz = np.load(data_folder + 'training.npz')
        test_npz = np.load(data_folder + 'test.npz')

        train_data, train_labels = train_npz['data'], train_npz['labels']
        test_data, test_labels = test_npz['data'], test_npz['labels']

        #train_data, train_labels = BrightfieldGenerator.loadData(data_folder + "training/*.png")
        #test_data, test_labels = BrightfieldGenerator.loadData(data_folder + "test/*.png")
        DiffractionGenerator.generateDiffractionDataset(train_data, train_labels, train_destination, 'training')
        DiffractionGenerator.generateDiffractionDataset(test_data, test_labels, test_destination, 'test')


    @classmethod
    def generateMNISTSet(cls, source_data, source_labels, destination,
                         npzName, save=True, dx=0.8, dy=0.8, z=0.2, lmbda=405):
        #bf_image, label = BrightfieldGenerator.generateImage(destination,seq,save=save)
        # load source dataset
        num_images = source_data.shape[0]
        data = np.zeros([num_images, 192, 192], dtype='float32', )

        if not os.path.exists(destination):
            os.makedirs(destination)

        for i in range(num_images):
            image = source_data[i,:].reshape([40,40])
            label = source_labels[i] # should be a number
            holo = DiffractionGenerator.freeSpacePropagation(image, upsample=1, z=7e-4)
            data[i, :] = np.abs(holo)

        # labels haven't changed...
        dir = os.path.dirname(os.path.dirname(destination))
        np.savez(os.path.join(dir,npzName + '.npz'), data=data, labels=source_labels)
        return data, source_labels


    @classmethod
    def diffractMNIST(cls, set_name='mnist-diffraction', chop=False):
        from keras.datasets import mnist

        image_folder = Folders.data_folder() + set_name + '/'
        os.makedirs(image_folder, exist_ok=True)

        (train_data, train_labels), (test_data, test_labels) = mnist.load_data()

        if chop:
           for i in range(train_data.shape[0]):
               if bool(random.getrandbits(1)):
                   train_data[i, 0:14, :] = 0
               else:
                   train_data[i, 14:, :] = 0
           for i in range(test_data.shape[0]):
               if bool(random.getrandbits(1)):
                   test_data[i, 0:14, :] = 0
               else:
                   test_data[i, 14:, :] = 0

        train_num = 3000
        test_num = 750
        data_train = np.zeros([train_num, 192, 192], dtype='float32', )
        labels_train = np.zeros([train_num, 192, 192], dtype='float32', )
        data_test = np.zeros([test_num, 192, 192], dtype='float32', )
        labels_test = np.zeros([test_num, 192, 192], dtype='float32', )
        Gfp = None
        for t_idx in range(train_num): #, t in enumerate(train_data):
            # mnist "data" is our "label"
            norm = (255. - train_data[t_idx]) / 255.
            upsampled = scipy.ndimage.zoom(norm, 3.0, order=3)
            upsampled = np.pad(upsampled, (192-upsampled.shape[0]) // 2, mode='edge')
            holo = np.abs(DiffractionGenerator.freeSpacePropagation(upsampled,
                    z=2.5e-3, lmbda=405e-9, upsample=2, Gfp=None))
            holo = scipy.ndimage.zoom(holo, 0.251, order=3)

            data_train[t_idx] = holo
            labels_train[t_idx] = upsampled
            holoDestFilename = '{0:05}-H-{1}.png'.format(t_idx,train_labels[t_idx])
            magnDestFilename = '{0:05}-M-{1}.png'.format(t_idx,train_labels[t_idx])
            # save hologram and magnitude
            imageio.imwrite(image_folder +  holoDestFilename, np.squeeze(holo))
            imageio.imwrite(image_folder +  magnDestFilename, np.squeeze(upsampled))
            if t_idx % 100 == 0:
                print("train: {0}\n".format(t_idx))

        for t_idx in range(test_num):
            # mnist "data" is our "label"
            norm = (255. - test_data[t_idx]) / 255.
            upsampled = scipy.ndimage.zoom(norm, 3.0, order=3)
            upsampled = np.pad(upsampled, (192-upsampled.shape[0]) // 2, mode='edge')
            holo = np.abs(DiffractionGenerator.freeSpacePropagation(upsampled,
                    z=2.5e-3, lmbda=405e-9, upsample=2, Gfp=Gfp))
            holo = scipy.ndimage.zoom(holo, 0.251, order=3)

            data_test[t_idx] = holo
            labels_test[t_idx] = upsampled
            holoDestFilename = '{0:05}-H-{1}.png'.format(train_num+t_idx,test_labels[t_idx])
            magnDestFilename = '{0:05}-M-{1}.png'.format(train_num+t_idx,test_labels[t_idx])
            # save hologram and magnitude
            imageio.imwrite(image_folder +  holoDestFilename, np.squeeze(holo))
            imageio.imwrite(image_folder +  magnDestFilename, np.squeeze(upsampled))
            if t_idx % 100 == 0:
                print("test: {0}\n".format(t_idx))

        np.savez(os.path.join(Folders.data_folder(), set_name + '-training.npz'),
                 data=data_train, labels=labels_train)
        np.savez(os.path.join(Folders.data_folder(), set_name + '-test.npz'),
                  data=data_test, labels=labels_test)


if __name__ == "__main__":
    # DiffractionGenerator.diffractMNIST()
    #DiffractionGenerator.diffractMNIST(set_name='mnist-chopped', chop=True)

    # # # Diffract a random image...
    # recon = np.asarray(Image.open(r'c:\dev\Worms.jpg').convert('L'))
    # # propagate to a hologram
    # holo1 = np.abs(DiffractionGenerator.freeSpacePropagation(recon, upsample=1, z=9e-4))
    # # image.save('output.png')
    # imageio.imwrite(r'c:\dev\holo1.png', np.abs(holo1))
    # # propagate to a hologram
    # holo2 = np.abs(DiffractionGenerator.freeSpacePropagationNoShift(recon, upsample=1, z=9e-4))
    # # image.save('output.png')
    # print("Arrays equal: {0}".format(str(np.array_equal(holo1, holo2))))


    # imageio.imwrite(r'c:\dev\holo2.png', np.abs(holo2))

    # np.set_printoptions(precision=2, suppress=True, linewidth=400)

    # generate code for a free-space propagation kernel...
    # kernel_w, kernel_h = 256,256
    # delta = 2.2e-6
    # Gfp = DiffractionGenerator.freeSpaceKernelOnly(kernel_w, kernel_h,  z = 9e-4, lmbda = 405e-9,
    #                          delta=2.2e-6)
    # imageio.imwrite(r'c:\dev\nGFP11.png', np.real(Gfp))

    # # Gfp = np.fft.ifftshift(Gfp)
    # recon = np.asarray(Image.open(r'c:\dev\Worms.jpg').convert('L'))
    # rf = np.fft.rfft2(recon,s=(256,256))
    # rfft = np.hstack((rf, np.conj(np.flip(np.vstack((rf, rf[0])))[:-1, 1:-1])))
    # # rfft = np.fft.fft2(recon)
    # conv = np.multiply(rfft, Gfp)
    # # ifft = np.fft.ifft2(conv)
    # ifft = np.fft.irfft2(conv)
    # imageio.imwrite(r'c:\dev\holoreal.png', np.abs(ifft))
    # imageio.imwrite(r'c:\dev\nGFP.png', np.real(Gfp))
    # imageio.imwrite(r'c:\dev\nGFPi.png', np.imag(Gfp))

    # kernel_w, kernel_h = 2048,2048
    # delta = 2.2e-6
    # Gfp = DiffractionGenerator.freeSpaceKernelOnly(kernel_w, kernel_h,  z = 11e-4, lmbda = 625e-9,
    #                          delta=2.2e-6)
    # Gfp = np.fft.ifftshift(Gfp)
    # recon = np.asarray(Image.open(r'C:\dev\opencv-debug\holotest\video_test.png').convert('L'))
    # rf = np.fft.rfft2(recon,s=(kernel_w,kernel_h))
    # rfft = np.hstack((rf, np.conj(np.flip(np.vstack((rf, rf[0])))[:-1, 1:-1])))
    # imageio.imwrite(r'C:\dev\opencv-debug\holotest\video_test_spectrumi.png', np.imag(rf))
    # # rfft = np.fft.fft2(recon)
    # conv = np.multiply(rfft, Gfp)
    # # ifft = np.fft.ifft2(conv)
    # ifft = np.fft.irfft2(conv)
    # imageio.imwrite(r'c:\dev\holoreal.png', np.abs(ifft))
    # imageio.imwrite(r'c:\dev\nGFP.png', np.real(Gfp))
    # imageio.imwrite(r'c:\dev\nGFPi.png', np.imag(Gfp))

    # for i in range(kernel_w):
    #     for j in range(kernel_h):
    #         print("{{{0:0.6f}, {1:0.6f}}}".format(gfp[i,j].real, gfp[i,j].imag), end='')
    #         print(', ', end='')
    #     print()

    def print_data(data, x, y):
        print(data[x:x+8,y:y+8])


    # CUDA side-by-side test
    kernel_w, kernel_h = 2048,2048
    np.set_printoptions(precision=2, suppress=False, linewidth=1000)
    delta = 2.2e-6
    dz = 11.0e-4
    lmbda = 625e-9
    Gfp = DiffractionGenerator.freeSpaceKernelOnly(kernel_w, kernel_h,  z = dz, lmbda = lmbda,  delta=delta)
    kernel_spec = np.fft.fftshift(Gfp)
    kernel_spec = kernel_spec.astype(np.complex64)

    # load the test image
    # imageio.imread(r'C:\dev\opencv-debug\video_test.png', format='L')
    data_frame = np.asarray(Image.open(r'C:\dev\opencv-debug\video_test.png').convert('L'))
    padded = np.pad(data_frame, ((544, 544), (384, 384)), 'constant', constant_values=(0.0, 0.0))
    # cudaPad = np.asarray(Image.open(r'C:\dev\opencv-debug\holotest\d_PaddedData.png').convert('L'))
    # imageio.imwrite(r'C:\dev\opencv-debug\pytest\d_PaddedData.png', padded)
    data_spec = np.fft.fft2(padded)
    data_spec = data_spec.astype(np.complex64)

    conv_spec = data_spec * kernel_spec
    conv_dest = np.fft.ifft2(conv_spec)
    imageio.imwrite(r'C:\dev\opencv-debug\pytest\d_ConvDest_mag_cpp.png', np.abs(conv_dest))



    # imageio.imwrite(r'c:\dev\nGFP11.png', np.real(Gfp))

    # fftshift the CUDA image
    # cudaPad = np.asarray(Image.open(r'C:\dev\opencv-debug\holotest\d_PaddedData.png').convert('L'))
    # fftshifted = np.fft.fftshift(cudaPad)
    # imageio.imwrite(r'C:\dev\opencv-debug\holotest\d_PaddedDataShifted.png', fftshifted)