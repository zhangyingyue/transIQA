from torch.utils.data import Dataset
import numpy as np
import torch
import tools
import cv2
import multiprocessing as mtp

class RandomCrop(object):
    """Crop randomly the image in a sample.

    Args:
        output_size (tuple or int): Desired output size. If int, square crop
            is made.
    """

    def __init__(self, output_size):
        assert isinstance(output_size, (int, tuple))
        if isinstance(output_size, int):
            self.output_size = (output_size, output_size)
        else:
            assert len(output_size) == 2
            self.output_size = output_size

    def __call__(self, sample):
        image, score = sample['image'], sample['score']

        h, w = image.shape[:2]
        new_h, new_w = self.output_size

        top = np.random.randint(0, h - new_h)
        left = np.random.randint(0, w - new_w)

        image = image[top: top + new_h,
                left: left + new_w]

        return {'image': image, 'score': score}


class ToTensor(object):
    """Convert ndarrays in sample to Tensors."""

    def __call__(self, sample):
        image, score = sample['image'], sample['score']

        # swap color axis because
        # numpy image: H x W x C
        # torch image: C X H X W
        image = image.transpose((2, 0, 1))
        return {'image': torch.from_numpy(image),
                'score': torch.from_numpy(score)}


class FaceScoreDataset_015(Dataset):
    """Face Score dataset"""

    def __init__(self, image_list, transform=None):
        """
        initiate imagelist and score
        :param image_list: .txt file with image path and score
        """
        self.images = [line.rstrip('\n').split()[0] for line in open(image_list)]
        self.scores = [line.rstrip('\n').split()[1] for line in open(image_list)]
        self.transform = transform

        #debug: show image shape
        debug = False
        if debug:
            num = 0
            path = []
            for i in self.images:
                fault_path = tools.show_image_depth(i)
                if fault_path != '':
                    path.append(fault_path)
                    num += 1
            print(num)
            print(path)
            exit(0)

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        """
        # Version 0.15
        if self.images[idx][-4:] == '.jp2':
            image = glymur.Jp2k(self.images[idx])[:]

            #debug
            debug=0
            if debug:
                tools.show_image(image)

        else:
            image = io.imread(self.images[idx])
        image = np.array(image, dtype=np.float32)
        """

        image = cv2.imread(self.images[idx])
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = np.array(image, dtype=np.float32)

        # debug
        debug = 0
        if debug:
            print(image.dtype)
            print(np.array(image, dtype=np.float32).dtype)
            print(image.shape)
            tools.show_image(np.array(image, dtype=np.int)) # interfaces is not supported for multi-processing
            #exit(0)

        score = np.array((float(self.scores[idx])), dtype=np.float32).reshape([1])#IMPORTANT
        sample = {'image': image, 'score': score}

        if self.transform:
            sample = self.transform(sample)

        return sample

class FaceScoreDataset_0152(Dataset):
    """Face Score dataset"""

    def __init__(self, image_list, transform=None, use_dlib_cnn=True, scale = 1.2):
        """
        initiate imagelist and score
        :param image_list: .txt file with image path and score
        """
        self.images = [line.rstrip('\n').split()[0] for line in open(image_list)]
        self.scores = [line.rstrip('\n').split()[1] for line in open(image_list)]
        self.transform = transform

        # prepare faces
        # detect faces and save as images file

        #debug: show image shape
        debug = False
        if debug:
            num = 0
            path = []
            for i in self.images:
                fault_path = tools.show_image_depth(i)
                if fault_path != '':
                    path.append(fault_path)
                    num += 1
            print(num)
            print(path)
            exit(0)

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        """
        # Version 0.15
        if self.images[idx][-4:] == '.jp2':
            image = glymur.Jp2k(self.images[idx])[:]

            #debug
            debug=0
            if debug:
                tools.show_image(image)

        else:
            image = io.imread(self.images[idx])
        image = np.array(image, dtype=np.float32)
        """

        image = np.load(self.images[idx])
        image = np.array(image, dtype=np.float32)

        # debug
        debug = 1
        if debug:
            print(image.dtype)
            print(np.array(image, dtype=np.float32).dtype)
            print(image.shape)
            tools.show_image(np.array(image, dtype=np.int)) # interfaces is not supported for multi-processing
            #exit(0)

        score = np.array((float(self.scores[idx])), dtype=np.float32).reshape([1])#IMPORTANT
        sample = {'image': image, 'score': score}

        if self.transform:
            sample = self.transform(sample)

        return sample

class FaceScoreDataset_MTP(Dataset):
    """MTP"""
    """Face Score dataset"""

    def __init__(self, train=True, image_list='', transform=None, num_faces=10000):
        """
        initiate imagelist and score
        :param image_list: .txt file with image path and score
        """
        faces = [line.rstrip('\n').split()[0] for line in open(image_list)]
        scores = [line.rstrip('\n').split()[1] for line in open(image_list)]
        self.transform = transform
        self.images = []
        self.scores = []
        self.train = train
        # multiprocessing for data parallelism
        p = mtp.Pool(4)
        step = 10

        #debug: show image shape
        debug = False
        if debug:
            num = 0
            path = []
            for i in self.images:
                fault_path = tools.show_image_depth(i)
                if fault_path != '':
                    path.append(fault_path)
                    num += 1
            print(num)
            print(path)
            exit(0)

        # reading datasets
        assert num_faces < len(faces)
        assert len(faces) > 50000
        if self.train:
            print('Loading Training set')
            shuffle_face = np.random.choice(50000, num_faces)

            for i in shuffle_face:
                self.scores.append(float(scores[i]))

            num_step = int(50000 / step)
            for i in range(num_step):
                img = p.map(read_dataset, [faces[j] for j in shuffle_face[i*step: (i+1)*step]])

                for j in img:
                    self.images.append(j)

                #if len(self.images) % 1000 == 0:
                #    print('%d in %d'%(len(self.images), len(faces)))
        else:
            print('Loading Testing set')
            self.scores = [float(score) for score in scores[50000:]]
            self.scores = np.array(self.scores, dtype=np.float32)
            num_step = int((len(faces) - 50000) / step)
            for i in range(num_step):

                img = p.map(read_dataset, faces[50000 + i*step: 50000+i*step+step])
                for j in img:
                    self.images.append(j)

            if 50000 + num_step*step != len(self.scores):
                img = p.map(read_dataset, faces[50000 + num_step*step:])
                # there is something wrong when left one
                for j in img:
                    self.images.append(j)

            # debug
            debug =0
            if debug:
                print(len(self.images))
                exit(0)
            '''
            for i in range(50000, len(faces)):
                #debug
                debug=1
                if debug:
                    print(i)
                    print(faces[i])
                face = faces[i]
                self.images.append(np.array(p.map(np_load, (face, face)), dtype=np.float32))
                if type(self.scores) == list:
                    self.scores.append(float(scores[i]))
                else:
                    np.concatenate([self.scores, np.array(float(scores[i])).reshape(1)])
                #if len(self.images) % 1000 == 0:
                #    print('%d in %d'%(i, len(faces)))
                self.scores = np.array(self.scores, dtype=np.float32)
            '''



    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):

        assert self.train == True, 'getitem fuction only for training.'

        image = self.images[idx]

        # debug
        debug = 0
        if debug:
            print(image.dtype)
            print(np.array(image, dtype=np.float32).dtype)
            print(image.shape)
            tools.show_image(np.array(image, dtype=np.int)) # interfaces is not supported for multi-processing
            #exit(0)

        score = np.array((float(self.scores[idx])), dtype=np.float32).reshape([1])#IMPORTANT
        sample = {'image': image, 'score': score}

        if self.transform:
            sample = self.transform(sample)

        return sample

class FaceScoreDataset(Dataset):
    """Face Score dataset"""

    def __init__(self, image_list, transform=None, limited=True, train=True):
        """
        initiate imagelist and score
        :param image_list: .txt file with image path and score
        """
        faces = [line.rstrip('\n').split()[0] for line in open(image_list)]
        scores = [line.rstrip('\n').split()[1] for line in open(image_list)]
        self.limited = limited
        self.transform = transform
        self.images = []
        self.scores = []
        self.train = train

        if self.limited:
            num_faces = 2000
        else:
            num_faces = 10000

        #debug: show image shape
        debug = False
        if debug:
            num = 0
            path = []
            for i in self.images:
                fault_path = tools.show_image_depth(i)
                if fault_path != '':
                    path.append(fault_path)
                    num += 1
            print(num)
            print(path)
            exit(0)

        # reading datasets
        assert num_faces < len(faces)
        assert len(faces) > 50000
        if self.train:
            print('Loading Training set')
            for i in np.random.choice(50000, num_faces):
                #debug
                debug=0
                if debug:
                    print(i)
                self.images.append(tools.standardize_image(
                    np.array(np.load(faces[i]), dtype=np.float32)))
                self.scores.append(scores[i])
                #if len(self.images) % 1000 == 0:
                #    print('%d in %d'%(len(self.images), len(faces)))
        else:
            print('Loading Testing set')
            test_length = 8000
            if self.limited:
                test_length = 4000

            num = 0
            self.scores = np.zeros(test_length)
            for i in range(len(faces) - test_length, len(faces)):
                self.images.append(tools.standardize_image(
                    np.array(np.load(faces[i]), dtype=np.float32)))

                #if len(self.images) % 1000 == 0:
                #    print('%d in %d'%(i, len(faces)))
                self.scores[i - len(faces) + test_length] = float(scores[i])

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):

        assert self.train == True, 'getitem fuction only for training.'

        image = self.images[idx]

        # debug
        debug = 0
        if debug:
            print(image.dtype)
            print(np.array(image, dtype=np.float32).dtype)
            print(image.shape)
            tools.show_image(np.array(image, dtype=np.int)) # interfaces is not supported for multi-processing
            #exit(0)

        score = np.array((float(self.scores[idx])), dtype=np.float32).reshape([1])#IMPORTANT
        sample = {'image': image, 'score': score}

        if self.transform:
            sample = self.transform(sample)

        return sample