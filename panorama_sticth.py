import numpy as np
import cv2
import time
from tqdm import tqdm

cp = cv2.VideoCapture('plot_104.mp4')
n_frames = int(cp.get(cv2.CAP_PROP_FRAME_COUNT))
print("N_frames:", n_frames)

width = int(cp.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cp.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cp.get(cv2.CAP_PROP_FPS)

# After rotation 270°: width and height swap
rot_width, rot_height = height, width

out = cv2.VideoWriter('video_out.mp4', cv2.VideoWriter_fourcc(*'mp4v'), fps/2, (2 * rot_width, rot_height))

ret, prev = cp.read()
if not ret:
    raise RuntimeError("Could not read first frame")

# Rotate the first frame
prev = cv2.rotate(prev, cv2.ROTATE_90_CLOCKWISE)
prev_gray = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)

index = 0
stitched = None
start_time = time.time()
processed_frames = 0

with tqdm(total=n_frames-2, desc="Processing frames", unit="frame") as pbar:
    for i in range(n_frames - 2):
        sift = cv2.SIFT_create()
        kp1, des1 = sift.detectAndCompute(prev_gray, None)
        
        succ, curr = cp.read()
        if not succ:
            break
        
        # Rotate the current frame
        curr = cv2.rotate(curr, cv2.ROTATE_90_CLOCKWISE)
        
        if index % 20 == 0:
            frame_start = time.time()
            curr_gray = cv2.cvtColor(curr, cv2.COLOR_BGR2GRAY)
            kp2, des2 = sift.detectAndCompute(curr_gray, None)
            
            bf = cv2.BFMatcher()
            matches = bf.knnMatch(des1, des2, k=2)
            
            if len(matches) == 0:
                pbar.update(1)
                continue
                
            good = []
            for m in matches:
                if len(m) == 2 and m[0].distance < 0.75 * m[1].distance:
                    good.append(m[0])
                    
            matches = np.asarray(good)
            
            if matches.shape[0] >= 4:
                src_pts = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
                dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
                
                H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
                
                if H is None:
                    pbar.update(1)
                    continue
                    
                stitched = cv2.warpPerspective(prev, H, (curr.shape[1] + prev.shape[1], curr.shape[0]))
                stitched[0:curr.shape[0], 0:curr.shape[1]] = curr
                
                if stitched.shape[1] > 1920:
                    stitched = cv2.resize(stitched, (int(stitched.shape[1] / 2), int(stitched.shape[0] / 2)))
                    
                prev_gray = curr_gray
                prev = curr
                
            processed_frames += 1
            elapsed = time.time() - start_time
            avg_time = elapsed / processed_frames
            remaining_frames = (n_frames - i) / 20
            eta = remaining_frames * avg_time
            
            pbar.set_postfix({
                'Processed': processed_frames,
                'ETA': f'{eta:.1f}s'
            })
            
        index += 1
        pbar.update(1)

cp.release()
out.release()

if stitched is not None:
    print("\nSaving panorama...")
    cv2.imwrite('resultant_stitched_panorama_.jpg', stitched)
    cv2.imshow("dst", stitched)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
else:
    print("No panorama could be created.")
