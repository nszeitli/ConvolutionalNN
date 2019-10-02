
import os
import numpy as np
import tensorflow.compat.v1 as tf
import matplotlib.pyplot as plt
tf.disable_v2_behavior()
from scipy.io import loadmat
from sklearn.utils import shuffle
from datetime import datetime


def y2indicator(y):
	N = len(y)
	ind = np.zeros((N,10))
	for i in xrange(N):
		ind[i, y[i]] = 1
	return ind

def error_rate(p, t):
    return np.mean(p != t)

def convpool(X, W, b):
	conv_out = tf.nn.conv2d(X, W, strides=[1,1,1,1], padding='SAME')
	conv_out = tf.nn.bias_add(conv_out, b)
	pool_out = tf.nn.max_pool(conv_out, ksize=[1,2,2,1], strides=[1,2,2,1], padding='SAME')
	return pool_out

def init_filter(shape, poolsz):
	w = np.random.randn(*shape) / np.sqrt(np.prod(shape[:-1]) + shape[-1]*np.prod(shape[:-2] / np.prod(poolsz)))
	return w.astype(np.float32)

def rearrange(X):
	N = X.shape[-1]
	out = np.zeros((N,32,32,3), dtype=np.float32)
	for i in xrange(N):
		for j in xrange(3):
			out[i,:,:,j] = x[:,:,j,i]
	return out / 255


def get_data():
    if not os.path.exists('large_files/train_32x32.mat'):
        print('Looking for large_files/train_32x32.mat')
        print('You have not downloaded the data and/or not placed the files in the correct location.')
        print('Please get the data from: http://ufldl.stanford.edu/housenumbers')
        print('Place train_32x32.mat and test_32x32.mat in the folder large_files adjacent to the class folder')
        exit()

    train = loadmat('large_files/train_32x32.mat')
    test  = loadmat('large_files/test_32x32.mat')
    return train, test


def main():
    train, test = get_data()
    

    # Need to scale! don't leave as 0..255
    # Y is a N x 1 matrix with values 1..10 (MATLAB indexes by 1)
    # So flatten it and make it 0..9
    # Also need indicator matrix for cost calculation
    Xtrain = flatten(train['X'].astype(np.float32) / 255.)
    Ytrain = train['y'].flatten() - 1
    Xtrain, Ytrain = shuffle(Xtrain, Ytrain)

    Xtest  = flatten(test['X'].astype(np.float32) / 255.)
    Ytest  = test['y'].flatten() - 1

    # gradient descent params
    max_iter = 20
    print_period = 10
    N, D = Xtrain.shape
    batch_sz = 500
    n_batches = N // batch_sz

	#new stuff, input size to be constant

	Xtrain = Xtrain[:73000,]
	Ytrain = Ytrain[:73000]
	Xtest = Xtest[:26000]
	Ytest = Ytest[:26000]

	Ytest_ind = Ytest_ind[:26000,]

	M = 500
	K = 10
	poolsz = (2,2)
	W1_Shape = (5, 5, 3, 20)
	W1_init = init_filter(W1_Shape, poolsz)
	b1_init = np.zeros(W1_shape[-1], dtype=np.float32)

	W2_Shape = (5, 5, 3, 20)
	W2_init = init_filter(W2_Shape, poolsz)
	b2_init = np.zeros(W2_shape[-1], dtype=np.float32)

	W3_init = init_filter(W2_Shape, poolsz)
	b3_init = np.zeros(W2_shape[-1], dtype=np.float32)

	W3_init = np.random.randn(W2_shape[-1]*8*8, M) / np.sqrt(W2_shape[-1]*8*8 + M)
	b3_init = np.zeros(M, dtype=np.float32)
	W4_init = np.random.randn(M, K) / np.sqrt(M+K)
	b4_init = np.zeros(K, dtype=np.float32)

	# tensorflow variables
	X = tf.place(tf.float32, shape=(batch_sz, 32, 32, 3), name='X')
	T = tf.placeholder(tf.float32, shape(batch_sz, K), name='T')
	W1 = tf.Variable(W1_init.astype(np.float32))
    b1 = tf.Variable(b1_init.astype(np.float32))
    W2 = tf.Variable(W2_init.astype(np.float32))
    b2 = tf.Variable(b2_init.astype(np.float32))
    W3 = tf.Variable(W3_init.astype(np.float32))
    b3 = tf.Variable(b3_init.astype(np.float32))
	W4 = tf.Variable(W3_init.astype(np.float32))
    b4 = tf.Variable(b4_init.astype(np.float32))

	Z1 = convpool(X, W1, b1)
	Z2 = convpool(Z1, W2, b2)
	Z2_Shape = Z2.get_shape().as_list()
	Z2r = tf.reshape(Z2, [Z2_shape[0], np.prod(Z2_shape[1:])])
	Z3 = tf.nn.relu(tf.matmul(Z2r, w3) + b3)
	Yish = tf.matmul(Z3, W4) + b4

	
    cost = tf.reduce_sum(
        tf.nn.sparse_softmax_cross_entropy_with_logits(
            logits=logits,
            labels=T
        )
    )

	train_op = tf.train.RMSPropOptimizer(0.0001, decay=0.99, momentum=0.9).minimize(cost)

	# we'll use this to calculate the error rate
    predict_op = tf.argmax(logits, 1)

    t0 = datetime.now()
    LL = []
    init = tf.global_variables_initializer()
    with tf.Session() as session:
        session.run(init)

        for i in xrange(max_iter):
            for j in xrange(n_batches):
                Xbatch = Xtrain[j*batch_sz:(j*batch_sz + batch_sz),]
                Ybatch = Ytrain[j*batch_sz:(j*batch_sz + batch_sz),]

				if len(Xbatch) == batch_sz:
	                session.run(train_op, feed_dict={X: Xbatch, T: Ybatch})
					if j % print_period == 0:
					test_cost = 0
					prediction = np.zeros(len(Xtest))
					for k in xrange(len(Xtest) / batch_sz):
						Xtestbatch = Xtest[k*batch_sz + batch_sz]
						Ytestbatch = Ytest_ind[k*batch_sz:(k*batch_sz + batch_sz)]
						test_cost += session.run(cost, feed_dict={X: Xtestbatch, T: Ytestbatch})
						prediction[k*batch_sz:(k*batch_sz + batch_sz)] = session.run(
							predict_op, feed_dict={X: Xtestbatch})
					err = error_rate(prediction, Ytest)
                    print("Cost / err at iteration i=%d, j=%d: %.3f / %.3f" % (i, j, test_cost, err))
                    LL.append(test_cost)
    print("Elapsed time:", (datetime.now() - t0))
    plt.plot(LL)
    plt.show()
