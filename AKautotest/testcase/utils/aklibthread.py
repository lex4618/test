# -*- coding: utf-8 -*-
import math
import sys
import os

root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos+len("AKautotest")]
sys.path.append(root_path)    

from akcommon_define import *
import threading
import time
import traceback
import inspect
import ctypes
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List, Any, Dict, Tuple, Optional, Union


__all__ = [
    'AkThread',
    'thread_start_with_join',
    'multi_devices_test_start',
    'multi_devices_login_web',
    'multi_devices_start_capture_syslog',
    'thread_exec_func_with_devices',
    'multi_devices_exec_func',
    'concurrent_exec_in_child_thread',
    'thread_exec_with_stop_event',
    'thread_pool_run'
]


class AkThread(threading.Thread):

    def __init__(self, target, args=(), kwargs=None, wait_time=None, stop_event=None, name=None):
        auto_name = self._generate_thread_name(target, name)
        super().__init__(name=auto_name)
        self.func = target
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.result = None
        self.wait_time = wait_time
        self.exit_code = 0
        self.exception = None
        self.exc_traceback = ''
        self.stop_event = None
        # 如果func有stop_event参数，则注入
        if stop_event is not None:
            sig = inspect.signature(self.func)
            if 'stop_event' in sig.parameters:
                self.kwargs['stop_event'] = stop_event
                self.stop_event: Optional[threading.Event] = stop_event
        self.start_time = None

    @staticmethod
    def _generate_thread_name(func: object, name):
        """
        智能生成线程名称
        优先级：用户传入 > 类/实例的device_name+func名 > func名
        """
        if name:
            return name

        device_name = None

        # 1. 实例方法
        if hasattr(func, '__self__') and func.__self__:
            # 优先取实例属性
            device_name = getattr(func.__self__, 'device_name', None)
            # 如果实例没有，再取类属性
            if device_name is None:
                device_name = getattr(type(func.__self__), 'device_name', None)
        # 2. 类方法
        elif hasattr(func, '__objclass__'):
            device_name = getattr(func.__objclass__, 'device_name', None)
        # 3. 静态方法/普通函数，不处理

        if device_name:
            return f"[{device_name}]{func.__name__}"
        else:
            return func.__name__

    def run(self):
        if self.wait_time is not None and self.wait_time != 0:
            aklog_printf(f'thread run: {self.name}, after {self.wait_time}s')
            time.sleep(self.wait_time)
        aklog_printf(f'thread run: {self.name}, with params: {self.args} {self.kwargs}')
        try:
            self.start_time = time.time()
            self.result = self.func(*self.args, **self.kwargs)
        except Exception as e:
            aklog_error(f"子线程{self.name}执行异常: {e}")
            self.exit_code = 1
            self.exception = e
            self.exc_traceback = traceback.format_exc()
            aklog_printf(self.exc_traceback)

    def get_result(self):
        """获取子线程执行结果"""
        try:
            return self.result
        except Exception as e:
            print(e)
            return None

    def get_exception(self):
        return self.exception

    def get_exit_code(self):
        return self.exit_code

    def _async_raise(self, exctype):
        """raises the exception, performs cleanup if needed"""
        if not inspect.isclass(exctype):
            raise TypeError("Only types can be raised (not instances)")
        print(self.ident)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident, ctypes.py_object(exctype))
        if res == 0:
            raise ValueError("invalid thread id")
        elif res != 1:
            # """if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"""
            ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident, 0)
            raise SystemError("PyThreadState_SetAsyncExc failed")

    def raise_exc(self, exctype):
        """raises the given exception type in the context of this thread"""
        self._async_raise(exctype)

    def terminate(self):
        """raises SystemExit in the context of the given thread, which should
        cause the thread to exit silently (unless caught)"""
        self.raise_exc(SystemExit)

    def stop_by_event(self, timeout=None):
        """
        等待子线程执行结束或超时，如果超时后，子线程仍未结束，则设置event事件，中断子线程
        Args:
            timeout (float|int): 超时时间（秒）
        Returns:
            any: 子线程返回结果
        """
        if self.is_alive():
            # 如果子线程还活着，先等待到超时时间
            if timeout:
                # 计算剩余等待时间
                elapsed = time.time() - (self.start_time or time.time())
                remaining_time = timeout - elapsed
                if remaining_time > 0:
                    aklog_debug(f"主线程等待子线程{self.name}，剩余超时时间: {remaining_time:.2f}s")
                    self.join(math.ceil(remaining_time))  # 等待剩余时间
            if self.is_alive():
                if self.stop_event is not None:
                    self.stop_event.set()  # 通知子线程中断
                    self.join()
                    if self.is_alive():
                        aklog_warn(f"子线程{self.name}中断失败，仍未退出！")
                    else:
                        aklog_debug(f"子线程{self.name}已被成功中断并退出")
                else:
                    aklog_warn(f"子线程{self.name}无法中断（未设置stop_event）")
        else:
            aklog_debug(f"子线程{self.name}已在超时时间内结束")
        return self.result


def thread_start_with_join(*targets, timeout=1800, interval=0.5, raise_exception=True):
    """
    多线程执行，并且都等待子线程执行完毕后再执行主线程
    :param targets: 也可以传入参数，类型为元组：(method, (arg1, arg2...), {})， 注意args参数传入元组时，如果元组的元素只有一个，需要加逗号
    :param timeout: 子线程执行的超时时间
    :param interval: 多个子线程执行前的等待时间，比如interval设为10秒，则第一个子线程等待时间为0，第二个等待10秒，第三个等待20秒...
    :param raise_exception: 是否抛出子线程的异常，让主线程获取
    :return:
    """
    if not targets:
        return None
    threads = []
    results = []
    i = 0
    for target in targets:
        # 判断传入的target类型，如果为元组，说明带有参数
        if isinstance(target, tuple):
            method = target[0]
            if len(target) == 2:
                if isinstance(target[1], tuple):
                    args = target[1]
                    kwargs = None
                else:
                    args = ()
                    kwargs = target[1]
            else:
                args = target[1]
                kwargs = target[2]
        else:
            method = target
            args = ()
            kwargs = None

        if interval is not None:
            wait_time = interval * i
        else:
            wait_time = None
        # print('{}, with params: {} {}'.format(method.__name__, args, kwargs))
        thread = AkThread(method, args, kwargs, wait_time)
        threads.append(thread)
        i += 1

    begin_time = time.time()
    for thread in threads:
        thread.daemon = True  # 设置主线程结束后也结束子线程
        thread.start()

    # 等待所有线程，逐一join
    for thread in threads:
        thread.join(timeout)
        if thread.is_alive():
            aklog_warn(f"子线程{thread.name}在超时时间{timeout}s后仍未结束！")

    # 检查是否有未完成的线程
    unfinished_threads = [thread for thread in threads if thread.is_alive()]
    if unfinished_threads:
        for thread in unfinished_threads:
            aklog_warn(f"子线程{thread.name}未能在超时时间内完成，当前状态：alive")
        if raise_exception:
            raise RuntimeError(f"存在{len(unfinished_threads)}个子线程未完成，详情见日志。")

    # 如果子线程出现异常，则抛出异常
    if raise_exception:
        for thread in threads:
            if thread.get_exit_code() != 0:
                raise thread.get_exception()

    time.sleep(1)
    for thread in threads:
        ret = thread.get_result()  # 获取每个子线程执行完返回的结果
        results.append(ret)

    if time.time() - begin_time > timeout:
        aklog_printf('Out Time: %s' % timeout)
        if raise_exception:
            raise RuntimeError('子线程执行超时')

    return results


def multi_devices_test_start(*devices, phone_init=False, interval=1, raise_exception=True):
    """
    多台设备同时初始化连接
    """
    func_list = []
    for device in devices:
        if phone_init:
            if device and hasattr(device, 'phone_init'):
                func = device.phone_init
                func_list.append(func)
                continue
        if device and hasattr(device, 'TestStart'):
            func = getattr(device, 'TestStart')
            func_list.append(func)
            continue
        elif device and hasattr(device, 'test_start'):
            func = getattr(device, 'test_start')
            func_list.append(func)
            continue

    thread_start_with_join(*func_list, interval=interval, raise_exception=raise_exception)


def multi_devices_login_web(*devices, interval=1, raise_exception=True):
    """
    多台设备同时打开浏览器登录网页
    """
    func_list = []
    for device in devices:
        if not device:
            continue
        func = getattr(device, 'start_and_login', None)
        if not func:
            device_web = getattr(device, 'web', None) or getattr(device, 'browser', None)
            if device_web:
                func = getattr(device_web, 'start_and_login', None)
        if func:
            func_list.append(func)

    thread_start_with_join(*func_list, interval=interval, raise_exception=raise_exception)
    

def multi_devices_start_capture_syslog(*devices, interval=1, raise_exception=True):
    """
    多台设备同时开启抓取log
    """
    aklog_info()
    func_list = []
    for device in devices:
        if not device:
            continue
        func = getattr(device, 'start_capture_syslog', None)
        if func is None:
            device_web = (getattr(device, 'web_inf', None)
                          or getattr(device, 'web', None)
                          or getattr(device, 'browser', None))
            if device_web:
                func = getattr(device_web, 'start_capture_syslog', None)
        if func is not None:
            func_list.append(func)

    thread_start_with_join(*func_list, interval=interval, raise_exception=raise_exception)


def thread_exec_func_with_devices(exec_func, devices, raise_exception=True):
    """
    同时执行某个方法，将devices的元素作为func的参数
    Args:
        exec_func (object):
        devices (list):
        raise_exception (bool):
    """
    func_list = []
    for device in devices:
        func = (exec_func, (device,))
        func_list.append(func)
    thread_start_with_join(*func_list, raise_exception=raise_exception)


def multi_devices_exec_func(exec_func, devices, *args, raise_exception=True, **kwargs):
    """
    多设备同时执行某个方法
    Args:
        exec_func (str):
        devices (list):
        raise_exception (bool):
        *args (): 要执行的方法的参数
        **kwargs (): 要执行的方法的参数
    """
    func_list = []
    for device in devices:
        method = getattr(device, exec_func, None)
        if not method:
            continue
        func = (method, tuple(args), dict(kwargs))
        func_list.append(func)
    results = thread_start_with_join(*func_list, raise_exception=raise_exception)
    return results


def concurrent_exec_in_child_thread(func, args=(), kwargs=None) -> AkThread:
    """子线程同步执行方法"""
    thread = AkThread(func, args, kwargs)
    thread.daemon = True
    thread.start()
    return thread


def thread_exec_with_stop_event(func, args=(), kwargs=None) -> AkThread:
    """
    启动支持stop_event的线程
    如果func有stop_event参数，则自动注入
    """
    sig = inspect.signature(func)
    if 'stop_event' in sig.parameters:
        stop_event = threading.Event()
    else:
        raise ValueError(f'{str(func)} 缺少stop_event参数')
    thread = AkThread(func, args, kwargs, stop_event=stop_event)
    thread.daemon = True
    thread.start()
    return thread


def thread_pool_run(
    func: Callable,
    args_list: List[Any],
    max_workers: int = 4,
    per_task_timeout: Optional[float] = 1800,
    task_name: str = "",
    result_fields: Optional[List[str]] = None,
    callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    is_raise: bool = True,
) -> List[Dict[str, Any]]:
    """
    通用线程池并发执行方法，支持args/kwargs、返回结构自定义、回调。

    Args:
        func (Callable): 需要并发执行的函数。
        args_list (List[Any]): 每个任务的参数（元组或字典）列表。
        max_workers (int): 最大线程数。
        per_task_timeout (Optional[float]): 每个任务的超时时间（秒），None表示不限时。
        task_name (str): 任务名称（用于日志）。
        result_fields (Optional[List[str]]): 指定返回结构字段，None则返回全部。
        callback (Optional[Callable[[Dict[str, Any]], None]]): 每个任务完成后的回调，参数为单个任务结果字典。
        is_raise (bool): 是否抛送异常
    Returns:
        List[Dict[str, Any]]: 每个任务的执行结果，包含参数、结果、异常等信息。
    """
    aklog_debug()

    results = []  # 存储所有任务的执行结果

    # 内部函数：根据参数类型调用func
    def _submit_task(executor, func, args_item):
        if isinstance(args_item, dict):
            return executor.submit(func, **args_item)
        elif isinstance(args_item, tuple):
            return executor.submit(func, *args_item)
        else:
            # 单一参数直接传递
            return executor.submit(func, args_item)

    def get_args_desc(args_item):
        """
        获取参数的可读性描述（如device_name），用于日志输出。
        """
        # 单个对象且有device_name属性
        if hasattr(args_item, 'device_name'):
            return f"{args_item.__class__.__name__}({getattr(args_item, 'device_name', '')})"
        # tuple/list，尝试获取每个元素的device_name
        if isinstance(args_item, (tuple, list)):
            descs = []
            for obj in args_item:
                if hasattr(obj, 'device_name'):
                    descs.append(f"{obj.__class__.__name__}({getattr(obj, 'device_name', '')})")
                else:
                    descs.append(str(obj))
            return ', '.join(descs)
        # dict，尝试获取每个value的device_name
        if isinstance(args_item, dict):
            descs = []
            for k, v in args_item.items():
                if hasattr(v, 'device_name'):
                    descs.append(f"{k}={v.__class__.__name__}({getattr(v, 'device_name', '')})")
                else:
                    descs.append(f"{k}={v}")
            return ', '.join(descs)
        # 其他类型直接转字符串
        return str(args_item)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务到线程池
        future_to_args = {}
        for args_item in args_list:
            future = _submit_task(executor, func, args_item)
            future_to_args[future] = args_item
        exceptions = []
        for future in as_completed(future_to_args):
            args_item = future_to_args[future]
            args_desc = get_args_desc(args_item)
            result_info: Dict[str, Any] = {
                "param": args_item,
                "result": None,
                "exception": None,
                "traceback": None
            }
            try:
                result = future.result(timeout=per_task_timeout)
                result_info["result"] = result
                aklog_info(f"任务: {task_name}, params: ({args_desc}), 执行完成，结果: {result}")
            except Exception as e:
                result_info["exception"] = e
                result_info["traceback"] = traceback.format_exc()
                aklog_warn(f"任务: {task_name}, params: ({args_desc}), 执行异常: {e}")
                aklog_debug(result_info['traceback'])
                exceptions.append(e)

            # 返回结构自定义
            if result_fields:
                filtered = {k: v for k, v in result_info.items() if k in result_fields}
            else:
                filtered = result_info

            # 支持回调
            if callback:
                try:
                    callback(filtered)
                except Exception as cb_e:
                    aklog_warn(f"{task_name} 回调执行异常: {cb_e}")

            results.append(filtered)

        # 循环结束后统一处理异常
        if is_raise and exceptions:
            # 可以选择raise第一个异常
            raise exceptions[0]
    return results
