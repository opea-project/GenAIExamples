from __future__ import print_function, division
import os
import time
import subprocess
from tqdm import tqdm
import argparse
from multiprocessing import Pool

parser = argparse.ArgumentParser(description="Dataset processor: Video->Frames")
parser.add_argument("dir_path", type=str, help="original dataset path")
parser.add_argument("dst_dir_path", type=str, help="dest path to save the frames")
parser.add_argument("--prefix", type=str, default="image_%05d.jpg", help="output image type")
parser.add_argument("--accepted_formats", type=str, default=[".mp4", ".mkv", ".webm", ".avi"], nargs="+",
                    help="list of input video formats")
parser.add_argument("--begin", type=int, default=0)
parser.add_argument("--end", type=int, default=666666666)
parser.add_argument("--file_list", type=str, default="")
parser.add_argument("--frame_rate", type=int, default=-1, help="frame sampling rate. -1 is native frame rate")
parser.add_argument("--frame_size", type=int, default=-1, help="shortest frame size. -1 for native size")
parser.add_argument("--num_workers", type=int, default=16)
parser.add_argument("--dry_run", action="store_true")
parser.add_argument("--parallel", action="store_true")
args = parser.parse_args()


def par_job(command):
    if args.dry_run:
        print(command)
    else:
        subprocess.call(command, shell=True)


if __name__ == "__main__":
    t0 = time.time()
    dir_path = args.dir_path
    dst_dir_path = args.dst_dir_path

    if args.file_list == "":
        file_names = sorted(os.listdir(dir_path))
    else:
        file_names = [x.strip() for x in open(args.file_list).readlines()]
    del_list = []
    for i, file_name in enumerate(file_names):
        if not any([x in file_name for x in args.accepted_formats]):
            del_list.append(i)
    file_names = [x for i, x in enumerate(file_names) if i not in del_list]
    file_names = file_names[args.begin:args.end + 1]
    print("%d videos to handle (after %d being removed)" % (len(file_names), len(del_list)))
    cmd_list = []
    for file_name in tqdm(file_names):

        name, ext = os.path.splitext(file_name)
        dst_directory_path = os.path.join(dst_dir_path, name)

        video_file_path = os.path.join(dir_path, file_name)
        if not os.path.exists(dst_directory_path):
            os.makedirs(dst_directory_path, exist_ok=True)

        if os.listdir(dst_directory_path):
            continue

        frame_rate_str = "-r %d" % args.frame_rate if args.frame_rate > 0 else ""
        if args.frame_size > 0:
            try:
                result = os.popen(
                    f"ffprobe -hide_banner -loglevel error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 {video_file_path}"
                )
                w, h = [int(d) for d in result.readline().rstrip().split(",")]
            except:
                print(f"Error with video {video_file_path}!")
                continue
            if min(w, h) <= args.frame_size:
                frame_size_str = ""
            elif w > h:
                frame_size_str = "-vf scale=-1:%d" % args.frame_size
            else:
                frame_size_str = "-vf scale=%d:-1" % args.frame_size
        else:
            frame_size_str = ""
        cmd = 'ffmpeg -nostats -loglevel 0 -i "{}" -q:v 2 {} {} "{}/{}"'.format(video_file_path, frame_size_str, frame_rate_str,
                                                                                   dst_directory_path, args.prefix)
        if not args.parallel:
            if args.dry_run:
                print(cmd)
            else:
                subprocess.call(cmd, shell=True)
        cmd_list.append(cmd)

    if args.parallel:
        with Pool(processes=args.num_workers) as pool:
            with tqdm(total=len(cmd_list)) as pbar:
                for _ in tqdm(pool.imap_unordered(par_job, cmd_list)):
                    pbar.update()
    t1 = time.time()
    print("Finished in %.4f seconds" % (t1 - t0))
    os.system("stty sane")
