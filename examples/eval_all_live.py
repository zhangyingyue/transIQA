import numpy as np
import sys
from scipy import stats
import face_iqa
from skimage import io


mode = 'ft2'

if mode == 'ft12':
    model_path = '/data/junrui/github/transIQA/model/ft12/live_mse_405_0.9725_0.9674.pth.tar'
elif mode == 'ft2':
    model_path = '/data/junrui/github/transIQA/model/ft2/live_mae_398_0.9104_0.9255.pth.tar'
elif mode == 'ft':
    model_path = '/data/junrui/github/transIQA/model/ft/live_mae_283_0.9776_0.9692.pth.tar'
else:
    print('error mode')
    exit(0)

tp = mode + '_all'

fi = face_iqa.FaceIQA(enable_cuda=True, model_path=model_path, mode=mode)

res_dir = './log/results/live/'

srocc_file = open(res_dir + tp + '_srocc' + '.txt', "w")
lcc_file = open(res_dir + tp + '_lcc' + '.txt', "w")

test_file = './data/live_generator/' + 'ft_live_test.txt'

filename = [line.rstrip('\n') for line in open(test_file)]

roidb = []
scores = []
for i in filename:
    roidb.append(i.split()[0])
    scores.append(float(i.split()[1]))
scores = np.asarray(scores)

Num_Image = len(scores)
pre = np.zeros(Num_Image)
med = np.zeros(Num_Image)

for i in range(Num_Image):
    directory = roidb[i]
    im = io.imread(directory)
    pre[i] = fi.get_score(im)

srocc = stats.spearmanr(pre, scores)[0]
lcc = stats.pearsonr(pre, scores)[0]
print('%   LCC of mean : {}'.format(lcc))
print('% SROCC of mean: {}'.format(srocc))

srocc_file.write('%6.3f\n' % (srocc))
lcc_file.write('%6.3f\n' % (lcc))
srocc_file.close()
lcc_file.close()
