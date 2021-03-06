import cv2
from numpy import *
from matplotlib import pyplot as plt
from networktables import NetworkTables
import sys
import math

#Find the 'n' greatest values in an array 'lst' and store their indicies in array 'ind' from greatest value to the nth greatest value.
def findmax(lst,n):

    templst = lst;
    ind = [];
    
    for j in range(n):
        tempval = 0;
        for i in range(len(templst)):
            if max(templst) == templst[i]:
                tempval = i;

        templst[tempval] = 0;
        ind.append(tempval);

    return ind

#Input image of red laser dot. Using Contours, determine the (x,y) pixel coordinates of each laser dot in the image.
def findpix(im):
    ret,bim = cv2.threshold(im[:,:,2],240,255,cv2.THRESH_BINARY);   #threshold on red data of image

    #plt.imshow(bim); plt.show();

    #Find the external contours in the binary image. Store the endpoints of each contour in a seperate array within the array 'contours'.
    contours = cv2.findContours(bim,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE); 

    lst = [];
    for i in range(len(contours[0])):
        lst.append(len(contours[0][i]));

    #Find the largest array of contour endpoints.  This was done to reduce the chances of picking up small red diffraction patterns from the laser.
    #This does not rule out large red objects in the image.  Selecting a range of sizes of contour endpoints would be more practical. Given the time
    #constraint of this project, this provided to be the quickest solution, albiet its lack of robustness.
    ind = findmax(lst,numlasers);

    #Find the mean of the contour enpoints to find the centre of the laser dot.
    pix = [];
    for j in range(len(ind)):
        temp = 0; temp2 = 0;
        for i in range(len(contours[0][ind[j]])):
            temp = temp + contours[0][ind[j]][i][0][0];
            temp2 = temp2 + contours[0][ind[j]][i][0][1];

        xpixel = temp/len(contours[0][ind[j]]);
        ypixel = temp2/len(contours[0][ind[j]]);

        pix.append([xpixel,ypixel]);
	
    return pix

#Given a horizontal pixel value of each image, calculate the distance.
def finddist(left_cam_x,right_cam_x):

        x_res = 1280.0;         #horizontal resolution of images
        fov_x_half = 59.6/2;    #half the horizontal field of view (in degrees) of the cameras

        l_0 = x_res/2;
        theta_0 = fov_x_half*math.pi/180;

        l_1 = abs(right_cam_x - l_0);   #dist from laser to image centre
        theta_1 = math.pi/2 - math.atan(math.tan(theta_0)*(l_1/l_0));

        l_2 = abs(left_cam_x - l_0);    #dist from laser to image centre
        theta_2 = math.pi/2 - math.atan(math.tan(theta_0)*(l_2/l_0));

        #Find the side lengths of the triangle
        hyp_1 = cam_sep/math.sin(math.pi - theta_1 - theta_2) * math.sin(theta_2);      
        hyp_2 = cam_sep/math.sin(math.pi - theta_1 - theta_2) * math.sin(theta_1);

        #Find median of the triangle
        dist = math.sqrt((2*hyp_1**2 + 2*hyp_2**2 - sep**2)/4);     

        return dist

#Constants
numlasers = 3;
cam_sep = 10;
left_cam_index = 0;
right_cam_index = 1;

#Capture images
left_cam = cv2.VideoCapture(left_cam_index);
l, left_img = cv2.left_cam.read();
right_cam = cv2.VideoCapture(right_cam_index);
r, right_img = cv2.right_cam.read();

#Load images and find the laser dot pixel coordinates
pix = findpix(left_img);
left_cam_x1 = pix[0][0]; left_cam_y1 = pix[0][1];
left_cam_x2 = pix[1][0]; left_cam_y2 = pix[1][1];
left_cam_x3 = pix[2][0]; left_cam_y3 = pix[2][1];

pix = findpix(right_img);
right_cam_x1 = pix[0][0]; right_cam_y1 = pix[0][1];
right_cam_x2 = pix[1][0]; right_cam_y2 = pix[1][1];
right_cam_x3 = pix[2][0]; right_cam_y3 = pix[2][1];

xleft = [left_cam_x1,left_cam_x2,left_cam_x3];
xr = [right_cam_x1,right_cam_x2,right_cam_x3];

#Match the laser dots between the images 
orderx1 = findmax(xleft,numlasers);
orderxr = findmax(xr,numlasers);

dist1 = finddist(xleft[orderx1[0]],xr[orderxr[0]]);
dist2 = finddist(xleft[orderx1[1]],xr[orderxr[1]]);
dist3 = finddist(xleft[orderx1[2]],xr[orderxr[2]]);

#Get angle from object
opposite = dist1 - dist3;
theta = math.degrees(math.atan(opposite / cam_sep));

#Average distances
avg_dist = (dist1 + dist2 + dist3)/3;

#Setup network tables
ip = sys.argv[1];
NetworkTables.initialize(server=ip);
sd = NetworkTables.getTable("SmartDashboard");

#Pass values to SmartDashboard
sd.putNumber('visionDist', avg_dist);
sd.putNumber('visionAngle', theta);
