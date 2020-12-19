from keras.layers import Input
from m2det import M2DET
from PIL import Image
from keras.applications.imagenet_utils import preprocess_input
from utils.utils import BBoxUtility,letterbox_image,m2det_correct_boxes
from utils.anchors import get_anchors
from tqdm import tqdm
import math
import copy
import numpy as np
import os
class mAP_M2DET(M2DET):
    #---------------------------------------------------#
    #   检测图片
    #---------------------------------------------------#
    def detect_image(self,image_id,image):
        self.confidence = 0.01
        f = open("./input/detection-results/"+image_id+".txt","w") 

        image_shape = np.array(np.shape(image)[0:2])
        # 加灰条的方式， resize 到 320x320
        crop_img,x_offset,y_offset = letterbox_image(image, [self.model_image_size[0],self.model_image_size[1]])
        photo = np.array(crop_img,dtype = np.float64)

        # 图片预处理，归一化
        photo = preprocess_input(np.reshape(photo,[1,self.model_image_size[0],self.model_image_size[1],self.model_image_size[2]]))
        preds = self.m2det.predict(photo)

        # 将预测结果进行解码
        results = self.bbox_util.detection_out(preds,self.prior,confidence_threshold=self.confidence    )
        if len(results[0])<=0:
            return image

        # 筛选出其中得分高于confidence的框
        det_label = results[0][:, 0]
        det_conf = results[0][:, 1]
        det_xmin, det_ymin, det_xmax, det_ymax = results[0][:, 2], results[0][:, 3], results[0][:, 4], results[0][:, 5]

        top_indices = [i for i, conf in enumerate(det_conf) if conf >= self.confidence]
        top_conf = det_conf[top_indices]
        top_label_indices = det_label[top_indices].tolist()
        top_xmin, top_ymin, top_xmax, top_ymax = np.expand_dims(det_xmin[top_indices],-1),np.expand_dims(det_ymin[top_indices],-1),np.expand_dims(det_xmax[top_indices],-1),np.expand_dims(det_ymax[top_indices],-1)
        
        # 去掉灰条
        boxes = m2det_correct_boxes(top_ymin,top_xmin,top_ymax,top_xmax,np.array([self.model_image_size[0],self.model_image_size[1]]),image_shape)

        for i, c in enumerate(top_label_indices):
            predicted_class = self.class_names[int(c)-1]
            score = str(top_conf[i])

            top, left, bottom, right = boxes[i]
            f.write("%s %s %s %s %s %s\n" % (predicted_class, score[:6], str(int(left)), str(int(top)), str(int(right)),str(int(bottom))))

        f.close()
        return 

m2det = mAP_M2DET()
image_ids = open('VOCdevkit/VOC2007/ImageSets/Main/test.txt').read().strip().split()

if not os.path.exists("./input"):
    os.makedirs("./input")
if not os.path.exists("./input/detection-results"):
    os.makedirs("./input/detection-results")
if not os.path.exists("./input/images-optional"):
    os.makedirs("./input/images-optional")

for image_id in tqdm(image_ids):
    image_path = "./VOCdevkit/VOC2007/JPEGImages/"+image_id+".jpg"
    image = Image.open(image_path)
    # image.save("./input/images-optional/"+image_id+".jpg")
    m2det.detect_image(image_id,image)
    
print("Conversion completed!")
