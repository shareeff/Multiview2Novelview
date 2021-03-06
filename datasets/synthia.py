from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os.path as osp
import numpy as np
import h5py

from util import log

__PATH__ = './datasets/synthia'
num_digit = 4

rs = np.random.RandomState(123)


class Dataset(object):

    def __init__(self, ids, n, name='default',
                 max_examples=None, is_train=True, bound=10):
        self._ids = list(ids)
        self.name = name
        self.is_train = is_train
        self.n = n
        self.bound = bound

        if max_examples is not None:
            self._ids = self._ids[:max_examples]

        filename = 'data_synthia.hdf5'

        file = osp.join(__PATH__, filename)
        log.info("Reading %s ...", file)

        self.data = h5py.File(file, 'r')
        log.info("Reading Done: %s", file)

    def get_data(self, id, order=None):
        # preprocessing and data augmentation
        image = self.data[id]['image'].value/255.*2 - 1
        pose = np.expand_dims(self.data[id]['pose'].value, -1)

        valid = False
        id_num = int(id[-num_digit:])
        while not valid:
            random_num = np.random.randint(-self.bound, self.bound)
            id_target = id[:-num_digit] + str(id_num + random_num).zfill(num_digit)

            if id_target in self.data:
                image_tmp = self.data[id_target]['image'].value/255.*2 - 1
                pose_tmp = np.expand_dims(self.data[id_target]['pose'].value, -1)
                image = np.concatenate((image, image_tmp), axis=-1)
                pose = np.concatenate((pose, pose_tmp), axis=-1)

                if pose.shape[-1] == self.n + 1:
                    valid = True

        dummy_mask = np.expand_dims(0 * (np.sum(image, axis=-1)), axis=-1)
        image = np.concatenate((image, dummy_mask), axis=-1)
        return image, pose

    def get_data_by_id(self, id_list):
        # preprocessing and data augmentation
        # taget idx: [diff ang, diff evelation]
        id = id_list[0]
        image = self.data[id]['image'].value/255.*2 - 1
        pose = np.expand_dims(self.data[id]['pose'].value, -1)

        for id_source in id_list[1:]:
            if not pose.shape[-1] > self.n:
                image_tmp = self.data[id_source]['image'].value/255.*2 - 1
                pose_tmp = np.expand_dims(self.data[id_source]['pose'].value, -1)
                image = np.concatenate((image, image_tmp), axis=-1)
                pose = np.concatenate((pose, pose_tmp), axis=-1)
        dummy_mask = np.expand_dims(0 * (np.sum(image, axis=-1)), axis=-1)
        image = np.concatenate((image, dummy_mask), axis=-1)
        return image, pose

    def get_data_by_id_tuple(self, id_target, id_input):
        # preprocessing and data augmentation
        image_target = self.data[id_target]['image'].value/255.*2 - 1
        pose_target = np.expand_dims(self.data[id_target]['pose'].value, -1)

        image_input = self.data[id_input]['image'].value/255.*2 - 1
        pose_input = np.expand_dims(self.data[id_input]['pose'].value, 0)

        dummy_mask = np.expand_dims(0 * (np.sum(image_target, axis=-1)), axis=-1)
        image = np.concatenate((image_target, image_input, dummy_mask), axis=-1)
        pose = np.concatenate((pose_target, pose_input), axis=-1)

        return image, pose

    def get_data_by_target(self, id_input, target_idx):
        # preprocessing and data augmentation
        input_image = self.data[id_input]['image'].value/255.*2 - 1
        input_pose = np.expand_dims(self.data[id_input]['pose'].value, -1)

        id_num = int(id_input[-num_digit:])
        id_target = id_input[:-num_digit] + str(int(id_num + target_idx[0])).zfill(num_digit)

        try:
            target_image = self.data[id_target]['image'].value/255.*2 - 1
            target_pose = np.expand_dims(self.data[id_target]['pose'].value, -1)
        except:
            target_image = input_image
            target_pose = input_pose

        dummy_mask = np.expand_dims(0 * (np.sum(target_image, axis=-1)), axis=-1)
        image = np.concatenate((target_image, input_image, dummy_mask), axis=-1)
        pose = np.concatenate((target_pose, input_pose), axis=-1)

        return image, pose, id_target

    @property
    def ids(self):
        return self._ids

    def __len__(self):
        return len(self.ids)

    def __repr__(self):
        return 'Dataset (%s, %d examples)' % (
            self.name,
            len(self)
        )


def create_default_splits(n, is_train=True, bound=10):
    ids_train, ids_test = all_ids()

    dataset_train = Dataset(ids_train, n, name='train', is_train=is_train,
                            bound=bound)
    dataset_test = Dataset(ids_test, n, name='test', is_train=is_train,
                           bound=bound)
    return dataset_train, dataset_test


def all_ids():

    with open(osp.join(__PATH__, 'id_train.txt'), 'r') as fp:
        ids_train = [s.strip() for s in fp.readlines() if s]
    rs.shuffle(ids_train)

    with open(osp.join(__PATH__, 'id_test.txt'), 'r') as fp:
        ids_test = [s.strip() for s in fp.readlines() if s]
    rs.shuffle(ids_test)

    return ids_train, ids_test
