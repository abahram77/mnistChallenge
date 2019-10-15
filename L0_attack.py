"""
Implementation of attack methods. Running this file as a program will
apply the attack to the model specified by the config file and store
the examples in an .npy file.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import cv2
import os
import tensorflow as tf
import numpy as np
import scipy.misc
from PIL import Image
from matplotlib import pyplot


class L0Attack:
  def __init__(self, model, epsilon, threshold, a, random_start, loss_func):
    """Attack parameter initialization. The attack performs k steps of
       size a, while always staying within epsilon from the initial
       point."""
    self.model = model
    self.epsilon = epsilon
    self.threshold = threshold
    self.a = a
    self.rand = random_start


    if loss_func == 'xent':
      loss = model.xent
    elif loss_func == 'cw':
      label_mask = tf.one_hot(model.y_input,
                              10,
                              on_value=1.0,
                              off_value=0.0,
                              dtype=tf.float32)
      correct_logit = tf.reduce_sum(label_mask * model.pre_softmax, axis=1)
      wrong_logit = tf.reduce_max((1-label_mask) * model.pre_softmax
                                  - 1e4*label_mask, axis=1)
      loss = -tf.nn.relu(correct_logit - wrong_logit + 50)
    else:
      print('Unknown loss function. Defaulting to cross-entropy')
      loss = model.xent


    self.grad = tf.gradients(loss, model.x_input)[0]


  def perturb(self, x_nat, y, sess):
    """Given a set of examples (x_nat, y), returns a set of adversarial
       examples within epsilon of x_nat in l_infinity norm."""
    # if self.rand:
    #   x = x_nat + np.random.uniform(-self.epsilon, self.epsilon, x_nat.shape)
    #   x = np.clip(x, 0, 1) # ensure valid pixel range
    # else:
    #   x = np.copy(x_nat)
    x=np.copy(x_nat)
    # first_image = x[0]
    # first_image = np.array(first_image, dtype='float')
    # pixels = first_image.reshape((28, 28))
    # pyplot.imshow(pixels, cmap='gray')
    # for k in range (len(x)):
    #   first_image = x[k]
    #   first_image = np.array(first_image, dtype='float')
    #   pixels = first_image.reshape((28, 28))
    #
    #   # scipy.misc.imsave('/pics'+'/pic'+str(k)+'.jpg', pixels)
    #
    #
    #
    #   # convert values to 0 - 255 int8 format
    #   formatted = (pixels * 255 / np.max(pixels)).astype('uint8')
    #   img = Image.fromarray(formatted)
    #   path = 'C:/Users/abahram77/PycharmProjects/mnist_challenge/mnist_challenge/L0_pics_nonPerturbed/'
    #   img.save(path+'pic'+str(k)+'.png')
    listOfSets=[set() for i in range(200)]
    listOfSets2=[set() for i in range(200)]

    for i in range(self.threshold):
      grad = sess.run(self.grad, feed_dict={self.model.x_input: x,
                                           self.model.y_input: y})
      grad2 = grad.tolist()

      for j in range(len(x)):
        max_grad=np.where(grad[j] == np.amax(grad[j]))
        index = max_grad[0][0]
        # print(grad[j][index])
        grad2=grad.tolist()
        while (index in listOfSets[j]):
          del grad2[j][index]
          grad2=np.asanyarray(grad2)
          max_grad = np.where(grad2[j] == np.amax(grad2[j]))
          index = max_grad[0][0]

        listOfSets[j].add(index)
        x[j][index] =1
        min_grad = np.where(grad[j] == np.amin(grad[j]))
        index1 = min_grad[0][0]
        grad2 = grad.tolist()
        while (index1 in listOfSets2[j]):
          del grad2[j][index1]
          grad2 = np.asanyarray(grad2)
          min_grad = np.where(grad2[j] == np.amin(grad2[j]))
          index1 = min_grad[0][0]

        listOfSets2[j].add(index1)
        # print(grad[j][index1])
        x[j][index1]=0
        # print(x[j][index])
        # print(x[j])


    # for k in range (len(x)):
    #   first_image = x[k]
    #   first_image = np.array(first_image, dtype='float')
    #   pixels = first_image.reshape((28, 28))
    #
    #   # scipy.misc.imsave('/pics'+'/pic'+str(k)+'.jpg', pixels)
    #
    #
    #
    #   # convert values to 0 - 255 int8 format
    #   formatted = (pixels * 255 / np.max(pixels)).astype('uint8')
    #   img = Image.fromarray(formatted)
    #   path = 'C:/Users/abahram77/PycharmProjects/mnist_challenge/mnist_challenge/L0_pics_perturbed/'
    #   img.save(path+'pic'+str(k)+'.png')
    #
    #   #x += self.a * np.sign(grad)
    #
    #
    #   #x = np.clip(x, x_nat - self.epsilon, x_nat + self.epsilon)
    # for i in range(0,len(listOfSets)):
    #   listOfSets[i]=len(listOfSets[i])
    #   listOfSets2[i]=len(listOfSets2[i])
    # print(listOfSets)
    # print(listOfSets2)
    # print()

    x = np.clip(x, 0, 1) # ensure valid pixel range


    return x




if __name__ == '__main__':
  import json
  import sys
  import math


  from tensorflow.examples.tutorials.mnist import input_data


  from model import Model


  with open('config.json') as config_file:
    config = json.load(config_file)


  model_file = tf.train.latest_checkpoint(config['model_dir2'])
  if model_file is None:
    print('No model found')
    sys.exit()


  model = Model()
  attack = L0Attack(model,
                    config['epsilon'],
                    config['threshold'],
                    config['a'],
                    config['random_start'],
                    config['loss_func'])
  saver = tf.train.Saver()


  mnist = input_data.read_data_sets('MNIST_data', one_hot=False)


  with tf.Session() as sess:
    # Restore the checkpoint
    saver.restore(sess, model_file)


    # Iterate over the samples batch-by-batch
    num_eval_examples = config['num_eval_examples']
    eval_batch_size = config['eval_batch_size']
    num_batches = int(math.ceil(num_eval_examples / eval_batch_size))
    num_batches=1

    x_adv = [] # adv accumulator


    print('Iterating over {} batches'.format(num_batches))


    for ibatch in range(num_batches):
      bstart = ibatch * eval_batch_size
      bend = min(bstart + eval_batch_size, num_eval_examples)
      print('batch size: {}'.format(bend - bstart))


      x_batch = mnist.test.images[bstart:bend, :]
      y_batch = mnist.test.labels[bstart:bend]


      x_batch_adv = attack.perturb(x_batch, y_batch, sess)


      x_adv.append(x_batch_adv)


    print('Storing examples')
    path = config['store_adv_L0_path']
    x_adv = np.concatenate(x_adv, axis=0)
    np.save(path, x_adv)
    print('Examples stored in {}'.format(path))










