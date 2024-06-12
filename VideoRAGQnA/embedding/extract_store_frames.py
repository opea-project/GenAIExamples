import os
import time as t
import cv2
import json
import datetime
import random
from tzlocal import get_localzone

def calculate_intervals(video_path, chunk_duration, clip_duration):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("Error: Could not open video.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    total_seconds = total_frames / fps

    intervals = []

    chunk_frames = int(chunk_duration * fps)
    clip_frames = int(clip_duration * fps)

    for start_frame in range(0, total_frames, chunk_frames):
        end_frame = min(start_frame + clip_frames, total_frames)
        start_time = start_frame / fps
        end_time = end_frame / fps
        intervals.append((start_frame, end_frame, start_time, end_time))

    cap.release()
    return intervals

def process_all_videos(config):
    path = config['videos']
    image_output_dir = config['image_output_dir'] 
    meta_output_dir = config['meta_output_dir']
    N = config['number_of_frames_per_second']
    selected_db = config['vector_db']['choice_of_db']
    emb_path = config['embeddings']['path']
    emb_type = config['embeddings']['type']
    chunk_duration = config['chunk_duration']
    clip_duration = config['clip_duration']

    def extract_frames(video_path, image_output_dir, meta_output_dir, N, date_time, local_timezone):
        video = os.path.splitext(os.path.basename(video_path))[0]
        # Create a directory to store frames and metadata
        os.makedirs(image_output_dir, exist_ok=True)
        os.makedirs(meta_output_dir, exist_ok=True)
        
        # Open the video file
        cap = cv2.VideoCapture(video_path)

        if int(cv2.__version__.split('.')[0]) < 3:
            fps = cap.get(cv2.cv.CV_CAP_PROP_FPS)
        else:
            fps = cap.get(cv2.CAP_PROP_FPS)
    
        total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        
        #print (f'fps {fps}')
        #print (f'total frames {total_frames}')
        
        mod = int(fps // N)
        if mod == 0: mod = 1
        
        print (f'total frames {total_frames}, N {N}, mod {mod}')
        
        # Variables to track frame count and desired frames
        frame_count = 0
        
        # Metadata dictionary to store timestamp and image paths
        metadata = {}
        
        while cap.isOpened():
            ret, frame = cap.read()
            
            if not ret:
                break
            
            frame_count += 1
            
            if frame_count % mod == 0:
                timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000  # Convert milliseconds to seconds
                frame_path = os.path.join(image_output_dir, f"{video}_{frame_count}.jpg")
                time = date_time.strftime("%H:%M:%S")
                date = date_time.strftime("%Y-%m-%d")
                hours, minutes, seconds = map(float, time.split(":"))
                year, month, day = map(int, date.split("-"))
                
                cv2.imwrite(frame_path, frame)  # Save the frame as an image


                metadata[frame_count] = {"timestamp": timestamp, "frame_path": frame_path,"date": date, "year": year, "month": month, "day": day, 
                    "time": time, "hours": hours, "minutes": minutes, "seconds": seconds}
                if selected_db == 'vdms':
                    # Localize the current time to the local timezone of the machine
                    #Tahani might not need this
                    current_time_local = date_time.replace(tzinfo=datetime.timezone.utc).astimezone(local_timezone)

                    # Convert the localized time to ISO 8601 format with timezone offset
                    iso_date_time = current_time_local.isoformat()
                    metadata[frame_count]['date_time'] = {"_date": str(iso_date_time)}

        # Save metadata to a JSON file
        metadata_file = os.path.join(meta_output_dir, f"{video}_metadata.json")
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=4)
        
        # Release the video capture and close all windows
        cap.release()
        print(f"{frame_count/mod} Frames extracted and metadata saved successfully.") 
        return fps, total_frames, metadata_file

    videos = [file for file in os.listdir(path) if file.endswith('.mp4')] # TODO: increase supported video formats

    # print (f'Total {len(videos)} videos will be processed')
    metadata = {}
    
    for i, each_video in enumerate(videos):
        metadata[each_video] = {}
        keyname = each_video
        video_path = os.path.join(path, each_video)
        #date_time = datetime.datetime.now()  # FIXME CHECK: is this correct? 
        date_time = t.ctime(os.stat(video_path).st_ctime)
        print(f"date_time of {video_path} being created : ",date_time)
        # Get the local timezone of the machine
        local_timezone = get_localzone()
        if emb_type == 'frame':
            fps, total_frames, metadata_file = extract_frames(video_path, image_output_dir, meta_output_dir, N, date_time, local_timezone)
            metadata[each_video].update({
                'extracted_frame_metadata_file': metadata_file,
            })
        elif emb_type == 'video':
            time_format = "%a %b %d %H:%M:%S %Y"
            date_time = datetime.datetime.strptime(date_time, time_format)
            time = date_time.strftime("%H:%M:%S")
            hours, minutes, seconds = map(float, time.split(":"))
            date = date_time.strftime("%Y-%m-%d")
            year, month, day = map(int, date.split("-"))

            if clip_duration is not None and chunk_duration is not None and clip_duration < chunk_duration:
                interval_count = 0
                metadata.pop(each_video)
                for start_frame, end_frame, start_time, end_time in calculate_intervals(video_path, chunk_duration, clip_duration):
                    keyname = os.path.splitext(os.path.basename(video_path))[0]+f"_interval_{interval_count}"
                    metadata[keyname] = {"timestamp":start_time}
                    metadata[keyname].update({"date": date, "year": year, "month": month, "day": day, 
                        "time": time, "hours": hours, "minutes": minutes, "seconds": seconds})
                    if selected_db == 'vdms':
                        # Localize the current time to the local timezone of the machine
                        #Tahani might not need this
                        current_time_local = date_time.replace(tzinfo=datetime.timezone.utc).astimezone(local_timezone)

                        # Convert the localized time to ISO 8601 format with timezone offset
                        iso_date_time = current_time_local.isoformat()
                        metadata[keyname]['date_time'] = {"_date": str(iso_date_time)}

                    # Open the video file
                    cap = cv2.VideoCapture(video_path)

                    if int(cv2.__version__.split('.')[0]) < 3:
                        fps = cap.get(cv2.cv.CV_CAP_PROP_FPS)
                    else:
                        fps = cap.get(cv2.CAP_PROP_FPS)
                
                    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                    # get the duration
                    metadata[keyname].update({
                            "clip_duration":(min(total_frames,end_frame)-start_frame)/fps,
                            'fps': fps, 
                            'total_frames': total_frames, 
                            #'embedding_path': os.path.join(emb_path, each_video+".pt"),
                            'video_path': f'{os.path.join(path,each_video)}',
                        })
                    cap.release()
                    interval_count+=1
        metadata[keyname].update({
                'fps': fps, 
                'total_frames': total_frames, 
                #'embedding_path': os.path.join(emb_path, each_video+".pt"),
                'video_path': f'{os.path.join(path,each_video)}',
            })
        print (f'✅  {i+1}/{len(videos)}')
    os.makedirs(meta_output_dir, exist_ok=True)
    metadata_file = os.path.join(meta_output_dir, f"metadata.json")
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=4)