import numpy as np
from numpy.lib import vander 
from common.opencv_tools import SimpleVideoReader
import cv2
import os 
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
from math import ceil
def generate_mot_from_cvat(cvat_results_filename, video_filename, clean_ids_list, skip_frames=1, sequences_duration=30, blank_space_duration=3, no_segment=False):
    mot_results  = np.loadtxt(cvat_results_filename, delimiter=',')
    if len(clean_ids_list): mot_results = remap_ids(mot_results, clean_ids_list)

    video = SimpleVideoReader(video_filename)
    blank_space_length = int(blank_space_duration*video.fps)

    frame_interval = skip_frames+1
    segments = []
    if no_segment:
        sequences_length = video.num_frames-blank_space_length
        segments.append((0,sequences_length))
    else:
        sequences_length = int(sequences_duration*video.fps)
        segment_start = 0
        segment_end = sequences_length

        while segment_end < video.num_frames:

            segments.append((segment_start,segment_end))
            segment_start = segment_end + blank_space_length
            segment_end = segment_start + sequences_length
        

    for segment_nb, (segment_start, segment_end) in enumerate(segments):
        video_name = video_filename.split('/')[-1].split('.')[0]
        sequence_name = video_name if no_segment else '{}_segment_{}'.format(video_name, segment_nb) 
        sequence_dir = os.path.join(sequences_dir,sequence_name)
        os.mkdir(sequence_dir)
        seqmap_file = open(os.path.join(sequence_dir,'seqinfo.ini'),'w')
        sequence_gt_dir = os.path.join(sequence_dir,'gt')
        os.mkdir(sequence_gt_dir)

        first_frame_added = None
        writer = cv2.VideoWriter(filename=os.path.join(output_dir,sequence_name+'.mp4'), apiPreference=cv2.CAP_FFMPEG, fourcc=fourcc, fps=video.fps/frame_interval, frameSize=video.shape, params=None)
        video.set_frame(segment_start)
        while True: 
            ret, frame, frame_read_nb = video.read()
            if ret and frame_read_nb < segment_end:
                if frame_read_nb % frame_interval == 0: 
                    if first_frame_added is None: first_frame_added = frame_read_nb
                    writer.write(frame)
            else: 
                break
            
        writer.release()
        with open(os.path.join(sequence_gt_dir,'gt.txt'),'w') as out_file:
            mot_results_for_segment = np.array([mot_result for mot_result in mot_results if (mot_result[0] >= first_frame_added+1 and mot_result[0] < segment_end)])
            mot_results_for_segment = remap_ids(mot_results_for_segment)
            for mot_result in mot_results_for_segment:
                frame_id = int(mot_result[0])
                track_id = int(mot_result[1])
                left, top, width, height = mot_result[2:6]
                center_x = left+width/2
                center_y = top+height/2
                if (frame_id - 1) % frame_interval == 0: 
                    frame_id_to_write = int((frame_id - 1) // frame_interval - first_frame_added // frame_interval + 1)
                    track_id_to_write = track_id
                    out_file.write('{},{},{},{},{},{},{},{}\n'.format(frame_id_to_write,
                                                                    track_id_to_write,
                                                                    center_x,
                                                                    center_y,
                                                                    -1,
                                                                    -1,
                                                                    1,
                                                                    -1))


        seqmap_file.write('[Sequence]\nname={}\nimDir=img1\nframeRate={}\nseqLength={}\nimWidth=1920\nimHeight=1080\nimExt=.png'.format(sequence_name,video.fps/frame_interval, ceil(sequences_length/frame_interval)))
        seqmap_file.close()
        seqmaps.write(sequence_name+'\n')


def remap_ids(mot_results, list_ids_to_remove=[]):

    if len(list_ids_to_remove):
        indices_to_keep = [i for i in range(len(mot_results)) if mot_results[i,1] not in list_ids_to_remove]
        mot_results = mot_results[indices_to_keep]
    original_ids = sorted(list(set(mot_results[:,1])))
    new_ids_map =  {v:k+1 for k,v in enumerate(original_ids)}
    for result_nb in range(len(mot_results)):
        mot_results[result_nb,1] = new_ids_map[mot_results[result_nb,1]]
    
    return mot_results






    




if __name__ == '__main__':

    output_dir = 'data/validation_videos/T1/long_segments'
    seqmaps_dir = os.path.join(output_dir,'seqmaps')
    os.mkdir(seqmaps_dir)
    seqmaps = open(os.path.join(seqmaps_dir,'surfrider-test.txt'),'w')
    seqmaps.write('name\n')
    sequences_dir = os.path.join(output_dir,'surfrider-test')
    os.mkdir(sequences_dir)

    clean_ids_lists = [[5,6,7,8,9,12,21,22,24,25,27,28,30,31,32,34,35,37,39,47,48,49,56,58],[7,17,19,25,37,44]]
    cvat_results_filenames = ['data/validation_videos/T1/CVAT/gt_part_1.txt','data/validation_videos/T1/CVAT/gt_part_2.txt']
    video_filenames = ['data/validation_videos/T1/CVAT/part_1.mp4','data/validation_videos/T1/CVAT/part_2.mp4']
    # split_lists = [[np.inf]] #[[853,1303,1984,2818,3509,4008,4685,5355,np.inf],[844,2021,2692,3544,3999,4744,5171,6127,6889,np.inf]]


    for cvat_results_filename, video_filename, clean_ids_list in zip(cvat_results_filenames, video_filenames, clean_ids_lists):

        generate_mot_from_cvat(cvat_results_filename=cvat_results_filename, 
                               video_filename=video_filename, 
                               clean_ids_list=clean_ids_list,
                               skip_frames=1, 
                               no_segment=True)

    seqmaps.close()

