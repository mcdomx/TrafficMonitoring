# import queue
# import numpy as np
# import time
# from collections import namedtuple
# from multiprocessing import Process, Queue
#
# Frame = namedtuple("Frame", ['num', 'time', 'image', 'queue'])
#
#
# # GET AND ADD FRAMES FROM/TO QUEUES ##################################
# def get_frame(ref_queue: queue.Queue) -> (int, np.array):
#     """
#     Get the next frame in the queue.
#     :return: frame number and the frame as an np.array
#     """
#     print("GET FRAME           ", end='\r')
#     try:
#         frame_num, source_queue = ref_queue.get(block=False)  # True, timeout=1 / 60)
#         ref_queue.task_done()
#         frame = source_queue.get(block=False)  # True, timeout=1 / 60)
#         source_queue.task_done()
#
#     except queue.Empty:
#         # print("qs: get_frame(): queue empty")
#         return None, None
#
#     return frame.time, frame.image
#
#
# # def add_frame(frame: Frame,
# #               ref_queue: queue.Queue,
# #               detections: list = None,
# #               detections_queue: queue.Queue = None,
# #               # mon_queue: queue.Queue = None) -> None:
# #               mon_queue: Queue = None) -> None:
# #
# #     print("ADD FRAME              ", end='\r')
# #
# #     # print("qs: add_frame(): // {} // {}".format(frame.num, type(frame)))
# #
# #     try:
# #         ref_queue.put((frame.num, frame.queue), block=True)  # True, timeout=1 / 60)
# #         frame.queue.put(frame, block=True)  # True, timeout=1 / 60)
# #
# #         # if detections are present, put in det queue and add
# #         # detections and monitored items
# #         if detections:
# #             # q = det_queue
# #             _add_detection(detections=detections, detections_queue=detections_queue)
# #             # _add_to_monitor(mon_queue=mon_queue, t=time.time(), detections=detections, f=frame.image)
# #             mon_process = Process(target=_add_to_monitor, args=(mon_queue, time.time(), detections, frame.image))
# #             mon_process.start()
# #             mon_process.join()
# #
# #     except queue.Full:
# #         pass
#
#
# # def get_detections(detections_queue: queue.Queue) -> list:
# #     """get all detections from queue as a list"""
# #     print("GET ALL DETECTIONS   ", end='\r')
# #     det_list = []
# #
# #     while not detections_queue.empty():
# #         det_list.append(detections_queue.get())
# #         detections_queue.task_done()
# #
# #     return det_list
#
#
# # def _add_detection(detections_queue: queue.Queue, detections: list) -> None:
# #     """add a detection to detections queue. clear an item if queue is full."""
# #     # print("queue_service: adding to detections ...")
# #     print("ADD DETECTION         ", end='\r')
# #     try:
# #         detections_queue.put(detections, block=True, timeout=1 / 60)
# #     except queue.Full:
# #         # if full, remove an item to make room and add new item
# #         _ = detections_queue.get(block=False)  # True, timeout=1 / 60)
# #         detections_queue.task_done()
# #         detections_queue.put(detections)
# #     # print("queue_service: added to detections!")
#
#
# # # def get_monitored_item(mon_queue: queue.Queue) -> (bool, float, set, np.array):
# # def get_monitored_item(mon_queue: Queue) -> (bool, float, set, np.array):
# #     """return item from monitored items queue"""
# #     print("GET MONITORED ITEM    ", end='\r')
# #     try:
# #         d_elems = mon_queue.get(block=False) # block=True, timeout=1 / 60)  # need to allow pass in case of shutdown
# #         # mon_queue.task_done()
# #         time_stamp = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime(d_elems.get('t')))
# #
# #         d_items = d_elems.get('d')
# #
# #         return True, time_stamp, d_items, d_elems.get('f')
# #
# #     # except queue.Empty:
# #     except Exception:
# #         return False, None, None, None
#
#
# # def _add_to_monitor(mon_queue: queue.Queue, t: time, detections: list, f: np.array) -> None:
# # def _add_to_monitor(mon_queue: Queue, t: time, detections: list, f: np.array) -> None:
# #     """add to monitored items queue. monitor thread will determine if
# #     item needs to be monitored or not.  All detections will be put
# #     into this queue."""
# #     print("ADD TO MONITOR       ", end='\r')
# #     d_items = {d.get('name') for d in detections}  # make set of names
# #     # print("queue_service: adding to monitor ...")
# #     try:
# #         mon_queue.put({"t": t, "d": set(d_items), "f": f}, block=True, timeout=1 / 60)
# #     except queue.Full:
# #         # if full, remove an item to make room and add new item
# #         _ = mon_queue.get(block=False)  # True, timeout=1 / 60)
# #         mon_queue.task_done()
# #         mon_queue.put({"t": t, "d": set(d_items), "f": f})
# #     # print("queue_service: added to monitor!")
#
# # END - GET AND ADD FRAMES FROM/TO QUEUES ##################################
